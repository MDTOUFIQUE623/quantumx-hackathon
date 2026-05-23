from pq_voting.config.demo_data import ELECTIONS


def get_election(election_id: str) -> dict | None:
    for election in ELECTIONS:
        if election["election_id"] == election_id:
            return election
    return None


def valid_candidate_ids(election_id: str) -> set[str]:
    election = get_election(election_id)
    if election is None:
        return set()
    return {c["candidate_id"] for c in election["candidates"]}


def candidate_name_map(election_id: str) -> dict[str, str]:
    election = get_election(election_id)
    if election is None:
        return {}
    return {c["candidate_id"]: c["name"] for c in election["candidates"]}
