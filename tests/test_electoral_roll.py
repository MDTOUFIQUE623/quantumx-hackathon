"""IA electoral roll checks at registration."""
import oqs
from fastapi.testclient import TestClient

from pq_voting.api.main import app
from pq_voting.crypto.keygen import sig_alg
from pq_voting.ia.electoral_roll import check_eligibility

client = TestClient(app)


def test_roll_check_unit():
    ok = check_eligibility(
        name="Ananya Desai",
        dob="1998-04-12",
        aadhaar="900011112222",
        constituency_id="MH-22-Pune",
    )
    assert ok.ok

    bad = check_eligibility(
        name="Ananya Desai",
        dob="1998-04-12",
        aadhaar="900011112222",
        constituency_id="DL-07-Delhi",
    )
    assert not bad.ok
    assert "Constituency mismatch" in bad.message


def test_register_rejects_unknown_aadhaar():
    with oqs.Signature(sig_alg()) as sig:
        pk = sig.generate_keypair()

    r = client.post(
        "/api/register",
        json={
            "name": "Ghost Voter",
            "dob": "2000-01-01",
            "aadhaar": "000000000000",
            "constituency_id": "MH-22-Pune",
            "dilithium_pk": pk.hex(),
        },
    )
    assert r.status_code == 403
    assert "Electoral roll" in r.json()["detail"]


def test_register_rejects_constituency_mismatch():
    with oqs.Signature(sig_alg()) as sig:
        pk = sig.generate_keypair()

    r = client.post(
        "/api/register",
        json={
            "name": "Ananya Desai",
            "dob": "1998-04-12",
            "aadhaar": "900011112222",
            "constituency_id": "DL-07-Delhi",
            "dilithium_pk": pk.hex(),
        },
    )
    assert r.status_code == 403


def test_register_accepts_roll_match():
    with oqs.Signature(sig_alg()) as sig:
        pk = sig.generate_keypair()

    r = client.post(
        "/api/register",
        json={
            "name": "Kabir Singh",
            "dob": "1995-09-03",
            "aadhaar": "900033334444",
            "constituency_id": "DL-07-Delhi",
            "dilithium_pk": pk.hex(),
        },
    )
    assert r.status_code == 200
    assert r.json()["credential"]["constituency_id"] == "DL-07-Delhi"
