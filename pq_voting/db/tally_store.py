import json
import os
from pathlib import Path
from typing import Any


def _tally_dir() -> Path:
    base = Path(os.environ.get("PQ_VOTING_DATA_DIR", "data"))
    path = base / "tallies"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_tally_result(result: dict[str, Any]) -> None:
    election_id = result["election_id"]
    path = _tally_dir() / f"{election_id}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def get_tally_result(election_id: str) -> dict[str, Any] | None:
    path = _tally_dir() / f"{election_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
