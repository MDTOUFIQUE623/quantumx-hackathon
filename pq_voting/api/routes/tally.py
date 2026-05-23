import os
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException

from pq_voting.api.deps import get_authority_keys
from pq_voting.config.demo_data import ELECTIONS
from pq_voting.config.elections import get_election
from pq_voting.crypto.tally import tally_election
from pq_voting.db.tally_store import get_tally_result, save_tally_result

router = APIRouter(tags=["tally"])


def _require_ea_authority(x_ea_key: str | None) -> None:
    """Optional API key gate for tally (set PQ_EA_TALLY_KEY in production demos)."""
    expected = os.environ.get("PQ_EA_TALLY_KEY")
    if not expected:
        return
    if x_ea_key != expected:
        raise HTTPException(status_code=403, detail="Election Authority tally key required")


@router.get("/tally/elections")
def list_tally_elections() -> dict:
    return {
        "elections": [
            {"election_id": e["election_id"], "title": e["title"]} for e in ELECTIONS
        ]
    }


@router.post("/tally/{election_id}")
def run_tally(
    election_id: str,
    x_ea_key: str | None = Header(default=None, alias="X-EA-Key"),
) -> dict:
    """
    Election Authority decrypts all ballots for an election and publishes counts.

    Requires ``X-EA-Key`` header when ``PQ_EA_TALLY_KEY`` env var is set.
    """
    _require_ea_authority(x_ea_key)

    if get_election(election_id) is None:
        raise HTTPException(status_code=404, detail="Unknown election")

    keys = get_authority_keys()
    try:
        result = tally_election(election_id, keys.ea_secret_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result["tallied_at"] = datetime.now(timezone.utc).isoformat()
    save_tally_result(result)
    return result


@router.get("/tally/{election_id}")
def get_tally(election_id: str) -> dict:
    """Return the last published tally for an election (public results)."""
    if get_election(election_id) is None:
        raise HTTPException(status_code=404, detail="Unknown election")

    result = get_tally_result(election_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No tally published yet — POST /api/tally/{election_id} as EA",
        )
    return result
