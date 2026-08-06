from telethon import events
import requests
import urllib.parse
import os

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_text2speech(client):
    @client.on(events.NewMessage(pattern=r'\.(?:t2s|text2speech)(?: (.*))?', outgoing=True))
    async def t2s_handler(event):
        """Matnni ovozli xabarga aylantirish (Google TTS orqali)"""
        args_str = event.pattern_match.group(1)
        if not args_str:
            await event.edit(f"{ERROR_EMOJI} <b>Matn yozing!</b>\n\n<blockquote>Namuna: <code>.t2s Salom uz</code> (uz, ru, en)</blockquote>", parse_mode='html')
            return
            
        raw_args = args_str.strip().split()
            
        # Tilni aniqlash (oxirgi so'z til kodi bo'lsa)
        lang = "uz" # Standart til
        available_langs = ["uz", "ru", "en", "tr", "ar", "de", "fr"]
        
        if raw_args[-1].lower() in available_langs:
            lang = raw_args[-1].lower()
            text = " ".join(raw_args[:-1])
        else:
            text = " ".join(raw_args)

        if not text:
            await event.edit(f"{ERROR_EMOJI} <b>Matn yozing!</b>", parse_mode='html')
            return

        await event.edit(f"{CHECK_EMOJI} <b>Matn ovozga aylantirilmoqda (Google AI)...</b>\n🌍 <b>Til:</b> <code>{lang.upper()}</code>", parse_mode='html')
        
        # Google Translate TTS API (tw-ob client ishlatilganda captcha so'ramaydi)
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                file_name = f"voice_{event.id}.mp3"
                with open(file_name, "wb") as f:
                    f.write(response.content)
                    
                caption = (
                    f"{CHECK_EMOJI} <b>Matn ovozli xabarga aylantirildi!</b>\n\n"
                    f"📝 <b>Matn:</b> <code>{text}</code>\n"
                    f"🌍 <b>Til:</b> <i>{lang.upper()}</i>"
                )
                
                await client.send_file(
                    event.chat_id,
                    file_name,
                    voice_note=True,
                    caption=caption,
                    parse_mode='html',
                    reply_to=event.reply_to_msg_id
                )
                
                await event.delete()
                if os.path.exists(file_name):
                    os.remove(file_name)
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Google TTS xatosi: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xatolik:</b> <code>{str(e)}</code>", parse_mode='html')
            if 'file_name' in locals() and os.path.exists(file_name):
                os.remove(file_name)
