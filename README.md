# Telegram Bot: OCR + Gemini Multimodal Assistant

Ushbu loyiha - Telegram bot bo'lib, u rasmlardagi matnlarni **EasyOCR** orqali o'qiydi va **Gemini** modeli yordamida rasmni multimodal tahlil qilib, matndagi xatolarni tuzatadi hamda rasmdagi topshiriq/savollarga javob beradi.

## 🚀 Render.com platformasida bepul 24/7 ishga tushirish (Deploy)

Render platformasida botni 24/7 rejimida mutlaqo bepul ishlatish uchun quyidagi qadamlarni bajaring:

### 1. Render.com saytida yangi xizmat ochish
1. [Render.com](https://render.com) saytiga kiring va ro'yxatdan o'ting.
2. Boshqaruv panelida **New** tugmasini bosing va **Web Service** (bepul va HTTP port qo'llab-quvvatlaydi) tanlang.
3. GitHub hisobingizni ulab, `aibot` repozitoriyasini tanlang.

### 2. Sozlamalarni kiritish
* **Name**: botingiz uchun ixtiyoriy nom (masalan, `telegram-ocr-gemini-bot`)
* **Environment**: `Python` yoki `Python 3`
* **Region**: O'zingizga yaqin mintaqa (masalan, `Frankfurt`)
* **Branch**: `main`
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `python bot.py`
* **Instance Type**: `Free` (bepul reja)

### 3. Ekologik o'zgaruvchilar (Environment Variables)
Sahifaning pastki qismidagi **Advanced** tugmasini bosing va **Add Environment Variable** orqali quyidagi o'zgaruvchilarni qo'shing:

| Kalit (Key) | Qiymat (Value) | Izoh |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | `8062351285:AAHc0dGfwAPMOZ4pswofz3P-ZINIZJiEQ9A` | Sizning Telegram bot tokeningiz |
| `GEMINI_API_KEY` | `AIzaSyDszGSEBq9yVxXfiTA16on1LGcviw6W5Es` | Gemini API kaliti |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Standart ishlatiladigan Gemini modeli |
| `PORT` | `3000` | Render porti (bot ichidagi HTTP server buni eshitadi) |
| `USE_EASYOCR` | `False` | Render bepul rejasi (512MB RAM limit) uchun **False** bo'lishi kerak. Bu orqali OOM (Out Of Memory) xatoligi oldi olinadi va rasm/matn multimodal Gemini orqali tahlil qilinadi. Mahalliy kompyuterda ishlatish uchun **True** qilish mumkin. |

### 4. Deploy va Launch
Barcha ma'lumotlarni kiritgach, **Deploy Web Service** tugmasini bosing. Render loyihani avtomatik ravishda build qiladi va ishga tushiradi.

> [!NOTE]
> Bot ichiga avtomat ravishda Render platformasi uchun HTTP Port eshituvchi (Health Check) server joylashtirilgan. Shuning uchun Render'dagi bepul Web Service har doim yashil (Live) holatda qoladi.

## 🔄 Cronjob orqali 24/7 faollashtirish (Sleep oldini olish)

Render bepul rejasidagi xizmatlar agar 15 daqiqa davomida HTTP so'rov kelmasa, avtomatik "uyqu" (sleep) rejimiga o'tadi. Bot doimiy faol bo'lishi uchun quyidagilardan birini qiling:

1. [UptimeRobot](https://uptimerobot.com) saytida bepul hisob oching.
2. **HTTP(s) Monitor** qo'shing.
3. Monitor URL manziliga Render tomonidan berilgan loyihaning umumiy havolasini kiriting (masalan: `https://telegram-ocr-gemini-bot.onrender.com`).
4. Oraliq vaqtni **5 yoki 10 daqiqa** qilib belgilang.
5. Endi UptimeRobot har 5 daqiqada Render botingizga so'rov yuboradi va botingiz hech qachon uyquga ketmaydi (24/7 ishlaydi).