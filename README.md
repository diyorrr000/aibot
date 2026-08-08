# 🤖 Telegram Business AI & Userbot Platform (Production-Ready Architecture)

High-performance, modular, and scalable Telegram AI Platform built with **Python 3.12**, **Aiogram 3.x**, **SQLAlchemy Async**, **aiohttp**, **Pydantic v2**, and **Docker**.

Supports multi-model AI (Claude 4.5, Grok 4.3, GPT 4o, Gemini 2.5 Flash Lite) with automated fallbacks, Telegram Business integration, dynamic plugin management, rate limiting, and Uzbekistan profile clock updates.

---

## 🏛 Architecture Overview

```text
telegram-gemini-bot/
├── app/
│   ├── config/             # Pydantic environment configuration
│   ├── database/           # Async SQLAlchemy Engine, Models & Repositories
│   ├── services/
│   │   ├── ai/             # AI Provider Factory (Claude, Grok, GPT, Gemini)
│   │   ├── media.py        # Photo, voice & .ok media saver
│   │   └── animation.py    # Async text animation engine
│   ├── handlers/           # Aiogram routers (Start, Admin, Business)
│   ├── plugins/            # Dynamic Plugin Manager & self-contained modules
│   ├── keyboards/          # Inline UI keyboards & BotCommand menu
│   ├── middlewares/        # Rate limiting & global error handling
│   └── utils/              # Structured logging & helpers
├── Dockerfile              # Non-root, optimized container setup
├── docker-compose.yml      # Multi-container setup with Postgres & Healthchecks
├── requirements.txt        # Pinned dependencies
├── main.py                 # Entrypoint
└── README.md
```

---

## 🚀 Key Features

1. **Multi-Model AI Provider System**
   - Claude 4.5, Grok 4.3, GPT 4o, and Gemini 2.5 Flash Lite.
   - Automatic provider fallbacks and retries on API timeouts.
   - Per-chat model pinning (`.model claude|grok|gpt`).

2. **Telegram Business API Auto-Reply**
   - Native integration with `business_connection_id` and `business_message`.
   - Daily greeting logic (greets once per day per customer, then continues naturally).
   - Silent media saver (`.ok` command).

3. **Dynamic Plugin Manager**
   - Self-contained command plugins (`.weather`, `.tr`, `.currency`, `.yt`, `.anime`, `.tts`, `.telegraph`, `.shortlink`, `.gender`, `.me`, `.do`, `.try`, `.todo`, `.roulette`).
   - Isolated execution boundaries (a plugin error won't crash the bot).

4. **Uzbekistan Profile Clock Sync**
   - Background task updating Telegram Business profile names and descriptions with bold live time digits (`𝟏𝟗:𝟓𝟓`).

5. **Production Ready & Secure**
   - Async non-blocking I/O throughout (`aiohttp`, `asyncio`).
   - Built-in HTTP health check endpoint (`GET /health`) for Render/cloud platforms.
   - Containerized with non-root security practices.

---

## 🛠 Local Setup & Development

### 1. Requirements
- Python 3.10+
- SQLite or PostgreSQL

### 2. Installation
```bash
git clone https://github.com/diyorrr000/aibot.git
cd telegram-gemini-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your details:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite+aiosqlite:///./bot.db
ADMIN_IDS=7306854093
DEFAULT_MODEL=claude
RATE_LIMIT_SECONDS=1.5
PORT=3000
LOG_LEVEL=INFO
```

### 4. Run Locally
```bash
python main.py
```

---

## 🐳 Docker Deployment

Run with Docker Compose:
```bash
docker-compose up -d --build
```

Health check endpoint:
```bash
curl http://localhost:3000/health
```

---

## 📄 License
MIT License