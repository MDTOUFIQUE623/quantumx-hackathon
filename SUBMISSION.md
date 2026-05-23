# Hackathon submission checklist

## Required items

| Requirement | Status | Location |
|-------------|--------|----------|
| **Presentation deck** | ✅ Ready | [`static/deck.html`](static/deck.html) (web, print to PDF) · [`presentation/SLIDES.md`](presentation/SLIDES.md) (PowerPoint source) · [`static/pitch.html`](static/pitch.html) |
| **README** | ✅ Ready | [`README.md`](README.md) |
| **Demo codebase (GitHub)** | ⏳ Pending upload | Initialize git + push (see below) |

## Verified working (local)

| Check | Result |
|-------|--------|
| `docker compose up --build` | API on port 8000 |
| `GET /api/health` | `{"status":"ok"}` |
| `GET /api/demo/attacks` | 200 (restart API if 404 after pull) |
| `pytest tests/` | **33 passed** |
| Judge guide | http://localhost:8000/demo.html |
| Vote flow | http://localhost:8000/ |
| Attack lab | http://localhost:8000/attacks.html |
| Presentation deck | http://localhost:8000/deck.html → Ctrl+P → PDF |

## Before pushing to GitHub

1. **Commit vendored browser crypto** — `static/vendor/liboqs-js/` must be in the repo (see README). Judges need this to vote in the browser after clone.

2. **Do not commit secrets** — `data/` is gitignored (SQLite DB, generated keys).

3. **Optional:** Add team name and GitHub URL at the top of `README.md`.

## Upload to GitHub (first time)

```powershell
cd c:\Users\Lenovo\Downloads\quantumx-hackathon
git init
git add .
git status
git commit -m "Post-quantum secure e-voting MVP for hackathon submission"
```

Create a new repository on GitHub (empty, no README), then:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/quantumx-hackathon.git
git push -u origin main
```

## Submit to judges

- **Repo URL:** `https://github.com/YOUR_USERNAME/quantumx-hackathon`
- **Deck PDF:** export from http://localhost:8000/deck.html (Print → Save as PDF)
- **Quick start:** point judges to README → `docker compose up --build` → demo.html
