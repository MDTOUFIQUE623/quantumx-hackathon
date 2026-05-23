from fastapi import APIRouter, HTTPException

from pq_voting.config.demo_data import ELECTIONS
from pq_voting.db.ledger import (
    get_ballot,
    list_public_ballots_for_election,
    to_public_ballot,
)

router = APIRouter(tags=["board"])


def _election_title(election_id: str) -> str:
    for election in ELECTIONS:
        if election["election_id"] == election_id:
            return election["title"]
    return election_id


@router.get("/board/elections")
def list_board_elections() -> dict:
    """Elections available for the public bulletin board."""
    return {
        "elections": [
            {"election_id": e["election_id"], "title": e["title"]} for e in ELECTIONS
        ]
    }


@router.get("/board/{election_id}")
def public_bulletin_board(election_id: str) -> dict:
    """
    Public append-only bulletin board (partial upgrade A).

    Returns encrypted ballot blobs and chain hashes only — no voter_id.
    voter_id remains in the private DB table for double-vote enforcement.
    """
    ballots = list_public_ballots_for_election(election_id)
    latest_chain_hash = ballots[-1]["chain_hash"] if ballots else "0" * 64

    return {
        "election_id": election_id,
        "title": _election_title(election_id),
        "ballot_count": len(ballots),
        "genesis_chain_hash": "0" * 64,
        "latest_chain_hash": latest_chain_hash,
        "privacy_note": (
            "voter_id is withheld on this public view. Production would add a "
            "mix-net for full ballot anonymity."
        ),
        "ballots": ballots,
    }


@router.get("/board/ballot/{ballot_id}")
def public_ballot_detail(ballot_id: str) -> dict:
    """Single ballot on the public board (no voter_id)."""
    ballot = get_ballot(ballot_id)
    if ballot is None:
        raise HTTPException(status_code=404, detail="Ballot not found")

    return to_public_ballot(ballot)
