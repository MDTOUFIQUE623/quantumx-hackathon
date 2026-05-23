from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from pq_voting.api.deps import get_authority_keys
from pq_voting.crypto.credential import issue_voter_credential, verify_voter_credential
from pq_voting.db.ledger import get_voter, save_voter
from pq_voting.ia.electoral_roll import check_eligibility

router = APIRouter(tags=["register"])


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    dob: str = Field(min_length=4)
    aadhaar: str = Field(min_length=4)
    constituency_id: str
    dilithium_pk: str = Field(description="Hex-encoded voter Dilithium/ML-DSA public key")


class RegisterResponse(BaseModel):
    voter_id: str
    credential: dict


@router.post("/register", response_model=RegisterResponse)
def register_voter(body: RegisterRequest) -> RegisterResponse:
    try:
        bytes.fromhex(body.dilithium_pk)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid dilithium_pk hex") from exc

    roll = check_eligibility(
        name=body.name,
        dob=body.dob,
        aadhaar=body.aadhaar,
        constituency_id=body.constituency_id,
    )
    if not roll.ok:
        raise HTTPException(
            status_code=403,
            detail=f"Electoral roll check failed: {roll.message}",
        )

    # Constituency on the credential comes from the authoritative roll record.
    roll_entry = roll.roll_entry
    assert roll_entry is not None
    constituency_id = roll_entry["constituency_id"]

    keys = get_authority_keys()
    credential = issue_voter_credential(
        keys.ia_secret_key,
        name=body.name,
        dob=body.dob,
        aadhaar=body.aadhaar,
        constituency_id=constituency_id,
        dilithium_pk_hex=body.dilithium_pk,
    )

    if not verify_voter_credential(credential, keys.ia_public_key):
        raise HTTPException(status_code=500, detail="Credential self-check failed")

    existing = get_voter(credential["voter_id"])
    if existing is not None:
        raise HTTPException(status_code=409, detail="Voter already registered")

    save_voter(
        credential["voter_id"],
        credential["constituency_id"],
        credential,
    )
    return RegisterResponse(voter_id=credential["voter_id"], credential=credential)
