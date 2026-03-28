"""
Загрузка карт в БД.

Порядок приоритетов:
1. /app/data/cards_scraped.json  — свежий дамп с bgcheatsheet (после запуска fetch_cards.py)
2. cards_data.py                 — статичный датасет (fallback)
"""

import json
import os
import logging
from pathlib import Path

import aiosqlite

from app.core.database import DB_PATH

log = logging.getLogger(__name__)

# Пути где ищем cards_scraped.json
SCRAPED_JSON_PATHS = [
    Path("/app/data/cards_scraped.json"),          # Docker runtime (volume)
    Path("/app/cards_scraped.json"),               # Docker build-time COPY
    Path(__file__).parent / "cards_scraped.json",  # рядом с blizzard.py
    Path(__file__).parent.parent.parent.parent     # локальный запуск из корня репо
    / "scripts" / "cards_scraped.json",
]


def _load_scraped_json() -> list | None:
    for path in SCRAPED_JSON_PATHS:
        if path.exists():
            log.info(f"Найден cards_scraped.json: {path}")
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    log.info(f"Загружено {len(data)} карт из {path}")
                    return data
            except Exception as e:
                log.warning(f"Ошибка чтения {path}: {e}")
    return None


def _load_static_data() -> list:
    from app.services.cards_data import ALL_CARDS
    log.info(f"cards_scraped.json не найден, использую cards_data.py ({len(ALL_CARDS)} карт)")
    return ALL_CARDS


def _get_mechanics(card: dict) -> list:
    m = card.get("mechanics") or []
    if isinstance(m, str):
        try:
            m = json.loads(m)
        except Exception:
            m = []
    return m


async def sync_cards_to_db() -> int:
    cards = _load_scraped_json() or _load_static_data()

    inserted = 0
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cards")
        await db.commit()

        for card in cards:
            mechanics = _get_mechanics(card)

            # Пропускаем заклинания/токены с нулевыми статами
            atk = int(card.get("attack") or 0)
            hp  = int(card.get("health") or 0)
            text = card.get("text", "")
            if atk == 0 and hp == 0:
                if not text or "[Spell]" in text or "[Token]" in text:
                    continue

            try:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO cards
                        (id, name, attack, health, tier, race, mechanics, image_url, text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        card.get("id"),
                        card.get("name", ""),
                        atk,
                        max(hp, 1),
                        int(card.get("tier") or 1),
                        card.get("race", "Neutral"),
                        json.dumps(mechanics),
                        card.get("image_url", ""),
                        text,
                    ),
                )
                inserted += 1
            except Exception as e:
                log.warning(f"Пропускаю '{card.get('name')}': {e}")

        await db.commit()

    log.info(f"Загружено в БД: {inserted} карт")
    return inserted
