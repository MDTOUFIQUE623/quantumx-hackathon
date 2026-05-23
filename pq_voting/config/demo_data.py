from pq_voting.config.attack_lab import ATTACK_ROLL_ENTRIES

CONSTITUENCIES = [
    {"id": "MH-22-Pune", "name": "Pune (Maharashtra)"},
    {"id": "DL-07-Delhi", "name": "New Delhi"},
    {"id": "KA-12-Bangalore", "name": "Bangalore Urban"},
]

ELECTIONS = [
    {
        "election_id": "election-2026-local",
        "title": "2026 Local Council",
        "candidates": [
            {"candidate_id": "c1", "name": "Alice Sharma"},
            {"candidate_id": "c2", "name": "Ravi Patel"},
            {"candidate_id": "c3", "name": "Meera Iyer"},
        ],
    },
    {
        "election_id": "election-2026-state",
        "title": "2026 State Assembly",
        "candidates": [
            {"candidate_id": "s1", "name": "Party Alpha"},
            {"candidate_id": "s2", "name": "Party Beta"},
        ],
    },
]

# Simulated government electoral roll — IA checks this before signing a credential.
# Production: replace with official electoral-roll / Aadhaar-linked database.
ELECTORAL_ROLL = [
    {
        "name": "Ananya Desai",
        "dob": "1998-04-12",
        "aadhaar": "900011112222",
        "constituency_id": "MH-22-Pune",
        "eligible": True,
    },
    {
        "name": "Kabir Singh",
        "dob": "1995-09-03",
        "aadhaar": "900033334444",
        "constituency_id": "DL-07-Delhi",
        "eligible": True,
    },
    {
        "name": "Priya Nair",
        "dob": "2000-01-28",
        "aadhaar": "900055556666",
        "constituency_id": "KA-12-Bangalore",
        "eligible": True,
    },
    # Harness / test voters (same roll rules apply in pytest)
    {
        "name": "Flow Voter",
        "dob": "1993-07-20",
        "aadhaar": "700011112333",
        "constituency_id": "KA-12-Bangalore",
        "eligible": True,
    },
    {
        "name": "API Tester",
        "dob": "1992-06-15",
        "aadhaar": "800012341234",
        "constituency_id": "DL-07-Delhi",
        "eligible": True,
    },
    {
        "name": "Phase3 Voter",
        "dob": "1995-03-10",
        "aadhaar": "999911112222",
        "constituency_id": "MH-22-Pune",
        "eligible": True,
    },
    {
        "name": "Board Viewer",
        "dob": "1994-02-02",
        "aadhaar": "600011112222",
        "constituency_id": "MH-22-Pune",
        "eligible": True,
    },
    {
        "name": "Tally A",
        "dob": "1990-05-05",
        "aadhaar": "810011112222",
        "constituency_id": "MH-22-Pune",
        "eligible": True,
    },
    {
        "name": "Tally B",
        "dob": "1990-05-05",
        "aadhaar": "810022223333",
        "constituency_id": "DL-07-Delhi",
        "eligible": True,
    },
    {
        "name": "Tally C",
        "dob": "1990-05-05",
        "aadhaar": "810033334444",
        "constituency_id": "KA-12-Bangalore",
        "eligible": True,
    },
    {
        "name": "Wrong Constituency",
        "dob": "1991-01-01",
        "aadhaar": "700022223333",
        "constituency_id": "DL-07-Delhi",
        "eligible": True,
    },
    {
        "name": "Test User",
        "dob": "1990-01-01",
        "aadhaar": "123456789012",
        "constituency_id": "MH-22-Pune",
        "eligible": True,
    },
    *ATTACK_ROLL_ENTRIES,
]

# Pre-filled registration forms for the demo UI (keys are generated in-browser).
DEMO_VOTERS = [
    {
        "label": "Demo voter — Pune",
        "name": "Ananya Desai",
        "dob": "1998-04-12",
        "aadhaar": "900011112222",
        "constituency_id": "MH-22-Pune",
    },
    {
        "label": "Demo voter — Delhi",
        "name": "Kabir Singh",
        "dob": "1995-09-03",
        "aadhaar": "900033334444",
        "constituency_id": "DL-07-Delhi",
    },
    {
        "label": "Demo voter — Bangalore",
        "name": "Priya Nair",
        "dob": "2000-01-28",
        "aadhaar": "900055556666",
        "constituency_id": "KA-12-Bangalore",
    },
]
