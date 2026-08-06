from telethon import events
import requests

# Jins emojilari
MALE_EMOJI = "🖤"
FEMALE_EMOJI = "❤️🔥"
UNKNOWN_EMOJI = "🩵"
CHECK_EMOJI = "✅"

async def setup_gender_guesser(client):
    @client.on(events.NewMessage(pattern=r'\.gender(?: (.*))?', outgoing=True))
    async def gender_handler(event):
        """Username yoki reply orqali jinsni aniqlash"""
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        if not reply and not args:
            await event.edit(f"{ERROR_EMOJI} <b>Xato ishlatish!</b>\n\n<blockquote>Namuna: <code>.gender @username</code> yoki <code>.gender Ism</code></blockquote>", parse_mode='html')
            return
            
        try:
            if reply:
                user = await client.get_entity(reply.sender_id)
                name = user.first_name
            else:
                if args.startswith("@"):
                    user = await client.get_entity(args)
                    name = user.first_name
                else:
                    name = args # Ism sifatida qabul qilish
            
            if not name:
                await event.edit(f"{CHECK_EMOJI} <b>Foydalanuvchining ismi topilmadi!</b>", parse_mode='html')
                return

            await event.edit(f"{CHECK_EMOJI} <b>`{name}` ismi tahlil qilinmoqda...</b>", parse_mode='html')
            
            response = requests.get(f"https://api.genderize.io?name={name}", timeout=10)
            result = response.json()
            
            gender_val = result.get("gender")
            if gender_val == "female":
                emoji = FEMALE_EMOJI
                gender_text = "Ayol"
            elif gender_val == "male":
                emoji = MALE_EMOJI
                gender_text = "Erkak"
            else:
                emoji = UNKNOWN_EMOJI
                gender_text = "Noma'lum"
                
            await event.edit(
                f"{CHECK_EMOJI} <b>Taxminiy jins: {name}</b>\n\n"
                f"{emoji} <b>Jinsi:</b> <code>{gender_text}</code>",
                parse_mode='html'
            )
            
        except Exception as e:
            await event.edit(f"🚫 <b>Xatolik yuz berdi:</b> <code>{e}</code>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.gendername (.*)', outgoing=True))
    async def gendername_handler(event):
        """Faqat ism orqali jinsni aniqlash"""
        name = event.pattern_match.group(1)
        
        await event.edit(f"{CHECK_EMOJI} <b>`{name}` ismi tahlil qilinmoqda...</b>", parse_mode='html')
        
        try:
            response = requests.get(f"https://api.genderize.io?name={name}", timeout=10)
            result = response.json()
            
            gender_val = result.get("gender")
            if gender_val == "female":
                emoji = FEMALE_EMOJI
                gender_text = "Ayol"
            elif gender_val == "male":
                emoji = MALE_EMOJI
                gender_text = "Erkak"
            else:
                emoji = UNKNOWN_EMOJI
                gender_text = "Noma'lum"
                
            await event.edit(
                f"{CHECK_EMOJI} <b>Taxminiy jins: {name}</b>\n\n"
                f"{emoji} <b>Jinsi:</b> <code>{gender_text}</code>",
                parse_mode='html'
            )
        except Exception as e:
            await event.edit(f"🚫 <b>Xatolik:</b> <code>{e}</code>", parse_mode='html')
