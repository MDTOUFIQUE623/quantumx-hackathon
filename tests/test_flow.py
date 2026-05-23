"""End-to-end vote flow: register → build ballot → POST /vote → verify receipt."""
import oqs
from fastapi.testclient import TestClient

from pq_voting.api.main import app
from pq_voting.crypto.ballot import build_ballot, decap_and_decrypt
from pq_voting.crypto.keygen import sig_alg

client = TestClient(app)


def test_full_vote_flow():
    with oqs.Signature(sig_alg()) as sig:
        voter_pk = sig.generate_keypair()
        voter_sk = sig.export_secret_key()

    reg = client.post(
        "/api/register",
        json={
            "name": "Flow Voter",
            "dob": "1993-07-20",
            "aadhaar": "700011112333",
            "constituency_id": "KA-12-Bangalore",
            "dilithium_pk": voter_pk.hex(),
        },
    )
    assert reg.status_code == 200
    credential = reg.json()["credential"]
    voter_id = credential["voter_id"]
    constituency_id = credential["constituency_id"]

    ea_pk = bytes.fromhex(client.get("/api/authorities/ea-public-key").json()["ea_public_key"])

    ballot = build_ballot(
        candidate_id="c1",
        election_id="election-2026-local",
        voter_id=voter_id,
        voter_secret_key=voter_sk,
        ea_public_key=ea_pk,
    )

    vote = client.post(
        "/api/vote",
        json={"ballot": ballot, "constituency_id": constituency_id},
    )
    assert vote.status_code == 200, vote.text
    receipt = vote.json()
    assert receipt["ballot_id"] == ballot["ballot_id"]
    assert len(receipt["chain_hash"]) == 64
    assert receipt["position"] >= 1

    verify = client.get(f"/api/verify/{receipt['ballot_id']}")
    assert verify.status_code == 200
    assert verify.json()["chain_hash"] == receipt["chain_hash"]

    # Double vote must be rejected.
    again = client.post(
        "/api/vote",
        json={"ballot": ballot, "constituency_id": constituency_id},
    )
    assert again.status_code == 409

    # EA can decrypt the stored ballot (tally path preview).
    from pq_voting.api.deps import get_authority_keys

    ea_sk = get_authority_keys().ea_secret_key
    plain = decap_and_decrypt(ballot, ea_sk)
    assert plain["candidate_id"] == "c1"


def test_vote_wrong_constituency_rejected():
    with oqs.Signature(sig_alg()) as sig:
        voter_pk = sig.generate_keypair()
        voter_sk = sig.export_secret_key()

    reg = client.post(
        "/api/register",
        json={
            "name": "Wrong Constituency",
            "dob": "1991-01-01",
            "aadhaar": "700022223333",
            "constituency_id": "DL-07-Delhi",
            "dilithium_pk": voter_pk.hex(),
        },
    )
    credential = reg.json()["credential"]
    ea_pk = bytes.fromhex(client.get("/api/authorities/ea-public-key").json()["ea_public_key"])
    ballot = build_ballot(
        candidate_id="c1",
        election_id="election-2026-local",
        voter_id=credential["voter_id"],
        voter_secret_key=voter_sk,
        ea_public_key=ea_pk,
    )

    r = client.post(
        "/api/vote",
        json={"ballot": ballot, "constituency_id": "MH-22-Pune"},
    )
    assert r.status_code == 403
