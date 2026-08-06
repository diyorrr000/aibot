from telethon import events
import requests

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_weather(client):
    @client.on(events.NewMessage(pattern=r'\.weather(?: (.*))?', outgoing=True))
    async def weather_handler(event):
        """Ob-havo ma'lumotlarini olish (wttr.in orqali)"""
        city = event.pattern_match.group(1)
        
        if not city:
            # Agar shahar yozilmasa, default Qarshi
            city = "Qarshi"

        await event.edit(f"{CHECK_EMOJI} <b>{city} shahri ob-havosi qidirilmoqda...</b>", parse_mode='html')
        
        try:
            # wttr.in API dan foydalanish (JSON formatida)
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                await event.edit(f"{ERROR_EMOJI} <b>Ob-havo ma'lumotlarini olib bo'lmadi.</b>", parse_mode='html')
                return
            
            data = response.json()
            current = data["current_condition"][0]
            
            # Ma'lumotlarni ajratish
            temp = current["temp_C"]
            feels_like = current["FeelsLikeC"]
            hum = current["humidity"]
            wind = current["windspeedKmph"]
            # Ob-havo tasviri (Description)
            desc = current["weatherDesc"][0]["value"]
            
            text = (
                f"⚡️ <b>Ob-havo: {city}</b>\n\n"
                f"🌏 <b>Holati:</b> <code>{desc}</code>\n"
                f"🔥 <b>Harorat:</b> <code>{temp}°C</code>\n"
                f"🌨 <b>Tuyulishi:</b> <code>{feels_like}°C</code>\n"
                f"🌈 <b>Shamol:</b> <code>{wind} km/soat</code>\n"
                f"💧 <b>Namlik:</b> <code>{hum}%</code>"
            )
            
            await event.edit(text, parse_mode='html')
            
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xatolik yuz berdi:</b> <code>{str(e)}</code>", parse_mode='html')
