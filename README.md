# 🤖 Telegram Business AI & Userbot (telegram-gemini-bot)

## 📌 Loyiha Haqida

Ushbu loyiha Telegram Business foydalanuvchilari uchun maxsus yaratilgan **AI Yordamchi** va **Userbot** funksiyalarini birlashtirgan universal bot hisoblanadi. Bot Telegram Business orqali sizning nomingizdan kelgan xabarlarga avtomatik javob beradi (Claude 4.5 va Grok 4.3 orqali) va turli `.command` animatsiyalar hamda buyruqlarni qo'llab-quvvatlaydi.

## 🚀 Asosiy Qilingan Ishlar

1. **AI Modellarni Integratsiya Qilish (KILWA API)**
   - Claude Haiku 4.5 va Grok 4.3 modellari ulandi.
   - Ikkala model o'rtasida `/admin` panelidan real vaqtda almashish imkoniyati qo'shildi.

2. **Telegram Business va Ruxsat (Approval) Tizimi**
   - Yangi Business hisob ulanganida u **Avto-to'xtatilgan (Disabled)** holatda bo'ladi.
   - Admin (`7306854093`) ga tasdiqlash uchun xabar boradi (`/approve <conn_id>` yoki inline tugma orqali).
   - Foydalanuvchining real `@username` yoki Ismi AI Promptga kiritildi (bot o'zini "Noma'lum" demaydi).

3. **O'zbekiston Soati (Profil Ismida)**
   - Asinxron background tsikl orqali har 1 daqiqada bot o'zining Business Connection egalarining "Familiya" qismiga joriy soatni qalin (BOLD) raqamlarda (`𝟏𝟗:𝟓𝟓`) yangilab turadi.

4. **Userbot Buyruqlari (.help) va Animatsiyalar**
   - Userbot repo-dan 31 ta plaginlar fayllari ko'chirib o'tildi.
   - Aiogram Business Message doirasida **Animatsiyalar** (masalan `.love`, `.snow`, `.xd`, `.police`) Aiogramning `edit_message_text` orqali to'g'ridan-to'g'ri ishlashi joriy qilindi. (Alohida Telethon sessiyasi talab qilinmaydi!)
   - **Xatolikni to'g'irlash (Typo Correction)**: Agar foydalanuvchi `.lovee` yoki `.tts2` deb xato yozsa, bot eng yaqin to'g'ri buyruqni taklif qiladi va tushuntiradi.

5. **Xavfsizlik va Anti-Ban Guard (FloodWait himoyasi)**
   - Bot juda ko'p so'rov yubormasligi uchun maxsus asinxron Delay (kechikish) tizimi va Rate Limiter yozildi.
   - Render.com dagi `TelegramConflictError` xatoligini bartaraf etish uchun `start_polling` oldidan webhooklarni agressiv tozalash tizimi qo'shildi.

## 🛠 Hozirgi Holat (Qayerga keldik?)

- Barcha yozilgan xatolar tuzatilib (ImportError, TelegramConflictError) GitHub-ga Deploy qilindi.
- Admin Panel (Inline Buttons) mukammal ishlayapti: Avto-javobni yoqish, Modelni o'zgartirish, Profil soati, va Hisoblarni tasdiqlash tugmalari.
- `.help` buyrug'i barcha chatlarda (egasi yozsa) ishlaydi va ro'yxatni ko'rsatadi.
- Asosiy Userbot animatsiyalari `.love`, `.snow`, `.ping` va boshqalar endi Aiogram orqali **hamma chatlarda (qayerga yozsangiz ham)** ishlaydi.

## 📝 Keyingi Qadamlar (TODO)
- Qolgan Userbot API (ob-havo, tarjima, tiktok yuklash) funksiyalarini Aiogram orqali `business_message.py` ga to'liq integratsiya qilish (hozirda animatsiyalar qismi ishlaydi).

---
*Ushbu hujjat Antigravity AI tomonidan yaratildi.*