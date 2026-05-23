"""
Phase 3 crypto tests — ballot encrypt / sign / verify / decrypt.
Run with:  pytest tests/test_crypto.py -v
"""
import pytest
import oqs

from pq_voting.crypto.ballot import (
    build_ballot,
    decap_and_decrypt,
    decap_shared_secret,
    verify_ballot,
)
from pq_voting.crypto.credential import issue_voter_credential, verify_voter_credential
from pq_voting.crypto.hashing import chain_hash
from pq_voting.crypto.keygen import (
    generate_ea_keypair,
    generate_ia_keypair,
    kem_alg,
    sig_alg,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ia_keys():
    return generate_ia_keypair()  # (pk, sk)


@pytest.fixture(scope="module")
def ea_keys():
    return generate_ea_keypair()  # (pk, sk)


@pytest.fixture(scope="module")
def voter_keys():
    with oqs.Signature(sig_alg()) as sig:
        voter_pk = sig.generate_keypair()
        voter_sk = sig.export_secret_key()
    return voter_pk, voter_sk


@pytest.fixture(scope="module")
def credential(ia_keys, voter_keys):
    ia_pk, ia_sk = ia_keys
    voter_pk, _ = voter_keys
    return issue_voter_credential(
        ia_sk,
        name="Test Voter",
        dob="1990-01-01",
        aadhaar="123456789012",
        constituency_id="MH-22-Pune",
        dilithium_pk_hex=voter_pk.hex(),
        voter_id="test-voter-001",
    )


@pytest.fixture(scope="module")
def ballot(credential, voter_keys, ea_keys):
    _, voter_sk = voter_keys
    ea_pk, _ = ea_keys
    return build_ballot(
        candidate_id="candidate-A",
        election_id="GE-2026",
        voter_id=credential["voter_id"],
        voter_secret_key=voter_sk,
        ea_public_key=ea_pk,
    )


# ---------------------------------------------------------------------------
# Phase 2 — keygen + credential (kept from original)
# ---------------------------------------------------------------------------

def test_ia_credential_roundtrip(ia_keys, voter_keys):
    ia_pk, ia_sk = ia_keys
    voter_pk, _ = voter_keys
    cred = issue_voter_credential(
        ia_sk,
        name="Test User",
        dob="1990-01-01",
        aadhaar="123456789012",
        constituency_id="MH-22-Pune",
        dilithium_pk_hex=voter_pk.hex(),
    )
    assert verify_voter_credential(cred, ia_pk), "IA credential verification must pass"


def test_kyber_encap_decap(ea_keys):
    ea_pk, ea_sk = ea_keys
    with oqs.KeyEncapsulation(kem_alg()) as client:
        ciphertext, secret_client = client.encap_secret(ea_pk)
    with oqs.KeyEncapsulation(kem_alg(), secret_key=ea_sk) as server:
        secret_server = server.decap_secret(ciphertext)
    assert secret_client == secret_server, "KEM shared secrets must match"


# ---------------------------------------------------------------------------
# Phase 3 — ballot build
# ---------------------------------------------------------------------------

def test_ballot_has_required_fields(ballot):
    required = {
        "ballot_id", "voter_id", "election_id",
        "kem_ciphertext", "nonce", "ballot_ciphertext",
        "signature", "submitted_at",
    }
    assert required.issubset(ballot.keys()), f"Missing fields: {required - ballot.keys()}"


def test_ballot_fields_are_strings(ballot):
    for field in ("kem_ciphertext", "nonce", "ballot_ciphertext", "signature"):
        assert isinstance(ballot[field], str), f"Field {field!r} must be a base64 string"


# ---------------------------------------------------------------------------
# Phase 3 — verify_ballot (4-step bulletin-board check)
# ---------------------------------------------------------------------------

def test_verify_ballot_passes(ballot, credential, ia_keys):
    ia_pk, _ = ia_keys
    receipt = verify_ballot(ballot, credential, ia_pk)
    assert receipt["ballot_id"] == ballot["ballot_id"]
    assert len(receipt["chain_hash"]) == 64, "SHA3-256 hex digest is 64 chars"


def test_verify_ballot_bad_credential_sig(ballot, credential, ea_keys):
    """Tamper with IA signature — bullet-board must reject."""
    ia_pk, _ = ea_keys  # deliberately supply EA pk where IA pk is expected
    with pytest.raises(ValueError, match="Credential IA signature is invalid"):
        verify_ballot(ballot, credential, ia_pk)


def test_verify_ballot_tampered_ciphertext(ballot, credential, ia_keys):
    """Flip a byte in ballot_ciphertext — signature check must fail."""
    import base64

    ia_pk, _ = ia_keys
    raw = base64.b64decode(ballot["ballot_ciphertext"])
    tampered_raw = bytes([raw[0] ^ 0xFF]) + raw[1:]
    tampered = dict(ballot, ballot_ciphertext=base64.b64encode(tampered_raw).decode())

    with pytest.raises(ValueError, match="Ballot Dilithium signature is invalid"):
        verify_ballot(tampered, credential, ia_pk)


def test_verify_ballot_voter_id_mismatch(ballot, credential, ia_keys):
    """Voter ID in ballot differs from credential — must be caught."""
    ia_pk, _ = ia_keys
    tampered = dict(ballot, voter_id="evil-voter-999")
    with pytest.raises(ValueError, match="voter_id mismatch"):
        verify_ballot(tampered, credential, ia_pk)


# ---------------------------------------------------------------------------
# Phase 3 — chain hash
# ---------------------------------------------------------------------------

def test_chain_hash_deterministic():
    payload = b"test payload"
    h1 = chain_hash("0" * 64, payload)
    h2 = chain_hash("0" * 64, payload)
    assert h1 == h2, "chain_hash must be deterministic"


def test_chain_hash_changes_with_prev():
    payload = b"test payload"
    h1 = chain_hash("0" * 64, payload)
    h2 = chain_hash("a" * 64, payload)
    assert h1 != h2, "Different prev_hash must produce different chain_hash"


# ---------------------------------------------------------------------------
# Phase 3 — decap + decrypt (Election Authority tally path)
# ---------------------------------------------------------------------------

def test_decap_and_decrypt_roundtrip(ballot, ea_keys):
    _, ea_sk = ea_keys
    vote = decap_and_decrypt(ballot, ea_sk)
    assert vote["candidate_id"] == "candidate-A"
    assert vote["election_id"] == "GE-2026"


def test_decap_shared_secret(ballot, ea_keys):
    _, ea_sk = ea_keys
    secret = decap_shared_secret(ea_sk, ballot["kem_ciphertext"])
    assert isinstance(secret, bytes)
    assert len(secret) == 32, "Kyber512 shared secret must be 32 bytes (256-bit AES key)"


def test_wrong_ea_key_cannot_decrypt(ballot, ea_keys):
    """A different EA secret key must not decrypt the ballot."""
    from cryptography.exceptions import InvalidTag

    _, other_ea_sk = generate_ea_keypair()
    # decap_secret with wrong key → wrong shared secret → AES-GCM tag mismatch
    with pytest.raises((InvalidTag, Exception)):
        decap_and_decrypt(ballot, other_ea_sk)

