from fastapi import APIRouter, Query, HTTPException
from app.core.database import DB_PATH
import aiosqlite
import json

router = APIRouter()

@router.get("/")
async def get_cards(
    tier: int = Query(None, ge=1, le=6),
    race: str = Query(None),
    mechanic: str = Query(None),
):
    query = "SELECT * FROM cards WHERE 1=1"
    params = []
    if tier:
        query += " AND tier = ?"
        params.append(tier)
    if race:
        query += " AND race LIKE ?"
        params.append(f"%{race}%")
    if mechanic:
        query += " AND mechanics LIKE ?"
        params.append(f"%{mechanic}%")
    query += " ORDER BY tier ASC, name ASC"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        cards = []
        for row in rows:
            card = dict(row)
            try:
                card["mechanics"] = json.loads(card.get("mechanics") or "[]")
            except Exception:
                card["mechanics"] = []
            cards.append(card)
    return {"cards": cards, "total": len(cards)}

@router.post("/sync")
async def sync_cards():
    from app.services.blizzard import sync_cards_to_db
    await sync_cards_to_db()
    return {"message": "Cards synced successfully"}

@router.get("/{card_id}")
async def get_card(card_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Card not found")
        card = dict(row)
        card["mechanics"] = json.loads(card.get("mechanics") or "[]")
    return card
