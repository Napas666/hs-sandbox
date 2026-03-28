from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.simulator import run_simulation, simulate_with_replay

router = APIRouter()

class MinionInput(BaseModel):
    id: int
    name: str
    attack: int
    health: int
    mechanics: List[str] = []
    divine_shield: bool = False
    taunt: bool = False
    cleave: bool = False
    poisonous: bool = False
    windfury: bool = False
    reborn: bool = False

class SimulateRequest(BaseModel):
    board_a: List[MinionInput]
    board_b: List[MinionInput]
    iterations: int = 1000

class ReplayRequest(BaseModel):
    board_a: List[MinionInput]
    board_b: List[MinionInput]

@router.post("/battle")
async def simulate_battle(request: SimulateRequest):
    if not request.board_a or not request.board_b:
        return {"error": "Both boards must have at least one minion"}
    if len(request.board_a) > 7 or len(request.board_b) > 7:
        return {"error": "Max 7 minions per board"}
    board_a = [m.dict() for m in request.board_a]
    board_b = [m.dict() for m in request.board_b]
    return run_simulation(board_a, board_b, min(request.iterations, 5000))

@router.post("/replay")
async def simulate_replay(request: ReplayRequest):
    """Return a single battle with full event log for animation."""
    if not request.board_a or not request.board_b:
        return {"error": "Both boards must have at least one minion"}
    board_a = [m.dict() for m in request.board_a]
    board_b = [m.dict() for m in request.board_b]
    events, winner, remaining_hp = simulate_with_replay(board_a, board_b)
    return {"events": events, "winner": winner, "remaining_hp": remaining_hp}
