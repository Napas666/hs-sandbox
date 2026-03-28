import asyncio
import sys
import os
sys.path.insert(0, "/app")

from app.core.database import init_db, DB_PATH
from app.services.blizzard import sync_cards_to_db
import aiosqlite

async def main():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        row = await cursor.fetchone()
        count = row[0]

    if count == 0:
        print("DB empty, loading cards...")
        await sync_cards_to_db()
    else:
        print(f"DB already has {count} cards")

if __name__ == "__main__":
    asyncio.run(main())
