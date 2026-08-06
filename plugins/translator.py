from telethon import events
import requests
import urllib.parse

CHECK_EMOJI = "✅"

async def setup_translator(client):
    @client.on(events.NewMessage(pattern=r'\.tr(?: (.*))?', outgoing=True))
    async def translator_handler(event):
        """Matnni tarjima qilish"""
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        if not args and not reply:
            await event.edit(
                "<b>Xato ishlatish!</b>\n\n"
                f"📝 <b>Namuna:</b>\n"
                f"1. <code>.tr en Salom</code> (Matnni tarjima qilish)\n"
                f"2. <code>.tr ru</code> (Reply qilingan xabarni tarjima qilish)",
                parse_mode='html'
            )
            return

        # Til va matnni ajratish
        target_lang = "uz"
        text = ""
        
        if args:
            parts = args.split(maxsplit=1)
            target_lang = parts[0]
            if len(parts) > 1:
                text = parts[1]
        
        if not text and reply:
            text = reply.raw_text

        if not text:
            await event.edit("<b>Tarjima qilish uchun matn topilmadi!</b>")
            return

        await event.edit(f"{CHECK_EMOJI} <b>Tarjima qilinmoqda...</b> (<code>{target_lang}</code>)", parse_mode='html')

        try:
            # Google Translate API (Free endpoint)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = "".join([part[0] for part in result[0]])
                
                output = (
                    f"<b>Tarjima (<code>{target_lang.upper()}</code>):</b>\n\n"
                    f"<blockquote>{translated_text}</blockquote>"
                )
                await event.edit(output, parse_mode='html')
            else:
                await event.edit(f"<b>API xatosi: {response.status_code}</b>")
        except Exception as e:
            await event.edit(f"<b>Xatolik:</b> <code>{str(e)}</code>")
