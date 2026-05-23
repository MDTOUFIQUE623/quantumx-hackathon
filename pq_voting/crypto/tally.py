"""Election Authority tally — decrypt ballots and aggregate results (Phase 5)."""

from collections import Counter
from typing import Any

from cryptography.exceptions import InvalidTag

from pq_voting.config.elections import candidate_name_map, get_election, valid_candidate_ids
from pq_voting.crypto.ballot import decap_and_decrypt
from pq_voting.db.ledger import list_ballots_for_election


def tally_election(election_id: str, ea_secret_key: bytes) -> dict[str, Any]:
    """
    Decrypt all ballots for an election and produce anonymized results.

    Partial upgrade C: after decryption, reject ballots whose ``candidate_id``
    is not on the official list for this election.
    """
    election = get_election(election_id)
    if election is None:
        raise ValueError(f"Unknown election: {election_id}")

    allowed = valid_candidate_ids(election_id)
    names = candidate_name_map(election_id)
    ballots = list_ballots_for_election(election_id)

    counts: Counter[str] = Counter()
    anonymized: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for ballot in ballots:
        ballot_id = ballot["ballot_id"]
        position = ballot["position"]
        try:
            vote = decap_and_decrypt(ballot, ea_secret_key)
        except (InvalidTag, ValueError, KeyError) as exc:
            rejected.append(
                {
                    "ballot_id": ballot_id,
                    "position": position,
                    "reason": f"decryption failed: {exc}",
                }
            )
            continue

        if vote.get("election_id") != election_id:
            rejected.append(
                {
                    "ballot_id": ballot_id,
                    "position": position,
                    "reason": "plaintext election_id mismatch",
                }
            )
            continue

        candidate_id = vote.get("candidate_id")
        if candidate_id not in allowed:
            rejected.append(
                {
                    "ballot_id": ballot_id,
                    "position": position,
                    "reason": f"invalid candidate_id: {candidate_id!r}",
                }
            )
            continue

        counts[candidate_id] += 1
        anonymized.append(
            {
                "ballot_id": ballot_id,
                "position": position,
                "candidate_id": candidate_id,
                "chain_hash": ballot.get("chain_hash"),
            }
        )

    results = [
        {
            "candidate_id": cid,
            "name": names.get(cid, cid),
            "votes": counts[cid],
        }
        for cid in sorted(allowed, key=lambda c: (-counts[c], c))
    ]

    return {
        "election_id": election_id,
        "title": election["title"],
        "total_ballots_on_board": len(ballots),
        "valid_ballots_counted": len(anonymized),
        "rejected_ballots": len(rejected),
        "counts": results,
        "anonymized_votes": anonymized,
        "rejected": rejected,
        "integrity_note": (
            "Well-formedness is checked after EA decryption (partial upgrade C). "
            "ZK proofs would validate votes without decryption in production."
        ),
    }
