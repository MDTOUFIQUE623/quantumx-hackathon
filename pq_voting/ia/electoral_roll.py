"""Simulated electoral roll checked by the Identity Authority before credential issuance."""

from dataclasses import dataclass

from pq_voting.config.demo_data import ELECTORAL_ROLL


@dataclass
class RollCheckResult:
    ok: bool
    message: str
    roll_entry: dict | None = None


def _normalize(value: str) -> str:
    return value.strip()


def find_by_aadhaar(aadhaar: str) -> dict | None:
    key = _normalize(aadhaar)
    for entry in ELECTORAL_ROLL:
        if entry["aadhaar"] == key:
            return entry
    return None


def check_eligibility(
    *,
    name: str,
    dob: str,
    aadhaar: str,
    constituency_id: str,
) -> RollCheckResult:
    """
    Simulate IA lookup against the constituency electoral roll.

    Production: replace with government electoral-roll / Aadhaar-linked API.
    """
    entry = find_by_aadhaar(aadhaar)
    if entry is None:
        return RollCheckResult(
            ok=False,
            message="Aadhaar-like ID not found on the electoral roll",
        )

    if not entry.get("eligible", True):
        return RollCheckResult(
            ok=False,
            message="Voter is marked ineligible on the electoral roll",
        )

    if _normalize(entry["name"]) != _normalize(name):
        return RollCheckResult(
            ok=False,
            message="Name does not match electoral roll record for this Aadhaar ID",
        )

    if _normalize(entry["dob"]) != _normalize(dob):
        return RollCheckResult(
            ok=False,
            message="Date of birth does not match electoral roll record",
        )

    roll_constituency = entry["constituency_id"]
    if constituency_id != roll_constituency:
        return RollCheckResult(
            ok=False,
            message=(
                f"Constituency mismatch: roll has {roll_constituency}, "
                f"registration requested {constituency_id}"
            ),
        )

    return RollCheckResult(ok=True, message="Eligible", roll_entry=entry)
