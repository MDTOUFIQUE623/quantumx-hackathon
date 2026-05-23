# PQ Voting — 5-minute judge demo script

## Before you start

```bash
docker compose up --build
```

Open **http://localhost:8000/demo.html** (judge guide + sample voters table).

Hard-refresh (`Ctrl+Shift+R`) if you changed static files.

---

## 0:30 — Interop (optional warm-up)

1. Open http://localhost:8000/interop.html
2. Click **Run smoke test** → all checks green (browser ML-DSA-44 / Kyber512 ↔ server Dilithium2 / Kyber512).

**Say:** “PQ crypto runs in the voter’s browser and matches the server stack — not legacy RSA.”

---

## 1:30 — Register + vote

1. Open http://localhost:8000/
2. In **Sample eligible voters**, click **Use** on **Ananya Desai** (Pune), or use Quick-fill.
3. Click **Register** → IA-signed credential (electoral roll check passed).
4. Choose **2026 Local Council**, pick a candidate, **Cast encrypted ballot**.
5. Copy `ballot_id` from the receipt.

**Say:** “Identity Authority only signs if name, DOB, Aadhaar-like ID, and constituency match the roll. Ballot is Kyber-encrypted; voter signs with Dilithium.”

---

## 0:30 — Verify receipt

1. Paste `ballot_id` → **Verify on bulletin board**.
2. Show `verified: true`, chain hash, no `voter_id` in response.

---

## 0:45 — Public bulletin board

1. Open http://localhost:8000/board.html (or **Open board for this election**).
2. Point out: encrypted fields + signatures + `chain_hash`; **no voter_id** on the public view.

**Say:** “Anyone can audit that ballots were posted; production would add a mix-net to unlink voters entirely.”

---

## 1:00 — EA tally

1. Open http://localhost:8000/tally.html
2. Select the same election → **Run tally (POST)**.
3. Show candidate counts and “valid / rejected” summary.

**Say:** “Only the Election Authority decrypts with its secret key; published results are anonymized.”

---

## 0:45 — Rejection demos (pick one)

| Try | Expected |
|-----|----------|
| Register Ananya’s Aadhaar but select **Delhi** constituency | **403** — roll mismatch |
| Aadhaar `000000000000` | **403** — not on roll |
| Vote again in the same election | **409** — double vote |

---

## 1:00 — Attack lab (Phase 7)

1. Open http://localhost:8000/attacks.html
2. Click **Run** on **Register without electoral roll** → **403**
3. Click **Run** on **Double vote** → first vote OK, second **409**
4. Click **Explain** on **Harvest now, decrypt later** — PQ vs classical narrative

**Say:** “Every attack hits the real API. Fraud paths are blocked by the roll, credentials, signatures, and ledger — not by UI hiding.”

If an attack says “reset data”, delete `data/pq_voting.db` and restart the API.

---

## 0:45 — SDG 16 pitch (optional)

Open http://localhost:8000/pitch.html or read [PITCH.md](PITCH.md) for the 2-minute narrative.

---

## Closing (SDG 16 + quantum)

- **SDG 16:** Transparent, verifiable elections — public board + receipts + published tally.
- **Quantum:** Shor breaks RSA/ECDSA; lattice KEM/signatures (NIST ML-KEM / ML-DSA) are the migration path for long-lived election infrastructure.

---

## Sample eligible voters (copy-paste)

| Label | Name | DOB | Aadhaar-like ID | Constituency |
|-------|------|-----|-----------------|--------------|
| Pune | Ananya Desai | 1998-04-12 | 900011112222 | MH-22-Pune |
| Delhi | Kabir Singh | 1995-09-03 | 900033334444 | DL-07-Delhi |
| Bangalore | Priya Nair | 2000-01-28 | 900055556666 | KA-12-Bangalore |

API: `GET /api/electoral-roll/samples` and `GET /api/demo/config`.
