from telethon import events
import requests

CHECK_EMOJI = "✅"

async def setup_currency(client):
    @client.on(events.NewMessage(pattern=r'\.kurs', outgoing=True))
    async def currency_handler(event):
        """Markaziy bank valyuta kurslarini olish"""
        await event.edit(f"{CHECK_EMOJI} <b>Valyuta kurslari olinmoqda...</b>", parse_mode='html')
        
        try:
            # CBU API (Uzbekistan Central Bank)
            response = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/", timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # Asosiy valyutalarni filtrlash
                main_vals = ["USD", "EUR", "RUB"]
                curr_info = []
                
                for item in data:
                    if item["Ccy"] in main_vals:
                        flag = "🇺🇸" if item["Ccy"] == "USD" else "🇪🇺" if item["Ccy"] == "EUR" else "🇷🇺"
                        curr_info.append(
                            f"{flag} <b>1 {item['Ccy']}</b> = <code>{item['Rate']}</code> so'm "
                            f"({item['Diff']})"
                        )
                
                text = (
                    f"💰 <b>Markaziy Bank Kurslari:</b>\n"
                    f"📅 <i>Bugun: {data[0]['Date']}</i>\n\n"
                    + "\n".join(curr_info) +
                    f"\n\n🔄 <i>Oxirgi marta yangilandi: {data[0]['Date']}</i>"
                )
                await event.edit(text, parse_mode='html')
            else:
                await event.edit("<b>Ma'lumot olishda xato!</b>")
        except Exception as e:
            await event.edit(f"<b>Xatolik:</b> <code>{str(e)}</code>")
