# 🚀 Telegram Business AI Bot (aiogram 3.x + OpenAI GPT + PostgreSQL)

Ushbu loyiha **Telegram Business** hisoblari uchun mo'ljallangan ishlab chiqarishga tayyor (production-ready) Sun'iy Intellekt Asistent botidir. Bot Telegram Business ulanishi orqali mijozlaringizdan kelgan barcha shaxsiy xabarlarga sizning nomingizdan **OpenAI GPT-4o / GPT-4o-mini** modellaridan foydalanib avtomatik javob beradi.

---

## ✨ Imkoniyatlar

- **Telegram Business 7.2+ Integration**: `business_connection`, `business_message`, `edited_business_message` va `deleted_business_messages` hodisalarini to'liq qo'llab-quvvatlaydi.
- **Multimodal AI**: 
  - **Matn**: GPT-4o-mini / GPT-4o orqali kontekstli muloqot.
  - **Rasm (Vision)**: GPT Vision yordamida rasmlarni tahlil qilish.
  - **Ovozli xabarlar (Whisper)**: Ovozli xabarlarni matnga o'girib, aqlli javob qaytarish.
  - **Hujjatlar**: Matnli hujjat fayllarini o'qish va tahlil qilish.
- **PostgreSQL Ma'lumotlar Bazasi**: SQLAlchemy 2.0 Async ORM yordamida Business Connection ID-lar, har bir mijoz suhbat tarixi va sozlamalarni saqlash.
- **Tizim Yo'riqnomasi (System Prompt)**: Har bir biznes egasi `/setprompt` buyrug'i orqali bot mijozlar bilan qanday gaplashishini belgilashi mumkin.
- **Production Xususiyatlari**: Yozmoqda... (Typing indicator), Rate limiting (spamdan himoya), xatoliklarni boshqarish, Docker va Railway deployment.

---

## 🛠️ Texnologiyalar Steki

- **Til**: Python 3.12+
- **Kutubxona**: `aiogram 3.x`
- **AI Platforma**: OpenAI API (`AsyncOpenAI`, GPT-4o-mini, Whisper)
- **Baza**: PostgreSQL (`asyncpg` + `SQLAlchemy 2.0`) / SQLite (`aiosqlite`)
- **Container**: Docker & Docker Compose

---

## 📋 Telegram Business Hisobiga Ulash Ketma-ketligi

1. Telegram ilovangizni oching (Telegram Premium / Business obunasiga ega bo'lishingiz kerak).
2. **Settings (Sozlamalar)** -> **Telegram Business** -> **Chat Bots** bo'limiga kiring.
3. Botni tanlang va qo'shing.
4. Botga mijozlar xabarlarini o'qish va javob yuborish ruxsatlarini bering.
5. Tayyor! Bot endi mijozlaringizdan kelgan shaxsiy xabarlarga avtomatik javob beradi.

---

## 🚀 Mahalliy Ishga Tushirish (Local Setup)

1. Loyihani yuklab oling va papkaga o'ting:
   ```bash
   cd telegram-gemini-bot
   ```

2. Virtual muhit yarating va faollashtiring:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. Bog'liqliklarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

4. `.env` faylini yarating va kalitlarni kiriting:
   ```env
   TELEGRAM_BOT_TOKEN=8062351285:AAHc0dGfwAPMOZ4pswofz3P-ZINIZJiEQ9A
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=sqlite+aiosqlite:///./bot.db
   OPENAI_MODEL=gpt-4o-mini
   ```

5. Botni ishga tushiring:
   ```bash
   python main.py
   ```

---

## 🐳 Docker Compose bilan ishga tushirish (PostgreSQL + Bot)

```bash
docker-compose up -d --build
```

---

## ☁️ Railway.app yoki Render.com ga yuklash

- **Railway.app**: Repozitoriyani ulaganingizda, u avtomatik ravishda `Procfile` faylini aniqlaydi va `worker: python -u main.py` orqali ishga tushiradi.
- **Variables**: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, va `DATABASE_URL` kalitlarini platformaning Environment Variables bo'limiga kiriting.