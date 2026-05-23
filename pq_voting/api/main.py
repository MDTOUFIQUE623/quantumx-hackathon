from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pq_voting.api.deps import get_authority_keys
from pq_voting.api.routes import authorities, board, demo, interop, register, tally, verify, vote
from pq_voting.db.ledger import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_authority_keys()
    yield


app = FastAPI(
    title="PQ Voting",
    description="Post-quantum secure e-voting MVP",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authorities.router, prefix="/api")
app.include_router(register.router, prefix="/api")
app.include_router(interop.router, prefix="/api")
app.include_router(vote.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(board.router, prefix="/api")
app.include_router(tally.router, prefix="/api")
app.include_router(demo.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


static_dir = Path(__file__).resolve().parents[2] / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
