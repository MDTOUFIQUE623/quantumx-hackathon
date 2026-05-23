import json
import os
from dataclasses import dataclass
from pathlib import Path

import oqs


def _pick_sig(fallbacks: list[str]) -> str:
    enabled = oqs.get_enabled_sig_mechanisms()
    for candidate in fallbacks:
        if candidate in enabled:
            return candidate
    raise RuntimeError(f"No enabled signature algorithm among {fallbacks}")


def _pick_kem(fallbacks: list[str]) -> str:
    enabled = oqs.get_enabled_kem_mechanisms()
    for candidate in fallbacks:
        if candidate in enabled:
            return candidate
    raise RuntimeError(f"No enabled KEM algorithm among {fallbacks}")


SIG_ALG = None  # resolved on first use
KEM_ALG = None


def sig_alg() -> str:
    global SIG_ALG
    if SIG_ALG is None:
        SIG_ALG = _pick_sig(["Dilithium2", "ML-DSA-44"])
    return SIG_ALG


def kem_alg() -> str:
    global KEM_ALG
    if KEM_ALG is None:
        KEM_ALG = _pick_kem(["Kyber512", "ML-KEM-512"])
    return KEM_ALG


@dataclass
class AuthorityKeys:
    ia_public_key: bytes
    ia_secret_key: bytes
    ea_public_key: bytes
    ea_secret_key: bytes


def _keys_dir() -> Path:
    base = Path(os.environ.get("PQ_VOTING_DATA_DIR", "data"))
    path = base / "keys"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_keypair(path: Path, public_key: bytes, secret_key: bytes) -> None:
    path.write_text(
        json.dumps(
            {"public_key": public_key.hex(), "secret_key": secret_key.hex()},
            indent=2,
        ),
        encoding="utf-8",
    )


def _read_keypair(path: Path) -> tuple[bytes, bytes]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return bytes.fromhex(raw["public_key"]), bytes.fromhex(raw["secret_key"])


def generate_ia_keypair() -> tuple[bytes, bytes]:
    with oqs.Signature(sig_alg()) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()
    return public_key, secret_key


def generate_ea_keypair() -> tuple[bytes, bytes]:
    with oqs.KeyEncapsulation(kem_alg()) as kem:
        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()
    return public_key, secret_key


def load_or_create_authority_keys() -> AuthorityKeys:
    keys_dir = _keys_dir()
    ia_path = keys_dir / "ia.json"
    ea_path = keys_dir / "ea.json"

    if not ia_path.exists():
        ia_pk, ia_sk = generate_ia_keypair()
        _write_keypair(ia_path, ia_pk, ia_sk)
    if not ea_path.exists():
        ea_pk, ea_sk = generate_ea_keypair()
        _write_keypair(ea_path, ea_pk, ea_sk)

    ia_pk, ia_sk = _read_keypair(ia_path)
    ea_pk, ea_sk = _read_keypair(ea_path)
    return AuthorityKeys(
        ia_public_key=ia_pk,
        ia_secret_key=ia_sk,
        ea_public_key=ea_pk,
        ea_secret_key=ea_sk,
    )
