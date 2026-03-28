# Как получить актуальные карты из игры

## Самый надёжный способ: DevTools из браузера

Сайт Blizzard загружает карты через JavaScript — обычный парсер не работает.
Но можно перехватить запрос прямо в браузере.

### Шаг 1: Открой страницу карт

```
https://hearthstone.blizzard.com/en-us/battlegrounds?bgGameMode=solos&minionType=all
```

### Шаг 2: Открой DevTools → Network

- Chrome/Edge: F12 → вкладка **Network**
- Фильтр: **Fetch/XHR**

### Шаг 3: Обнови страницу (F5)

В Network появятся запросы. Ищи запрос похожий на:
- `cards?gameMode=battlegrounds`
- `battlegrounds/cards`
- `/api/...` с JSON-ответом содержащим `attack`, `health`, `name`

### Шаг 4: Скопируй ответ

Правый клик на запросе → **Copy Response** → вставь в файл:
```
scripts/blizzard_export.json
```

### Шаг 5: Запусти парсер

```bash
pip install requests
python scripts/fetch_cards.py --mode json --input scripts/blizzard_export.json
```

---

## Альтернатива: Playwright (автоматический браузер)

```bash
pip install playwright
playwright install chromium
python scripts/fetch_cards.py --mode playwright
```

Playwright откроет Chrome автоматически, загрузит страницу и перехватит API.
Если API-перехват не сработает — сохранит `scripts/blizzard_page.html`
который можно открыть и вручную найти данные.

---

## Если ничего не работает: обнови cards_manual.json

Это файл с ручными данными всех карт. Когда выходит новый патч:
1. Открой `https://hearthstone.blizzard.com/en-us/battlegrounds`
2. Найди новые/изменённые карты
3. Обнови их в `scripts/cards_manual.json`
4. Запусти: `python scripts/fetch_cards.py --mode requests`
   (возьмёт имена/картинки с bgcheatsheet + применит ручные правки)

---

## Подключение к Docker

После получения `backend/app/services/cards_scraped.json`:

Раскомментируй в `docker-compose.yml`:
```yaml
- ./scripts/cards_scraped.json:/app/data/cards_scraped.json:ro
```

Перезапусти:
```bash
docker compose down && docker compose up --build
```
