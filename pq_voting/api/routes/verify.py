from fastapi import APIRouter, HTTPException

from pq_voting.db.ledger import get_ballot, to_public_ballot

router = APIRouter(tags=["verify"])


@router.get("/verify/{ballot_id}")
def verify_receipt(ballot_id: str) -> dict:
    """Public receipt lookup — confirms ballot is on the append-only board."""
    ballot = get_ballot(ballot_id)
    if ballot is None:
        raise HTTPException(status_code=404, detail="Ballot not found on bulletin board")

    public = to_public_ballot(ballot)
    public["on_board"] = True
    return public
