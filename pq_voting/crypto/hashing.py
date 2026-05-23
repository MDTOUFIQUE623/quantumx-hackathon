import hashlib


def sha3_256_hex(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


def biometric_hash(name: str, dob: str, aadhaar: str) -> str:
    payload = f"{name}|{dob}|{aadhaar}".encode("utf-8")
    return sha3_256_hex(payload)


def chain_hash(prev_hash: str, payload: bytes) -> str:
    h = hashlib.sha3_256()
    h.update(prev_hash.encode("utf-8"))
    h.update(payload)
    return h.hexdigest()
