# Post-Quantum Secure Voting System — Agent Context File
# Paste this at the start of any coding agent session to restore full project context.

## Project overview
Building an MVP e-voting system using post-quantum cryptography for a hackathon.
Domain: Cybersecurity & Digital Identity | SDG 16 — Peace, Justice & Strong Institutions

## Problem being solved
1. Classical e-voting uses RSA/ECDSA — both broken by Shor's algorithm on a quantum computer.
2. No cryptographic binding between voter identity, constituency, and ballot → enables cross-jurisdiction fraud.

## Four system actors

| Actor | Role |
|---|---|
| Identity Authority | Simulates Aadhaar CA. Dilithium keypair. Issues signed voter credentials. |
| Election Authority | Kyber keypair. Public key encrypts all ballots. Secret key decrypts at tally time. |
| Voter | Holds Dilithium signing keypair + verifiable credential issued by IA. |
| Bulletin Board | Append-only public log. Runs 4-step verification before accepting ballots. |

## Cryptographic stack

| Algorithm | NIST name | Role |
|---|---|---|
| CRYSTALS-Kyber 512 | ML-KEM | Key encapsulation — ballot confidentiality |
| CRYSTALS-Dilithium 2 | ML-DSA | Digital signatures — voter auth + credential signing |
| AES-256-GCM | — | Symmetric AEAD — encrypt ballot payload |
| SHA3-256 | — | Biometric commitment hash + chain hash |

Library: liboqs-python (pip install liboqs)
Framework: FastAPI + Uvicorn
Database: SQLite (append-only ballot ledger)
Serialisation: json.dumps(sort_keys=True) for canonical encoding before signing

## Voter credential (verifiable credential — solves cross-state fraud)
```json
{
  "voter_id":        "uuid",
  "biometric_hash":  "SHA3-256(name|dob|aadhaar_number)",
  "constituency_id": "MH-22-Pune",
  "dilithium_pk":    "hex-encoded voter public key",
  "issued_at":       "ISO 8601",
  "expiry":          "ISO 8601",
  "ia_signature":    "Dilithium sig by identity authority over above fields"
}
```
MVP note: biometric_hash = SHA3-256(name + "|" + dob + "|" + aadhaar_number) — no real biometrics.

## Ballot object (on bulletin board)
```json
{
  "ballot_id":         "uuid",
  "voter_id":          "uuid",
  "kem_ciphertext":    "base64",
  "nonce":             "base64",
  "ballot_ciphertext": "base64",
  "signature":         "base64",
  "chain_hash":        "hex",
  "submitted_at":      "ISO 8601"
}
```

## Ballot encryption + signing flow (Phase 3)

Step 1 — KEM encapsulation:
  kem = oqs.KeyEncapsulation("Kyber512")
  kem_ciphertext, shared_secret = kem.encap_secret(authority_pk)

Step 2 — Symmetric encryption:
  aes = AESGCM(shared_secret)
  nonce = os.urandom(12)
  ballot_ciphertext = aes.encrypt(nonce, json.dumps({"candidate_id": X, "election_id": Y}).encode(), None)

Step 3 — Dilithium sign full payload:
  payload = json.dumps({
      "voter_id": ..., "kem_ciphertext": ..., "nonce": ...,
      "ballot_ciphertext": ..., "election_id": ...
  }, sort_keys=True).encode()
  signature = signer.sign(payload, voter_sk)

Step 4 — Bulletin board 4-step check:
  1. Verify ia_signature on voter credential using IA's dilithium_pk
  2. Verify ballot signature using credential's dilithium_pk
  3. Check ballot's constituency_id == credential's constituency_id
  4. Check voter_id not already in ledger for this election

Step 5 — Receipt:
  chain_hash = sha256(prev_hash + payload).hexdigest()
  return {"ballot_id": uid, "chain_hash": chain_hash, "position": idx}

## Credential issuance (Phase 2)
```python
def issue_voter_credential(ia_sk, voter_data, voter_dilithium_pk):
    credential = {
        "voter_id":        voter_data["voter_id"],
        "biometric_hash":  hashlib.sha3_256(
            f"{voter_data['name']}|{voter_data['dob']}|{voter_data['aadhaar']}".encode()
        ).hexdigest(),
        "constituency_id": voter_data["constituency_id"],
        "dilithium_pk":    voter_dilithium_pk.hex(),
        "issued_at":       voter_data["timestamp"],
        "expiry":          voter_data["expiry"],
    }
    payload = json.dumps(credential, sort_keys=True).encode()
    signer = oqs.Signature("Dilithium2")
    credential["ia_signature"] = signer.sign(payload, ia_sk).hex()
    return credential
```

