from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import cards, simulate
from app.core.database import init_db

app = FastAPI(
    title="HS Battlegrounds Sandbox API",
    description="Backend for Hearthstone Battlegrounds combat simulator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(simulate.router, prefix="/api/simulate", tags=["simulate"])

@app.get("/api/health")
async def health():
    return {"status": "ok"}
