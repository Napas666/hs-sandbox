#!/usr/bin/env python3
"""
fetch_cards.py — парсер карт Hearthstone Battlegrounds

СПОСОБ 1 (рекомендуется): Playwright — полноценный браузер, загружает JS
  pip install playwright
  playwright install chromium
  python scripts/fetch_cards.py --mode playwright

СПОСОБ 2: Requests + BeautifulSoup (если bgcheatsheet актуальный)
  pip install requests beautifulsoup4 lxml
  python scripts/fetch_cards.py --mode requests

СПОСОБ 3: Ручной экспорт из браузера
  1. Открой https://hearthstone.blizzard.com/en-us/battlegrounds?bgGameMode=solos&minionType=all
  2. Открой DevTools → Network → найди XHR запрос к /api/... с данными карт
  3. Скопируй ответ в scripts/blizzard_export.json
  4. python scripts/fetch_cards.py --mode json --input scripts/blizzard_export.json

Результат сохраняется в: backend/app/services/cards_scraped.json
"""

import argparse
import json
import os
import re
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("fetch_cards")

SCRIPT_DIR  = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent
OUTPUT_PATH = REPO_ROOT / "backend" / "app" / "services" / "cards_scraped.json"
MANUAL_PATH = SCRIPT_DIR / "cards_manual.json"

BLIZZARD_URL = "https://hearthstone.blizzard.com/en-us/battlegrounds?bgGameMode=solos&minionType=all"
BGCHEATSHEET = "https://bgcheatsheet.com/"

TRIBE_PARAMS = ["Beast","Demons","Dragons","Elementals","Mech","Murlocs","Naga","Pirates","Quilboar","Undead"]
TRIBE_TO_RACE = {
    "Beast":"Beast","Demons":"Demon","Dragons":"Dragon","Elementals":"Elemental",
    "Mech":"Mech","Murlocs":"Murloc","Naga":"Naga","Pirates":"Pirate",
    "Quilboar":"Quilboar","Undead":"Undead",
}

