"""Public bulletin board API — no voter_id on public views."""
import oqs
from fastapi.testclient import TestClient

from pq_voting.api.main import app
from pq_voting.crypto.ballot import build_ballot
from pq_voting.crypto.keygen import sig_alg

client = TestClient(app)


def _register_and_vote():
    with oqs.Signature(sig_alg()) as sig:
        voter_pk = sig.generate_keypair()
        voter_sk = sig.export_secret_key()

    reg = client.post(
        "/api/register",
        json={
            "name": "Board Viewer",
            "dob": "1994-02-02",
            "aadhaar": "600011112222",
            "constituency_id": "MH-22-Pune",
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
    vote = client.post(
        "/api/vote",
        json={"ballot": ballot, "constituency_id": credential["constituency_id"]},
    )
    assert vote.status_code == 200
    return ballot, vote.json()


def test_public_board_hides_voter_id():
    ballot, _receipt = _register_and_vote()

    board = client.get("/api/board/election-2026-local")
    assert board.status_code == 200
    body = board.json()
    assert body["ballot_count"] >= 1
    assert "voter_id" not in body
    for entry in body["ballots"]:
        assert "voter_id" not in entry
        assert "ballot_id" in entry
        assert "chain_hash" in entry
        assert "kem_ciphertext" in entry

    detail = client.get(f"/api/board/ballot/{ballot['ballot_id']}")
    assert detail.status_code == 200
    assert "voter_id" not in detail.json()

    verify = client.get(f"/api/verify/{ballot['ballot_id']}")
    assert verify.status_code == 200
    assert "voter_id" not in verify.json()
    assert verify.json()["on_board"] is True


def test_board_elections_list():
    r = client.get("/api/board/elections")
    assert r.status_code == 200
    assert len(r.json()["elections"]) >= 1
