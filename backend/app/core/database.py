import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "/app/data/battlegrounds.db")

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                blizzard_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                attack INTEGER DEFAULT 0,
                health INTEGER DEFAULT 0,
                tier INTEGER DEFAULT 1,
                card_type TEXT DEFAULT 'MINION',
                race TEXT,
                mechanics TEXT,
                image_url TEXT,
                text TEXT
            )
        """)
        await db.commit()
