from fastapi import APIRouter

from pq_voting.config.attack_lab import ATTACK_LAB_VOTER, ATTACK_VOTERS_BY_ID

router = APIRouter(tags=["demo"])

ATTACK_CATALOG = [
    {
        "id": "fake_voter",
        "title": "Register without electoral roll",
        "threat": "Fake identity / ballot stuffing at registration",
        "expected_status": 403,
        "mitigation": "IA checks name, DOB, Aadhaar-like ID, and constituency against the roll",
        "plain_example": (
            "Someone shows up with a made-up ID number that is not on the voter list. "
            "Like trying to open a bank account with a passport the bank has never heard of — "
            "the system says no and does not give them a voter pass."
        ),
    },
    {
        "id": "cross_constituency",
        "title": "Cross-constituency registration",
        "threat": "Vote in a jurisdiction where the voter is not eligible",
        "expected_status": 403,
        "mitigation": "Roll binds constituency; credential is signed for that constituency only",
        "plain_example": (
            "Ananya is registered to vote in Pune, but she selects Delhi on the form. "
            "The roll says she belongs in Pune only — registration is rejected, like boarding "
            "the wrong flight with a ticket for another city."
        ),
    },
    {
        "id": "double_vote",
        "title": "Double vote in same election",
        "threat": "One person casts multiple ballots",
        "expected_status": 409,
        "mitigation": "Append-only ledger enforces one ballot per voter_id per election",
        "plain_example": (
            "The same person tries to vote twice in the same election. "
            "The first ballot is accepted; the second is refused — like scanning your ticket "
            "at the cinema a second time: the system remembers you already entered."
        ),
    },
    {
        "id": "forged_signature",
        "title": "Forged ballot signature",
        "threat": "Inject or alter a ballot without the voter's Dilithium key",
        "expected_status": 400,
        "mitigation": "Bulletin board verifies ML-DSA signature over canonical ballot payload",
        "plain_example": (
            "An attacker changes the vote package and fakes the voter's digital signature. "
            "Like signing a cheque with the wrong handwriting — the bank's verifier spots "
            "that the signature does not match the account holder's key."
        ),
    },
    {
        "id": "wrong_constituency_vote",
        "title": "Vote with wrong constituency_id",
        "threat": "Use a valid credential from Pune to vote as if from Delhi",
        "expected_status": 403,
        "mitigation": "POST /vote requires constituency_id to match IA-signed credential",
        "plain_example": (
            "A voter has a valid Pune pass but tries to submit a ballot claiming they are "
            "in Delhi. The pass and the ballot do not match — rejected, like using a school ID "
            "from one campus to enter another campus's exam hall."
        ),
    },
    {
        "id": "unregistered_voter",
        "title": "Ballot from unregistered voter_id",
        "threat": "Skip registration and submit a ballot directly",
        "expected_status": 404,
        "mitigation": "Server loads credential by voter_id; unknown voters are rejected",
        "plain_example": (
            "Someone skips the registration desk and drops a ballot in the box anyway. "
            "There is no record that they were checked in — the system says "
            "'we do not know this voter' and ignores the ballot."
        ),
    },
    {
        "id": "quantum_hndl",
        "title": "Harvest now, decrypt later (quantum)",
        "threat": "Store today's RSA-encrypted ballots; decrypt when a CRQC arrives",
        "expected_status": None,
        "mitigation": "ML-KEM (Kyber512) for ballot encryption — lattice problem, not factoring",
        "educational_only": True,
        "plain_example": (
            "A spy copies locked ballot boxes today hoping to pick the lock when a "
            "super-powerful quantum computer exists in 10 years. Old-style math locks "
            "(RSA) may break; our locks use a different puzzle (lattice math) that quantum "
            "machines are not known to solve quickly."
        ),
    },
]


@router.get("/demo/attacks")
def attack_catalog() -> dict:
    return {
        "attacks": ATTACK_CATALOG,
        "attack_lab_voter": ATTACK_LAB_VOTER,
        "attack_voters": ATTACK_VOTERS_BY_ID,
        "default_election_id": "election-2026-local",
        "reset_hint": "Delete data/pq_voting.db to replay attacks that need a fresh registration.",
        "note": "Run live demos at /attacks.html — each button calls the real API.",
    }
