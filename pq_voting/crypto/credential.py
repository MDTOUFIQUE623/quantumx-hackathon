from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import oqs

from pq_voting.crypto.encoding import canonical_json_bytes
from pq_voting.crypto.hashing import biometric_hash
from pq_voting.crypto.keygen import sig_alg


def _credential_body(
    voter_id: str,
    name: str,
    dob: str,
    aadhaar: str,
    constituency_id: str,
    dilithium_pk_hex: str,
    issued_at: str,
    expiry: str,
) -> dict[str, Any]:
    return {
        "voter_id": voter_id,
        "biometric_hash": biometric_hash(name, dob, aadhaar),
        "constituency_id": constituency_id,
        "dilithium_pk": dilithium_pk_hex,
        "issued_at": issued_at,
        "expiry": expiry,
    }


def issue_voter_credential(
    ia_secret_key: bytes,
    *,
    name: str,
    dob: str,
    aadhaar: str,
    constituency_id: str,
    dilithium_pk_hex: str,
    voter_id: str | None = None,
    validity_days: int = 365,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    issued_at = now.isoformat()
    expiry = (now + timedelta(days=validity_days)).isoformat()
    voter_id = voter_id or str(uuid4())

    credential = _credential_body(
        voter_id=voter_id,
        name=name,
        dob=dob,
        aadhaar=aadhaar,
        constituency_id=constituency_id,
        dilithium_pk_hex=dilithium_pk_hex,
        issued_at=issued_at,
        expiry=expiry,
    )
    payload = canonical_json_bytes(credential)

    with oqs.Signature(sig_alg(), secret_key=ia_secret_key) as signer:
        signature = signer.sign(payload)

    credential["ia_signature"] = signature.hex()
    return credential


def verify_voter_credential(credential: dict[str, Any], ia_public_key: bytes) -> bool:
    if "ia_signature" not in credential:
        return False

    signed = {k: v for k, v in credential.items() if k != "ia_signature"}
    payload = canonical_json_bytes(signed)
    signature = bytes.fromhex(credential["ia_signature"])

    with oqs.Signature(sig_alg()) as verifier:
        return verifier.verify(payload, signature, ia_public_key)


def verify_ballot_signature(
    payload: bytes, signature_b64: str, voter_public_key_hex: str
) -> bool:
    from pq_voting.crypto.encoding import b64d

    voter_pk = bytes.fromhex(voter_public_key_hex)
    signature = b64d(signature_b64)

    with oqs.Signature(sig_alg()) as verifier:
        return verifier.verify(payload, signature, voter_pk)
