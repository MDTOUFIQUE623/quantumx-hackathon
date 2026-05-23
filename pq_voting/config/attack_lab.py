"""Dedicated roll entries for live attack demos (isolated per attack type)."""

ATTACK_LAB_VOTER = {
    "name": "Attack Lab Voter",
    "dob": "1988-08-08",
    "aadhaar": "911122223333",
    "constituency_id": "MH-22-Pune",
    "eligible": True,
}

DOUBLE_VOTE_VOTER = {
    "name": "Double Vote Test",
    "dob": "1989-09-09",
    "aadhaar": "922233334444",
    "constituency_id": "MH-22-Pune",
    "eligible": True,
}

FORGED_SIG_VOTER = {
    "name": "Forged Sig Test",
    "dob": "1987-07-07",
    "aadhaar": "933344445555",
    "constituency_id": "MH-22-Pune",
    "eligible": True,
}

CONSTITUENCY_BIND_VOTER = {
    "name": "Constituency Bind Test",
    "dob": "1986-06-06",
    "aadhaar": "944455556666",
    "constituency_id": "MH-22-Pune",
    "eligible": True,
}

ATTACK_ROLL_ENTRIES = [
    ATTACK_LAB_VOTER,
    DOUBLE_VOTE_VOTER,
    FORGED_SIG_VOTER,
    CONSTITUENCY_BIND_VOTER,
]

ATTACK_VOTERS_BY_ID = {
    "double_vote": DOUBLE_VOTE_VOTER,
    "forged_signature": FORGED_SIG_VOTER,
    "wrong_constituency_vote": CONSTITUENCY_BIND_VOTER,
}