## Threat model

| Threat | Status | Mechanism |
|---|---|---|
| Classical attacker | MITIGATED | Kyber/Dilithium have no known polynomial classical attacks |
| Quantum attacker (Shor) | MITIGATED | ML-KEM and ML-DSA based on lattice problems — no known quantum speedup |
| Cross-jurisdiction fraud | MITIGATED | constituency_id embedded in IA-signed credential, verified by bulletin board |
| Double voting | MITIGATED | voter_id uniqueness enforced per election in append-only ledger |
| Fake ballot injection | MITIGATED | Dilithium sig must verify against IA-signed credential |
| Compromised authority | PARTIAL | MVP: API-level enforcement. Production: threshold crypto (M-of-N trustees) |
| ZK ballot well-formedness | OUT OF SCOPE | Future work — would require ZKP library (e.g. bulletproofs) |

## Hackathon phases remaining

- Phase 2 (~1.5h): Install liboqs, keygen for all 3 actors, credential issuance, voter registration API
- Phase 3 (~2h): Ballot encrypt + sign (code above), canonical serialisation, unit tests
- Phase 4 (~1.5h): FastAPI endpoints — /register, /vote, /verify-receipt; SQLite ledger; 4-step check
- Phase 5 (~1h): /tally endpoint — authority decrypts all ballots, publishes result + anonymised list
- Phase 6 (~1.5h): **Done** — UI flow, judge guide, sample voters, `DEMO_SCRIPT.md`
- Phase 7 (~1h): **Done** — `attacks.html` live attack lab, `pitch.html` + `PITCH.md`, `GET /api/demo/attacks`

## File/module structure (suggested)
```
pq_voting/
  crypto/
    keygen.py        # Key generation for all actors
    credential.py    # VC issuance + verification
    ballot.py        # Encrypt + sign + verify ballot
  api/
    main.py          # FastAPI app
    routes/
      register.py    # POST /register
      vote.py        # POST /vote
      tally.py       # POST /tally (authority only)
      verify.py      # GET /verify/{ballot_id}
  db/
    ledger.py        # SQLite append-only log
  tests/
    test_crypto.py
    test_flow.py
```

## Key invariants (never break these)
1. Always sign over the FULL payload with sort_keys=True — never just the ciphertext
2. The nonce must be stored alongside ballot_ciphertext — it is not secret but is required for decryption
3. Bulletin board never stores or sees the shared_secret — only kem_ciphertext
4. Identity authority secret key and election authority secret key are never in the same process
5. Ledger is append-only — no UPDATE or DELETE operations ever

## Agreed hackathon decisions (2026-05-23)

| Topic | Decision |
|--------|----------|
| Voter crypto | Browser: `@oqs/liboqs-js` + Web Crypto (AES-GCM, SHA3-256) |
| Server crypto | FastAPI + `liboqs-python` — IA credentials, bulletin verify, EA tally |
| UI | Plain HTML/JS, CORS to FastAPI |
| Voter key storage | `sessionStorage` / IndexedDB (demo disclaimer in UI) |
| Test data | Multiple constituencies, elections, demo voters |
| Chain hash | **SHA3-256** everywhere (not SHA-256) |
| Partial upgrade A (public board) | **Done** — `/board.html` + `GET /api/board/{election_id}` hide `voter_id` |
| IA electoral roll (simulated) | **Done** — `check_eligibility` before credential issuance |
| Partial upgrade B (2-of-3 tally keys) | Deferred — optional `PQ_EA_TALLY_KEY` header only |
| Partial upgrade C (post-decrypt check) | **Done** in tally — invalid `candidate_id` rejected after decrypt |
| Out of scope tonight | Full ZK, mix-net, real biometrics, threshold ML-KEM |
| Dev environment | **Docker** for backend on Windows; project on short path outside OneDrive |
| Project path | Moved off OneDrive (e.g. `C:\dev\quantumx-hackathon`) for native liboqs builds |

## Interop note (browser ↔ server)
- Python: `Kyber512`, `Dilithium2`
- JS: matching `@oqs/liboqs-js` factories; run smoke test early
- Ballot fields on wire: base64 for binary blobs; credential `dilithium_pk` and `ia_signature` as hex
