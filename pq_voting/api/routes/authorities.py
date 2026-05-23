from fastapi import APIRouter

from pq_voting.api.deps import get_authority_keys
from pq_voting.crypto.keygen import kem_alg, sig_alg
from pq_voting.config.demo_data import CONSTITUENCIES, DEMO_VOTERS, ELECTIONS, ELECTORAL_ROLL

router = APIRouter(tags=["authorities"])


@router.get("/authorities/ia-public-key")
def ia_public_key() -> dict:
    keys = get_authority_keys()
    return {"ia_public_key": keys.ia_public_key.hex()}


@router.get("/authorities/ea-public-key")
def ea_public_key() -> dict:
    keys = get_authority_keys()
    return {"ea_public_key": keys.ea_public_key.hex()}


@router.get("/authorities/public-keys")
def public_keys() -> dict:
    keys = get_authority_keys()
    return {
        "ia_public_key_hex": keys.ia_public_key.hex(),
        "ea_public_key_hex": keys.ea_public_key.hex(),
        "algorithms": {"signature": sig_alg(), "kem": kem_alg()},
        "browser_algorithms": {
            "signature": "ML-DSA-44 (createMLDSA44)",
            "kem": "Kyber512 (createKyber512)",
        },
    }


@router.get("/demo/config")
def demo_config() -> dict:
    return {
        "constituencies": CONSTITUENCIES,
        "elections": ELECTIONS,
        "demo_voters": DEMO_VOTERS,
        "sample_eligible_voters": DEMO_VOTERS,
        "electoral_roll_size": len(ELECTORAL_ROLL),
        "judge_demo_url": "/demo.html",
        "attack_lab_url": "/attacks.html",
        "pitch_url": "/pitch.html",
        "ia_note": (
            "Registration checks name, DOB, Aadhaar-like ID, and constituency against "
            "a simulated electoral roll before issuing a signed credential."
        ),
    }


@router.get("/electoral-roll/samples")
def sample_eligible_voters() -> dict:
    """Pre-filled voters for judges — same rows as the demo UI quick-fill."""
    return {
        "voters": DEMO_VOTERS,
        "note": (
            "All four fields must match the simulated electoral roll exactly. "
            "See /demo.html for a printable table and rejection scenarios."
        ),
    }
