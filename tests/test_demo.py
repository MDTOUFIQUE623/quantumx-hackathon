"""Phase 7 — demo / attack catalog endpoints."""
from fastapi.testclient import TestClient

from pq_voting.api.main import app
from pq_voting.config.attack_lab import ATTACK_ROLL_ENTRIES, ATTACK_VOTERS_BY_ID
from pq_voting.config.demo_data import ELECTORAL_ROLL

client = TestClient(app)


def test_attack_catalog():
    r = client.get("/api/demo/attacks")
    assert r.status_code == 200
    body = r.json()
    assert len(body["attacks"]) >= 7
    ids = {a["id"] for a in body["attacks"]}
    assert "double_vote" in ids
    assert "quantum_hndl" in ids
    assert body["attack_voters"]["double_vote"]["aadhaar"] == "922233334444"


def test_attack_roll_entries_on_electoral_roll():
    for entry in ATTACK_ROLL_ENTRIES:
        assert entry in ELECTORAL_ROLL


def test_attack_voters_eligible():
    from pq_voting.ia.electoral_roll import check_eligibility

    for voter in ATTACK_VOTERS_BY_ID.values():
        result = check_eligibility(
            name=voter["name"],
            dob=voter["dob"],
            aadhaar=voter["aadhaar"],
            constituency_id=voter["constituency_id"],
        )
        assert result.ok, result.message
