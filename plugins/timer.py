from telethon import events
import datetime
import json
import os

CHECK_EMOJI = "✅"
TIMER_EMOJI = "🎄"
import pytz
UZB_TZ = pytz.timezone('Asia/Tashkent')

CONFIG_FILE = "database/timer_config.json"

def get_timer_config():
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        default = {
            "date": "01.01.2027",
            "msg": "🎄 <b>Yangi yilgacha {date} qoldi!</b>\n🥰 <i>Yangi yilni do'stlar davrasida kutamiz</i>"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_timer_config(date, msg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": date, "msg": msg}, f, indent=4)

async def setup_timer(client):
    @client.on(events.NewMessage(pattern=r'\.time', outgoing=True))
    async def time_handler(event):
        """Voqegacha qolgan vaqtni ko'rsatish"""
        config = get_timer_config()
        d_str = config["date"]
        msg_template = config["msg"]

        try:
            d_parts = d_str.split(".")
            target_date = UZB_TZ.localize(datetime.datetime(int(d_parts[2]), int(d_parts[1]), int(d_parts[0])))
            now = datetime.datetime.now(UZB_TZ)

            if target_date < now:
                await event.edit(
                    "<b>Sana o'tib ketgan yoki noto'g'ri!</b>\n"
                    "Sozlash uchun: <code>.settime 31.12.2026 | Yangi yilga</code>",
                    parse_mode='html'
                )
                return

            diff = target_date - now
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds // 60) % 60
            seconds = diff.seconds % 60

            # O'zbekcha formatlash
            time_text = f"{days} kun, {hours} soat, {minutes} minut, {seconds} sekund"
            
            await event.edit(
                msg_template.format(date=time_text),
                parse_mode='html'
            )
        except Exception as e:
            await event.edit(
                "<b>Timer xatosi!</b>\n"
                "Sozlash uchun <code>.settime</code> buyrug'idan foydalaning.",
                parse_mode='html'
            )

    @client.on(events.NewMessage(pattern=r'\.settime(?: (.*))?', outgoing=True))
    async def set_timer_handler(event):
        """Timerni sozlash: .settime 31.12.2025 | Xabar"""
        args = event.pattern_match.group(1)
        
        if not args or "|" not in args:
            await event.edit(
                "<b>Xato format!</b>\n\n"
                "📝 <b>Namuna:</b> <code>.settime 01.01.2027 | Yangi yilgacha {date} qoldi</code>\n\n"
                "<i>{date} - qolgan vaqt o'rniga qo'yiladi.</i>",
                parse_mode='html'
            )
            return

        date_part, msg_part = args.split("|", 1)
        date_part = date_part.strip()
        msg_part = msg_part.strip()

        # Sanani tekshirish
        try:
            d_parts = date_part.split(".")
            datetime.datetime(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
        except Exception:
            await event.edit("<b>Sana formati xato!</b> (Kun.Oy.Yil bo'lishi kerak)")
            return

        save_timer_config(date_part, msg_part)
        await event.edit(f"{CHECK_EMOJI} <b>Timer sozlamalari saqlandi!</b>\n📅 Sana: <code>{date_part}</code>")
