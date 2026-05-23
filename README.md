# Post-Quantum Secure Voting (Hackathon MVP)

**QuantumX** — E-voting prototype using **Kyber512** (ballot secrecy) and **Dilithium2 / ML-DSA-44** (signatures), with Identity Authority–signed voter credentials, electoral-roll checks, public bulletin board, and EA tally.

> **SDG 16:** Peace, justice & strong institutions — transparent, verifiable elections with quantum-safe cryptography.

## Submission package

| Item | File / URL |
|------|------------|
| **Presentation deck** | [static/deck.html](static/deck.html) — open in browser, **Print → Save as PDF** · [presentation/SLIDES.md](presentation/SLIDES.md) for PowerPoint |
| **README** | This file |
| **Demo** | Run via Docker below · Full checklist: [SUBMISSION.md](SUBMISSION.md) |

## Quick start (Docker — recommended)

**Requirements:** Docker Desktop running.

```bash
git clone https://github.com/MDTOUFIQUE623/quantumx-hackathon
cd quantumx-hackathon
docker compose up --build
```

After first start, if attack lab shows API errors: `docker compose restart api`

| Page | URL |
|------|-----|
| **Judge demo guide** (start here) | http://localhost:8000/demo.html |
| Register & vote | http://localhost:8000/ |
| **Presentation deck** | http://localhost:8000/deck.html |
| Attack lab | http://localhost:8000/attacks.html |
| SDG 16 pitch | http://localhost:8000/pitch.html |
| Public bulletin board | http://localhost:8000/board.html |
| EA tally | http://localhost:8000/tally.html |
| Interop smoke test | http://localhost:8000/interop.html |
| API docs | http://localhost:8000/docs |

Hard-refresh static pages after updates: `Ctrl+Shift+R`

**Presenter scripts:** [DEMO_SCRIPT.md](DEMO_SCRIPT.md) · [PITCH.md](PITCH.md)

### Sample eligible voters (for judges)

| Name | DOB | Aadhaar-like ID | Constituency |
|------|-----|-----------------|--------------|
| Ananya Desai | 1998-04-12 | 900011112222 | MH-22-Pune |
| Kabir Singh | 1995-09-03 | 900033334444 | DL-07-Delhi |
| Priya Nair | 2000-01-28 | 900055556666 | KA-12-Bangalore |

On the vote page, click **Use** on a row or use quick-fill, then **Register**.

## Architecture

| Layer | Responsibility |
|--------|----------------|
| **Browser** (`liboqs-js` + Web Crypto + `js-sha3`) | Voter keygen, ballot encrypt/sign (Kyber + Dilithium) |
| **Server** (FastAPI + `liboqs-python`) | IA credentials, bulletin verify, EA tally |
| **Database** | SQLite append-only ledger |

## Run tests

```bash
docker compose run --rm -v ./pq_voting:/app/pq_voting -v ./tests:/app/tests -e PYTHONPATH=/app api pytest tests/ -v
```

Expected: **33 passed**

## Browser dependency (vendored)

`static/vendor/liboqs-js/` is included in the repo so judges can vote after `git clone` without extra npm steps. To refresh:

```powershell
cd static/vendor
npm install @oqs/liboqs-js@0.15.1
Remove-Item -Recurse -Force liboqs-js -ErrorAction SilentlyContinue
Copy-Item -Recurse node_modules/@oqs/liboqs-js liboqs-js
```

See [static/vendor/README.md](static/vendor/README.md).

## Local Python (optional)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PQ_VOTING_DATA_DIR=data
uvicorn pq_voting.api.main:app --reload
```

Requires native [liboqs](https://github.com/open-quantum-safe/liboqs) build on Windows — **Docker is easier**.

## Project structure

```
pq_voting/          # Python backend (crypto, API, DB, IA roll)
static/             # UI (HTML, CSS, JS, deck.html, vendor)
tests/              # pytest (33 tests)
presentation/       # SLIDES.md for PowerPoint
DEMO_SCRIPT.md      # 5–7 min judge walkthrough
PITCH.md            # 2 min narrative
SUBMISSION.md       # Hackathon checklist
docker-compose.yml
Dockerfile
```

## Features completed

- [x] Post-quantum register / vote / verify / board / tally
- [x] Simulated electoral roll (IA eligibility check)
- [x] Public board without `voter_id` on public API
- [x] Attack lab (live API fraud demos)
- [x] Judge UI + plain-English explanations
- [x] Presentation deck (`deck.html` + `SLIDES.md`)

## Team

<!-- TODO: Add team name, members, institution -->

## License

Hackathon MVP — demo only, not for production elections.
