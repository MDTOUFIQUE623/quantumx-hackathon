"""
Ballot crypto — Phase 3.

Responsibilities
----------------
* ``build_ballot``      — Encrypt + sign a ballot (server / test use; production path
                          is the browser, but this helper lets us test the full round-trip
                          without a browser).
* ``verify_ballot``     — 4-step bulletin-board check (credential sig, ballot sig,
                          constituency match, double-vote guard).
* ``decap_and_decrypt`` — Election Authority decrypts a stored ballot for tallying.
* ``decap_shared_secret`` / ``shared_secret_fingerprint`` — kept for interop endpoint.

Invariants (from context doc — never break)
-------------------------------------------
1. Always sign over the FULL payload with sort_keys=True — never just the ciphertext.
2. The nonce must be stored alongside ballot_ciphertext.
3. Bulletin board never stores or sees the shared_secret.
4. Ledger is append-only.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import oqs
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pq_voting.crypto.credential import verify_ballot_signature, verify_voter_credential
from pq_voting.crypto.encoding import b64d, b64e, canonical_json_bytes
from pq_voting.crypto.hashing import chain_hash, sha3_256_hex
from pq_voting.crypto.keygen import kem_alg, sig_alg


# ---------------------------------------------------------------------------
# Build (encrypt + sign) — used by tests and the interop smoke-test endpoint.
# In production the browser does this with liboqs-js + Web Crypto.
# ---------------------------------------------------------------------------

def build_ballot(
    *,
    candidate_id: str,
    election_id: str,
    voter_id: str,
    voter_secret_key: bytes,
    ea_public_key: bytes,
) -> dict[str, Any]:
    """
    Construct a signed, encrypted ballot ready for the bulletin board.

    Returns the ballot dict with all wire fields (base64 / hex encoded).
    """
    # Step 1 — KEM encapsulation: derive a one-time shared secret.
    with oqs.KeyEncapsulation(kem_alg()) as client_kem:
        kem_ciphertext, shared_secret = client_kem.encap_secret(ea_public_key)

    # Step 2 — AES-256-GCM: encrypt the vote payload using the shared secret.
    # AES-GCM requires a 256-bit key; Kyber512 shared secret is 32 bytes — perfect.
    nonce = os.urandom(12)
    vote_plaintext = json.dumps(
        {"candidate_id": candidate_id, "election_id": election_id},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    aes = AESGCM(shared_secret)
    ballot_ciphertext = aes.encrypt(nonce, vote_plaintext, None)

    # Step 3 — Dilithium sign over the FULL canonical payload.
    signable = canonical_json_bytes(
        {
            "ballot_ciphertext": b64e(ballot_ciphertext),
            "election_id": election_id,
            "kem_ciphertext": b64e(kem_ciphertext),
            "nonce": b64e(nonce),
            "voter_id": voter_id,
        }
    )
    with oqs.Signature(sig_alg(), secret_key=voter_secret_key) as signer:
        signature = signer.sign(signable)

    return {
        "ballot_id": str(uuid4()),
        "voter_id": voter_id,
        "election_id": election_id,
        "kem_ciphertext": b64e(kem_ciphertext),
        "nonce": b64e(nonce),
        "ballot_ciphertext": b64e(ballot_ciphertext),
        "signature": b64e(signature),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Bulletin-board 4-step verification
# ---------------------------------------------------------------------------

def _signable_payload(ballot: dict[str, Any]) -> bytes:
    """Re-derive the exact bytes that were signed during ballot construction."""
    return canonical_json_bytes(
        {
            "ballot_ciphertext": ballot["ballot_ciphertext"],
            "election_id": ballot["election_id"],
            "kem_ciphertext": ballot["kem_ciphertext"],
            "nonce": ballot["nonce"],
            "voter_id": ballot["voter_id"],
        }
    )


def verify_ballot(
    ballot: dict[str, Any],
    credential: dict[str, Any],
    ia_public_key: bytes,
    *,
    prev_chain_hash: str = "0" * 64,
) -> dict[str, Any]:
    """
    Run the 4-step bulletin-board check and return a receipt dict on success.

    Raises ``ValueError`` with a descriptive message on any failure.

    Steps
    -----
    1. Verify IA signature on the voter credential.
    2. Verify ballot Dilithium signature using the credential's voter public key.
    3. Check ballot constituency_id == credential constituency_id (not applicable here
       because constituency is in the credential, not the ballot wire format; the
       /vote route enforces this by fetching the credential from the DB).
    4. Double-vote check is enforced at the DB layer by the /vote route.

    Returns
    -------
    dict with ``ballot_id``, ``chain_hash``, and ``position`` (position will be
    set by the ledger writer; we return -1 as a sentinel here).
    """
    # Step 1 — Credential authenticity.
    if not verify_voter_credential(credential, ia_public_key):
        raise ValueError("Credential IA signature is invalid")

    # Step 2 — voter_id in ballot must match credential (before signature check).
    if ballot["voter_id"] != credential["voter_id"]:
        raise ValueError("voter_id mismatch between ballot and credential")

    # Step 3 — Ballot signature authenticity.
    payload = _signable_payload(ballot)
    voter_pk_hex: str = credential["dilithium_pk"]
    if not verify_ballot_signature(payload, ballot["signature"], voter_pk_hex):
        raise ValueError("Ballot Dilithium signature is invalid")

    # Compute chain hash for the receipt.
    ch = chain_hash(prev_chain_hash, payload)

    return {
        "ballot_id": ballot["ballot_id"],
        "chain_hash": ch,
        "position": -1,  # Assigned by ledger on INSERT.
    }


# ---------------------------------------------------------------------------
# Election Authority decryption (used during tallying — Phase 5)
# ---------------------------------------------------------------------------

def decap_and_decrypt(ballot: dict[str, Any], ea_secret_key: bytes) -> dict[str, Any]:
    """
    Decrypt a stored ballot for tallying.

    Returns the plaintext vote dict ``{"candidate_id": ..., "election_id": ...}``.
    """
    shared_secret = decap_shared_secret(ea_secret_key, ballot["kem_ciphertext"])
    nonce = b64d(ballot["nonce"])
    ciphertext = b64d(ballot["ballot_ciphertext"])
    aes = AESGCM(shared_secret)
    plaintext = aes.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))


# ---------------------------------------------------------------------------
# Kept for backward-compat / interop endpoint
# ---------------------------------------------------------------------------

def decap_shared_secret(ea_secret_key: bytes, kem_ciphertext_b64: str) -> bytes:
    """KEM decapsulation — returns the shared secret bytes."""
    ciphertext = b64d(kem_ciphertext_b64)
    with oqs.KeyEncapsulation(kem_alg(), secret_key=ea_secret_key) as kem:
        return kem.decap_secret(ciphertext)


def shared_secret_fingerprint(secret: bytes) -> str:
    return sha3_256_hex(secret)

