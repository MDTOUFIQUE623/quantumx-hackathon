"""Phase 5 — Election Authority tally."""
import oqs
from fastapi.testclient import TestClient

from pq_voting.api.main import app
from pq_voting.crypto.ballot import build_ballot
from pq_voting.crypto.keygen import sig_alg
from pq_voting.db.tally_store import get_tally_result

client = TestClient(app)


def _cast_vote(voter_name: str, aadhaar: str, constituency: str, candidate_id: str):
    with oqs.Signature(sig_alg()) as sig:
        voter_pk = sig.generate_keypair()
        voter_sk = sig.export_secret_key()

    reg = client.post(
        "/api/register",
        json={
            "name": voter_name,
            "dob": "1990-05-05",
            "aadhaar": aadhaar,
            "constituency_id": constituency,
            "dilithium_pk": voter_pk.hex(),
        },
    )
    assert reg.status_code == 200
    cred = reg.json()["credential"]
    ea_pk = bytes.fromhex(client.get("/api/authorities/ea-public-key").json()["ea_public_key"])
    ballot = build_ballot(
        candidate_id=candidate_id,
        election_id="election-2026-local",
        voter_id=cred["voter_id"],
        voter_secret_key=voter_sk,
        ea_public_key=ea_pk,
    )
    vote = client.post(
        "/api/vote",
        json={"ballot": ballot, "constituency_id": cred["constituency_id"]},
    )
    assert vote.status_code == 200
    return ballot


def test_tally_counts_votes():
    _cast_vote("Tally A", "810011112222", "MH-22-Pune", "c1")
    _cast_vote("Tally B", "810022223333", "DL-07-Delhi", "c1")
    _cast_vote("Tally C", "810033334444", "KA-12-Bangalore", "c2")

    r = client.post("/api/tally/election-2026-local")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["valid_ballots_counted"] >= 3
    by_id = {c["candidate_id"]: c["votes"] for c in body["counts"]}
    assert by_id["c1"] >= 2
    assert by_id["c2"] >= 1

    for row in body["anonymized_votes"]:
        assert "voter_id" not in row
        assert "candidate_id" in row

    cached = client.get("/api/tally/election-2026-local")
    assert cached.status_code == 200
    assert cached.json()["election_id"] == "election-2026-local"
    assert get_tally_result("election-2026-local") is not None


def test_tally_unknown_election():
    r = client.post("/api/tally/not-real")
    assert r.status_code == 404


def test_get_tally_before_publish():
    r = client.get("/api/tally/election-2026-state")
    if r.status_code == 404:
        assert "No tally" in r.json()["detail"]
