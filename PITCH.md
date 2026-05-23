# Post-quantum secure e-voting — SDG 16 pitch (2 min)

## Hook (15 s)

Election infrastructure must stay trustworthy for decades. **Shor’s algorithm** will break the RSA and ECDSA that most systems use today — including ballots an adversary **stores now** to decrypt later. We built an MVP that runs **NIST post-quantum** crypto end-to-end: register, vote, verify, public audit, and tally.

## Problem (20 s)

| Threat | Real-world impact |
|--------|-------------------|
| Cross-jurisdiction fraud | Ineligible voters affect the wrong constituency |
| Double voting | One person, multiple ballots |
| Forged ballots | Tampering on the network |
| Harvest-now-decrypt-later | Nation-state stores ciphertexts until a CRQC exists |

## SDG 16 — Peace, justice & strong institutions (25 s)

- **16.6** — Accountable institutions: IA electoral roll, signed credentials, append-only ledger  
- **16.7** — Inclusive participation: browser voting + verifiable `ballot_id` receipt  
- **16.10** — Transparency: public bulletin board and published tally **without** exposing `voter_id`

## Solution (30 s)

1. **Identity Authority** — checks simulated electoral roll; issues **Dilithium-signed** credential binding constituency  
2. **Voter browser** — **Kyber-encrypts** ballot; signs with voter **ML-DSA** key  
3. **Bulletin board** — verifies signatures + chain hash; public view omits voter identity  
4. **Election Authority** — decrypts and counts; publishes anonymized results  

**Algorithms:** Kyber512 (ML-KEM) + Dilithium2 (ML-DSA-44) + SHA3-256 chain.

## Live demo (20 s)

Open **http://localhost:8000/demo.html** → vote flow → **attacks.html** (403/409/400 blocks) → **pitch.html**.

## Differentiator (15 s)

Not a slide-deck crypto story — **liboqs in the browser and on the server**, interop-tested, with reproducible attack demos against the real API.

## Roadmap (15 s)

Mix-nets, threshold EA keys, ZK well-formedness, real UIDAI/roll integration. Tonight’s MVP proves the **PQ trust chain** is implementable now.

## Close (10 s)

**Strong institutions need cryptography that survives the quantum era.** This project is a working blueprint for SDG-aligned, verifiable, post-quantum elections.
