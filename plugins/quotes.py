import requests
import json
import os
from telethon import events, types
import io

# Quotly API is generally used for this
QUOTE_API = "https://bot.lyo.su/quote/generate"

async def setup_quotes(client):
    @client.on(events.NewMessage(pattern=r'\.r (.*)', outgoing=True))
    async def spoof_quote(event):
        # 1. Buyruqni darhol o'chirish
        try:
            await event.delete()
        except Exception:
            pass

        if not event.is_reply:
            return
        
        text = event.pattern_match.group(1)
        reply_msg = await event.get_reply_message()
        
        # Get target user info
        user = await client.get_entity(reply_msg.sender_id)
        
        # Prepare payload for Quotly API
        first_name = user.first_name or "User"
        last_name = user.last_name or ""
        
        import time
        payload = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": "#1b1429",
            "width": 512,
            "height": 512,
            "scale": 1.1,
            "messages": [
                {
                    "entities": [],
                    "avatar": True,
                    "from": {
                        "id": user.id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": user.username or "",
                        "language_code": "en",
                        "title": full_name_helper(user)
                    },
                    "text": text,
                    "replyMessage": {},
                    "date": int(time.time()) # Message ob'ekti ichida bo'lishi shart
                }
            ]
        }

        try:
            response = requests.post(QUOTE_API, json=payload, timeout=10)
            if response.status_code == 200:
                sticker_data = response.json()
                if "result" in sticker_data and "image" in sticker_data["result"]:
                    import base64
                    image_bytes = base64.b64decode(sticker_data["result"]["image"])
                    
                    # Send the sticker
                    sticker_file = io.BytesIO(image_bytes)
                    sticker_file.name = "sticker.webp"
                    
                    await client.send_file(
                        event.chat_id, 
                        sticker_file, 
                        reply_to=reply_msg.id
                    )
        except Exception:
            pass

def full_name_helper(user):
    first = user.first_name or ""
    last = user.last_name or ""
    return f"{first} {last}".strip() or "User"
