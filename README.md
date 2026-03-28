# HS Battlegrounds Sandbox

Симулятор боёв Hearthstone Battlegrounds. Собери доски, симулируй бой, смотри replay.

## Структура проекта

```
hs-battlegrounds/
├── backend/                 # FastAPI + SQLite
│   ├── app/
│   │   ├── api/             # Роуты: /api/cards, /api/simulate
│   │   ├── core/            # БД (SQLite)
│   │   └── services/
│   │       ├── blizzard.py  # Загрузка карт в БД
│   │       ├── cards_data.py# Статичный датасет (fallback)
│   │       ├── cards_scraped.json  # ← генерирует fetch_cards.py
│   │       └── simulator.py # Движок симуляции боёв
│   ├── Dockerfile
│   ├── requirements.txt
│   └── startup.py           # Инициализация БД при старте
├── frontend/                # React (Vite) + nginx
│   ├── src/
│   ├── nginx-frontend.conf  # nginx: статика + proxy /api/ → backend
│   └── Dockerfile
├── scripts/
│   ├── fetch_cards.py       # ← ПАРСЕР КАРТ (запускать вручную)
│   └── cards_manual.json    # Ручные правки статов карт
└── docker-compose.yml       # 2 контейнера: frontend + backend
```

## Быстрый старт

```bash
git clone <repo-url>
cd hs-battlegrounds
docker compose up --build
```

Открывай http://localhost

## Обновление карт (актуальный патч)

Скрипт `scripts/fetch_cards.py` парсит **bgcheatsheet.com** (актуальный пул карт)
и по возможности обогащает данными из **HearthstoneJSON** (статы, тиры, тексты).

### Шаг 1: Установи зависимости

```bash
pip install requests beautifulsoup4 lxml
```

### Шаг 2: Запусти скрипт

```bash
python scripts/fetch_cards.py
```

Скрипт:
1. Скачает все фракции с bgcheatsheet.com (Beast, Demon, Dragon, ...)
2. Попытается загрузить статы из HearthstoneJSON
3. Применит ручные правки из `scripts/cards_manual.json`
4. Сохранит результат в `backend/app/services/cards_scraped.json`

### Шаг 3: Раскомментируй volume в docker-compose.yml

```yaml
volumes:
  - db-data:/app/data
  - ./scripts/cards_scraped.json:/app/data/cards_scraped.json:ro  # ← раскомментируй
```

### Шаг 4: Перезапусти

```bash
docker compose down
docker compose up --build
```

Бэкенд автоматически найдёт `cards_scraped.json` и загрузит карты из него.

### Ручные правки статов

Если HearthstoneJSON недоступен или данные неточные — редактируй `scripts/cards_manual.json`:

```json
{
  "Cave Hydra": {"tier": 3, "attack": 2, "health": 4, "mechanics": ["cleave"]},
  "Brann Bronzebeard": {"tier": 4, "attack": 2, "health": 4}
}
```

После правок повторно запусти `fetch_cards.py` и перезапусти docker compose.

## API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/cards/` | Список карт (фильтры: tier, race, mechanic) |
| GET | `/api/cards/{id}` | Одна карта |
| POST | `/api/simulate/battle` | Monte Carlo симуляция (1000 итераций) |
| POST | `/api/simulate/replay` | Пошаговый replay боя |
| POST | `/api/cards/sync` | Принудительная перезагрузка карт в БД |
| GET | `/api/health` | Healthcheck |
| GET | `/docs` | Swagger UI |

## Деплой на сервер

1. Купи VPS (Timeweb/Selectel, ~200₽/мес) и домен (.ru ~30₽/год)
2. На сервере:

```bash
# Установи Docker
curl -fsSL https://get.docker.com | sh

# Клонируй репо
git clone <repo-url>
cd hs-battlegrounds

# Запусти
docker compose up -d --build
```

3. Настрой A-запись домена → IP сервера
4. Для HTTPS добавь Certbot (Let's Encrypt):

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.ru
```

## Технологии

- **Frontend**: React 18 + Vite, Zustand, @dnd-kit, Framer Motion
- **Backend**: Python 3.11, FastAPI, SQLite (aiosqlite)
- **Infra**: Docker Compose, nginx (2 контейнера)
