# QuantumX — Post-Quantum Secure E-Voting
## Presentation deck (copy into PowerPoint / Google Slides)

> **Also available as web deck:** open `http://localhost:8000/deck.html` after starting Docker, then **Print → Save as PDF** for submission.

---

### Slide 1 — Title
**Post-quantum secure e-voting**  
Trustworthy digital elections · SDG 16  
- Register → vote → verify → audit → tally  
- Live attack lab · Kyber + Dilithium  

---

### Slide 2 — Problem
- Fake voters & wrong constituency  
- Double voting & ballot tampering  
- Harvest now, decrypt later (quantum)  

*Example: Archives of RSA-encrypted ballots at risk when quantum computers mature.*

---

### Slide 3 — SDG 16
| Target | MVP |
|--------|-----|
| 16.6 Institutions | Roll check + public board + tally |
| 16.7 Participation | Browser vote + receipt |
| 16.10 Transparency | Audit without deanonymizing |

---

### Slide 4 — Architecture
1. **Identity Authority** — voter list, signed pass  
2. **Voter browser** — sealed ballot  
3. **Bulletin board** — public record, no names  
4. **Election Authority** — decrypt & count  

---

### Slide 5 — Post-quantum crypto
| | Classical | Ours |
|---|-----------|------|
| Encrypt | RSA | Kyber512 |
| Sign | ECDSA | Dilithium2 |
| Quantum | Broken (Shor) | Lattice-safe |

---

### Slide 6 — Live demo (5 min)
1. Interop smoke test  
2. Register Ananya (Pune) + vote  
3. Verify receipt  
4. Bulletin board + tally  
5. Attack lab (403/409)  

---

### Slide 7 — Attacks blocked
- Not on roll  
- Cross-constituency  
- Double vote  
- Forged signature  

---

### Slide 8 — Tech stack
- Browser: liboqs-js, Web Crypto  
- Server: FastAPI, liboqs-python  
- Docker · 33 pytest tests  

---

### Slide 9 — Limits & roadmap
- Demo keys in browser (not HSM)  
- Simulated roll (not UIDAI)  
- Future: mix-net, threshold EA, ZK  

---

### Slide 10 — Close
**Strong institutions need quantum-safe elections.**  
`docker compose up --build` → http://localhost:8000/demo.html  

GitHub · README · DEMO_SCRIPT.md
