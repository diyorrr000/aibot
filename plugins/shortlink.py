from telethon import events
import requests
import re

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_shortlink(client):
    @client.on(events.NewMessage(pattern=r'\.(?:shlink|shortlink)(?: (.*))?', outgoing=True))
    async def shortlink_handler(event):
        """Linklarni qisqartirish"""
        args = event.pattern_match.group(1)
        if not args:
            await event.edit(f"{ERROR_EMOJI} <b>Link kiriting!</b>\n\n<blockquote>Namuna: <code>.shlink https://google.com</code></blockquote>", parse_mode='html')
            return
            
        url = args.strip()
        
        # URL ekanligini tekshirish (oddiy regex)
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://' # http:// yoki https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domèn...
            r'localhost|' # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...yoki ip
            r'(?::\d+)?' # ixtiyoriy port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            await event.edit(f"{ERROR_EMOJI} <b>Iltimos, haqiqiy URL manzilini yuboring!</b>\n\n<blockquote>Namuna: <code>.shlink https://google.com</code></blockquote>", parse_mode='html')
            return

        await event.edit(f"{CHECK_EMOJI} <b>Link qisqartirilmoqda...</b>", parse_mode='html')

        try:
            api_url = f"https://is.gd/create.php?format=json&url={url}"
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            if "shorturl" in data:
                short_url = data["shorturl"]
                await event.edit(
                    f"{CHECK_EMOJI} <b>Link muvaffaqiyatli qisqartirildi!</b>\n\n"
                    f"🔗 <b>Original:</b> <code>{url}</code>\n"
                    f"🚀 <b>Qisqa link:</b> <code>{short_url}</code>",
                    parse_mode='html'
                )
            else:
                error_msg = data.get("errormessage", "Noma'lum xato")
                await event.edit(f"{ERROR_EMOJI} <b>Xato yuz berdi:</b> <code>{error_msg}</code>", parse_mode='html')
                
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Server bilan ulanishda xato:</b> <code>{str(e)}</code>", parse_mode='html')