MECHANIC_PATTERNS = {
    "divine_shield": [r"\bdivine shield\b"],
    "taunt":         [r"\btaunt\b"],
    "cleave":        [r"\bcleave\b", r"also damages the minions next to"],
    "poisonous":     [r"\bpoisonous\b", r"\bvenomous\b"],
    "windfury":      [r"\bwindfury\b", r"\bmega-windfury\b"],
    "reborn":        [r"\breborn\b"],
    "magnetic":      [r"\bmagnetic\b"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


# ── СПОСОБ 1: Playwright (полноценный браузер) ────────────────────────────────

def fetch_playwright() -> list[dict]:
    """
    Использует Playwright для загрузки JS-страницы Blizzard.
    Перехватывает XHR-запросы к их внутреннему API.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("Playwright не установлен. Запусти: pip install playwright && playwright install chromium")
        return []

    log.info(f"Запускаю Playwright, открываю {BLIZZARD_URL}")
    cards = []
    api_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Перехватываем все XHR ответы
        def handle_response(response):
            url = response.url
            if "api" in url.lower() and response.status == 200:
                ct = response.headers.get("content-type", "")
                if "json" in ct:
                    try:
                        data = response.json()
                        api_responses.append({"url": url, "data": data})
                        log.info(f"  Перехвачен API: {url}")
                    except Exception:
                        pass

        page.on("response", handle_response)

        page.goto(BLIZZARD_URL, wait_until="networkidle", timeout=30000)

        # Прокручиваем страницу чтобы загрузить все карты
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)

        # Пробуем найти карты в DOM
        log.info("Ищу карточки в DOM...")
        card_elements = page.query_selector_all("[class*='card'], [class*='Card'], [data-card]")
        log.info(f"  Найдено элементов с 'card': {len(card_elements)}")

        # Сохраняем HTML для анализа
        html = page.content()
        html_path = SCRIPT_DIR / "blizzard_page.html"
        html_path.write_text(html, encoding="utf-8")
        log.info(f"  HTML сохранён в {html_path}")

        browser.close()

    # Анализируем перехваченные API ответы
    log.info(f"Перехваченных API-ответов: {len(api_responses)}")
    for resp in api_responses:
        log.info(f"  {resp['url']}")
        # Сохраняем для ручного анализа
        resp_path = SCRIPT_DIR / f"api_response_{len(api_responses)}.json"
        with open(resp_path, "w", encoding="utf-8") as f:
            json.dump(resp, f, ensure_ascii=False, indent=2)

    # Парсим HTML в поисках данных карт
    cards = _parse_blizzard_html(html)
    return cards


def _parse_blizzard_html(html: str) -> list[dict]:
    """Ищет данные карт в HTML/JS страницы Blizzard."""
    cards = []

    # Blizzard часто встраивает данные как JSON в <script> тег
    # Ищем паттерны типа window.__INITIAL_STATE__ = {...}
    patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*({.+?});\s*</script>',
        r'window\.pageData\s*=\s*({.+?});\s*</script>',
        r'"cards"\s*:\s*(\[.+?\])',
        r'"minions"\s*:\s*(\[.+?\])',
    ]

    for pat in patterns:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                log.info(f"Найдены данные по паттерну: {pat[:40]}")
                extracted = _extract_cards_from_json(data)
                if extracted:
                    cards.extend(extracted)
            except Exception as e:
                log.debug(f"Ошибка парсинга {pat[:40]}: {e}")

    return cards


def _extract_cards_from_json(data) -> list[dict]:
    """Рекурсивно ищет карты в произвольном JSON."""
    cards = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and ("attack" in item or "health" in item or "name" in item):
                card = _normalize_blizzard_card(item)
                if card:
                    cards.append(card)
            else:
                cards.extend(_extract_cards_from_json(item))
    elif isinstance(data, dict):
        for v in data.values():
            cards.extend(_extract_cards_from_json(v))
    return cards


def _normalize_blizzard_card(raw: dict) -> dict | None:
    """Нормализует карту из Blizzard API в наш формат."""
    name = raw.get("name") or raw.get("cardName", "")
    if not name:
        return None
    return {
        "name":      name if isinstance(name, str) else name.get("en_US", str(name)),
        "attack":    int(raw.get("attack", 0) or 0),
        "health":    int(raw.get("health", 1) or 1),
        "tier":      int(raw.get("tier", 1) or raw.get("techLevel", 1) or 1),
        "race":      _normalize_race(raw.get("minionType") or raw.get("race", "Neutral")),
        "text":      _clean_text(raw.get("text") or raw.get("cardText", "")),
        "image_url": raw.get("image") or raw.get("cropImage") or "",
    }


def _normalize_race(race) -> str:
    if isinstance(race, dict):
        race = race.get("en_US", "Neutral")
    mapping = {
        "BEAST":"Beast","DEMON":"Demon","DRAGON":"Dragon","ELEMENTAL":"Elemental",
        "MECH":"Mech","MURLOC":"Murloc","NAGA":"Naga","PIRATE":"Pirate",
        "QUILBOAR":"Quilboar","UNDEAD":"Undead","NEUTRAL":"Neutral","ALL":"All",
    }
    return mapping.get(str(race).upper(), str(race).title() if race else "Neutral")


# ── СПОСОБ 2: Requests + bgcheatsheet ────────────────────────────────────────

def fetch_requests() -> list[dict]:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        log.error("Установи: pip install requests beautifulsoup4 lxml")
        return []

    session = requests.Session()
    session.headers.update(HEADERS)
    seen: set[str] = set()
    all_cards = []

    for tribe in TRIBE_PARAMS:
        url = f"{BGCHEATSHEET}?type={tribe}"
        log.info(f"  GET {url}")
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            log.warning(f"  Ошибка {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        race = TRIBE_TO_RACE.get(tribe, tribe)
        count = 0
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "").strip()
            if not re.match(r"^/images/cards/\d+-", src) or not alt:
                continue
            if alt in seen:
                continue
            seen.add(alt)
            all_cards.append({"name": alt, "image_url": f"https://bgcheatsheet.com{src}", "race": race})
            count += 1
        log.info(f"  → {count} карт для {tribe}")
        time.sleep(0.5)

    log.info(f"Итого с bgcheatsheet: {len(all_cards)}")
    return all_cards


# ── СПОСОБ 3: Ручной JSON ─────────────────────────────────────────────────────

def fetch_from_json(path: str) -> list[dict]:
    """Парсит JSON-файл экспортированный вручную из DevTools."""
    p = Path(path)
    if not p.exists():
        log.error(f"Файл не найден: {path}")
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    cards = _extract_cards_from_json(data)
    log.info(f"Извлечено карт из {path}: {len(cards)}")
    return cards


# ── Обогащение из HearthstoneJSON ─────────────────────────────────────────────

def fetch_hsjson() -> dict | None:
    try:
        import requests
        url = "https://api.hearthstonejson.com/v1/latest/enUS/cards.json"
        log.info(f"Загружаю HearthstoneJSON...")
        r = requests.get(url, timeout=30, headers=HEADERS)
        r.raise_for_status()
        raw = r.json()
        index = {}
        for card in raw:
            name = card.get("name", "")
            if not name:
                continue
            key = name.strip().lower()
            is_bg = card.get("set", "") in ("BATTLEGROUNDS",) or card.get("id","").startswith("TB_Bacon")
            if key not in index or is_bg:
                index[key] = card
        log.info(f"HearthstoneJSON: {len(index)} карт")
        return index
    except Exception as e:
        log.warning(f"HearthstoneJSON недоступен: {e}")
        return None


def enrich(card: dict, hsjson: dict) -> dict:
    key = card["name"].strip().lower()
    hs  = hsjson.get(key) or hsjson.get(re.sub(r"[^a-z0-9 ]","",key))
    if hs:
        card["attack"]  = hs.get("attack", card.get("attack", 0))
        card["health"]  = hs.get("health", card.get("health", 1))
        card["text"]    = _clean_text(hs.get("text", card.get("text","")))
        card["dbf_id"]  = hs.get("dbfId")
        tier = hs.get("battlegroundsTierTier") or hs.get("techLevel") or card.get("tier",1)
        card["tier"] = int(tier) if tier else 1
        card["mechanics"] = _mechanics_from_text(card.get("text",""))
        if card.get("dbf_id"):
            card["image_url"] = f"https://art.hearthstonejson.com/v1/256x/{card['dbf_id']}.jpg"
    return card


def _mechanics_from_text(text: str) -> list[str]:
    t = text.lower()
    return [m for m, pats in MECHANIC_PATTERNS.items() if any(re.search(p, t) for p in pats)]


def _clean_text(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


# ── Ручные правки ─────────────────────────────────────────────────────────────

def load_overrides() -> dict:
    if not MANUAL_PATH.exists():
        return {}
    with open(MANUAL_PATH, encoding="utf-8") as f:
        return {k:v for k,v in json.load(f).items() if not k.startswith("_")}


def apply_overrides(cards: list[dict], overrides: dict) -> list[dict]:
    for card in cards:
        patch = overrides.get(card["name"])
        if patch:
            card.update(patch)
    return cards


# ── Финализация ───────────────────────────────────────────────────────────────

def finalize(cards: list[dict]) -> list[dict]:
    result = []
    for i, card in enumerate(cards, 1):
        mech = card.get("mechanics") or _mechanics_from_text(card.get("text",""))
        result.append({
            "id":        i,
            "name":      card.get("name",""),
            "tier":      int(card.get("tier") or 1),
            "race":      card.get("race","Neutral"),
            "attack":    int(card.get("attack") or 0),
            "health":    int(card.get("health") or 1),
            "mechanics": mech,
            "text":      card.get("text",""),
            "image_url": card.get("image_url",""),
            "dbf_id":    card.get("dbf_id"),
        })
    return result


def report(cards: list[dict]):
    by_tier  = {}
    by_race  = {}
    no_stats = []
    for c in cards:
        by_tier[c["tier"]] = by_tier.get(c["tier"],0)+1
        by_race[c["race"]] = by_race.get(c["race"],0)+1
        if c["attack"]==0 and c["health"]==1:
            no_stats.append(c["name"])
    print(f"\n✅ Карт: {len(cards)}")
    print("По тирам: " + " | ".join(f"T{t}:{v}" for t,v in sorted(by_tier.items())))
    print("По фракциям: " + " | ".join(f"{r}:{v}" for r,v in sorted(by_race.items())))
    if no_stats:
        print(f"⚠️  Без статов ({len(no_stats)}): {', '.join(no_stats[:8])}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch HS Battlegrounds cards")
    parser.add_argument("--mode", choices=["playwright","requests","json"], default="playwright",
                        help="playwright=JS browser | requests=bgcheatsheet | json=manual export")
    parser.add_argument("--input", help="Path to JSON file (for --mode json)")
    parser.add_argument("--out", default=str(OUTPUT_PATH), help="Output path")
    args = parser.parse_args()

    print("=" * 58)
    print(f"  HS BG card fetcher — mode: {args.mode}")
    print(f"  Output: {args.out}")
    print("=" * 58)

    # 1. Получаем карты
    if args.mode == "playwright":
        cards = fetch_playwright()
    elif args.mode == "requests":
        cards = fetch_requests()
    elif args.mode == "json":
        if not args.input:
            log.error("Укажи --input path/to/file.json")
            sys.exit(1)
        cards = fetch_from_json(args.input)
    else:
        cards = []

    if not cards:
        log.warning("Нет карт из основного источника, использую только ручные правки...")

    # 2. Обогащаем из HearthstoneJSON
    hsjson = fetch_hsjson()
    if hsjson:
        cards = [enrich(c, hsjson) for c in cards]

    # 3. Применяем ручные правки
    overrides = load_overrides()
    log.info(f"Ручных правок: {len(overrides)}")

    # Если вообще нет карт — строим из ручных правок
    if not cards and overrides:
        log.info("Строю датасет из cards_manual.json...")
        for name, data in overrides.items():
            if name.startswith("_"):
                continue
            card = {"name": name, **data}
            if not card.get("image_url"):
                # Генерируем slug для bgcheatsheet
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                # Попытаемся найти ID в manual данных
                dbf = data.get("dbf_id")
                if dbf:
                    card["image_url"] = f"https://art.hearthstonejson.com/v1/256x/{dbf}.jpg"
                else:
                    card["image_url"] = ""
            cards.append(card)
    elif overrides:
        cards = apply_overrides(cards, overrides)

    if not cards:
        log.error("Нет данных. Проверь соединение или запусти с другим --mode")
        sys.exit(1)

    # 4. Финализируем
    cards = finalize(cards)
    report(cards)

    # 5. Сохраняем
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print(f"\n📁 Сохранено → {out}")
    print("\nСледующий шаг:")
    print("  Раскомментируй volume в docker-compose.yml и запусти:")
    print("  docker compose down && docker compose up --build")


if __name__ == "__main__":
    main()
