from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from pq_voting.api.deps import get_authority_keys
from pq_voting.crypto.ballot import verify_ballot
from pq_voting.db.ledger import (
    get_last_chain_hash,
    get_voter,
    save_ballot,
    voter_has_ballot,
)

router = APIRouter(tags=["vote"])


class VoteRequest(BaseModel):
    """Ballot built and signed in the browser."""

    ballot: dict = Field(description="Encrypted + signed ballot object")
    constituency_id: str = Field(
        description="Must match the IA-signed credential (anti cross-jurisdiction fraud)"
    )


class VoteResponse(BaseModel):
    ballot_id: str
    chain_hash: str
    position: int
    election_id: str


@router.post("/vote", response_model=VoteResponse)
def submit_vote(body: VoteRequest) -> VoteResponse:
    ballot = dict(body.ballot)
    voter_id = ballot.get("voter_id")
    election_id = ballot.get("election_id")

    if not voter_id or not election_id:
        raise HTTPException(
            status_code=400,
            detail="ballot must include voter_id and election_id",
        )

    credential = get_voter(voter_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Voter not registered")

    if body.constituency_id != credential["constituency_id"]:
        raise HTTPException(
            status_code=403,
            detail="constituency_id does not match voter credential",
        )

    if voter_has_ballot(voter_id, election_id):
        raise HTTPException(
            status_code=409,
            detail="Voter already cast a ballot for this election",
        )

    ballot.setdefault("ballot_id", str(uuid4()))

    keys = get_authority_keys()
    prev_hash = get_last_chain_hash(election_id)

    try:
        receipt = verify_ballot(
            ballot,
            credential,
            keys.ia_public_key,
            prev_chain_hash=prev_hash,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    position = save_ballot(ballot, receipt["chain_hash"])

    return VoteResponse(
        ballot_id=ballot["ballot_id"],
        chain_hash=receipt["chain_hash"],
        position=position,
        election_id=election_id,
    )
