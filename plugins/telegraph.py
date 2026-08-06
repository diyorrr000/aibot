from telethon import events
import requests
import json

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_telegraph(client):
    @client.on(events.NewMessage(pattern=r'\.telegraph(?: (.*))?', outgoing=True))
    async def telegraph_handler(event):
        """Telegra.ph da maqola yaratish"""
        args = event.pattern_match.group(1)
        
        if not args or '|' not in args:
            await event.edit(f"{ERROR_EMOJI} <b>Xato format!</b>\n\n<blockquote>Ishlatish: <code>.telegraph Sarlavha | Maqola matni</code></blockquote>", parse_mode='html')
            return
            
        args = args.strip()
            
        title, content_text = args.split('|', 1)
        title = title.strip()
        content_text = content_text.strip()
        
        await event.edit(f"{CHECK_EMOJI} <b>Maqola tayyorlanmoqda...</b>", parse_mode='html')
        
        try:
            # Muallif nomini olish
            me = await client.get_me()
            author = f"{me.first_name} {me.last_name or ''}".strip()
            
            # Telegra.ph akkunt yaratish (vaqtinchalik)
            acc_res = requests.get(
                "https://api.telegra.ph/createAccount",
                params={"short_name": "UserBot", "author_name": author},
                timeout=10
            ).json()
            
            if not acc_res.get("ok"):
                await event.edit(f"{ERROR_EMOJI} <b>Akkunt yaratishda xato!</b>", parse_mode='html')
                return
                
            token = acc_res["result"]["access_token"]
            
            # Maqola mazmuni (P tegiga o'ralgan)
            content = [{"tag": "p", "children": [content_text]}]
            
            # Sahifa yaratish
            page_data = {
                'access_token': token,
                'title': title,
                'content': json.dumps(content),
                'return_content': 'false'
            }
        
            response = requests.get('https://api.telegra.ph/createPage', params=page_data, timeout=15)
            result = response.json()
            
            if not result.get("ok"):
                await event.edit(f"{ERROR_EMOJI} <b>Maqola yaratishda xato!</b>", parse_mode='html')
                return
                
            page_url = result["result"]["url"]
            
            await event.edit(
                f"{CHECK_EMOJI} <b>Maqola muvaffaqiyatli yaratildi!</b>\n\n"
                f"📝 <b>Sarlavha:</b> <code>{title}</code>\n"
                f"🔗 <b>Maqola havolasi:</b> {page_url}",
                parse_mode='html',
                link_preview=True
            )
            
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xatolik:</b> <code>{str(e)}</code>", parse_mode='html')
