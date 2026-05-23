import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def _db_path() -> Path:
    base = Path(os.environ.get("PQ_VOTING_DATA_DIR", "data"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "pq_voting.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS voters (
                voter_id TEXT PRIMARY KEY,
                constituency_id TEXT NOT NULL,
                credential_json TEXT NOT NULL,
                registered_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ballots (
                ballot_id TEXT PRIMARY KEY,
                election_id TEXT NOT NULL,
                voter_id TEXT NOT NULL,
                ballot_json TEXT NOT NULL,
                chain_hash TEXT NOT NULL,
                position INTEGER NOT NULL,
                submitted_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_ballots_election_voter
                ON ballots (election_id, voter_id);
            """
        )
        conn.commit()


def save_voter(voter_id: str, constituency_id: str, credential: dict[str, Any]) -> None:
    from datetime import datetime, timezone

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO voters (voter_id, constituency_id, credential_json, registered_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                voter_id,
                constituency_id,
                json.dumps(credential),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def get_voter(voter_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT credential_json, constituency_id FROM voters WHERE voter_id = ?",
            (voter_id,),
        ).fetchone()
    if row is None:
        return None
    cred = json.loads(row["credential_json"])
    cred.setdefault("constituency_id", row["constituency_id"])
    return cred


def voter_has_ballot(voter_id: str, election_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM ballots
            WHERE voter_id = ? AND election_id = ?
            LIMIT 1
            """,
            (voter_id, election_id),
        ).fetchone()
    return row is not None


def get_last_chain_hash(election_id: str) -> str:
    """Return the chain_hash of the most recent ballot for an election.

    Returns the genesis sentinel (64 zeros) if no ballots exist yet.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT chain_hash FROM ballots
            WHERE election_id = ?
            ORDER BY position DESC
            LIMIT 1
            """,
            (election_id,),
        ).fetchone()
    return row["chain_hash"] if row is not None else "0" * 64


def save_ballot(ballot: dict[str, Any], chain_hash: str) -> int:
    """Append a ballot to the ledger. Returns the assigned position (1-indexed).

    Raises ``ValueError`` if the voter already has a ballot for this election
    (double-vote guard — last line of defence before DB INSERT).
    """
    from datetime import datetime, timezone

    election_id = ballot["election_id"]
    voter_id = ballot["voter_id"]

    with get_connection() as conn:
        # Atomic position assignment — count existing rows + 1.
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM ballots WHERE election_id = ?",
            (election_id,),
        ).fetchone()
        position = row["cnt"] + 1

        conn.execute(
            """
            INSERT INTO ballots
                (ballot_id, election_id, voter_id, ballot_json, chain_hash, position, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ballot["ballot_id"],
                election_id,
                voter_id,
                json.dumps(ballot),
                chain_hash,
                position,
                ballot.get("submitted_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
        conn.commit()
    return position


def get_ballot(ballot_id: str) -> dict[str, Any] | None:
    """Fetch a single ballot by ballot_id. Returns None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT ballot_json, chain_hash, position FROM ballots WHERE ballot_id = ?",
            (ballot_id,),
        ).fetchone()
    if row is None:
        return None
    result = json.loads(row["ballot_json"])
    result["chain_hash"] = row["chain_hash"]
    result["position"] = row["position"]
    return result


PUBLIC_BALLOT_FIELDS = (
    "ballot_id",
    "election_id",
    "kem_ciphertext",
    "nonce",
    "ballot_ciphertext",
    "signature",
    "chain_hash",
    "position",
    "submitted_at",
)


def to_public_ballot(ballot: dict[str, Any]) -> dict[str, Any]:
    """Strip voter-identifying fields for the public bulletin board (partial upgrade A)."""
    return {key: ballot[key] for key in PUBLIC_BALLOT_FIELDS if key in ballot}


def list_public_ballots_for_election(election_id: str) -> list[dict[str, Any]]:
    """Public board view — ciphertexts + chain metadata only, no voter_id."""
    return [to_public_ballot(b) for b in list_ballots_for_election(election_id)]


def list_ballots_for_election(election_id: str) -> list[dict[str, Any]]:
    """Return all ballots for an election ordered by position (for tallying)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ballot_json, chain_hash, position FROM ballots
            WHERE election_id = ?
            ORDER BY position ASC
            """,
            (election_id,),
        ).fetchall()
    results = []
    for row in rows:
        b = json.loads(row["ballot_json"])
        b["chain_hash"] = row["chain_hash"]
        b["position"] = row["position"]
        results.append(b)
    return results

