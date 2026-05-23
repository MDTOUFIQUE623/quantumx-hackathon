from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pq_voting.api.deps import get_authority_keys
from pq_voting.crypto.ballot import decap_shared_secret, shared_secret_fingerprint
from pq_voting.crypto.credential import verify_ballot_signature
from pq_voting.crypto.encoding import canonical_json_bytes

router = APIRouter(tags=["interop"])


class VerifySignatureRequest(BaseModel):
    message: str
    signature_b64: str
    public_key_hex: str


class VerifySignatureResponse(BaseModel):
    valid: bool


class DecapKemRequest(BaseModel):
    kem_ciphertext_b64: str


class DecapKemResponse(BaseModel):
    shared_secret_fingerprint: str


@router.post("/interop/verify-signature", response_model=VerifySignatureResponse)
def interop_verify_signature(body: VerifySignatureRequest) -> VerifySignatureResponse:
    try:
        message = body.message.encode("utf-8")
        valid = verify_ballot_signature(
            message, body.signature_b64, body.public_key_hex
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VerifySignatureResponse(valid=valid)


@router.post("/interop/decap-kem", response_model=DecapKemResponse)
def interop_decap_kem(body: DecapKemRequest) -> DecapKemResponse:
    keys = get_authority_keys()
    try:
        secret = decap_shared_secret(keys.ea_secret_key, body.kem_ciphertext_b64)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DecapKemResponse(shared_secret_fingerprint=shared_secret_fingerprint(secret))


@router.post("/interop/verify-ballot-payload")
def interop_verify_ballot_payload(body: dict) -> dict:
    """Verify a canonical JSON ballot signing payload from the browser."""
    payload = canonical_json_bytes(body)
    signature_b64 = body.get("signature_b64")
    public_key_hex = body.get("public_key_hex")
    if not signature_b64 or not public_key_hex:
        raise HTTPException(
            status_code=400,
            detail="signature_b64 and public_key_hex required",
        )
    unsigned = {k: v for k, v in body.items() if k not in ("signature_b64", "public_key_hex")}
    payload = canonical_json_bytes(unsigned)
    valid = verify_ballot_signature(payload, signature_b64, public_key_hex)
    return {"valid": valid, "payload_hex": payload.hex()[:64] + "..."}
