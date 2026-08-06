import requests
from telethon import events
import logging

# Yangi DeepSeek AI API (ZecoAI)
AI_API_URL = "https://zecora0.serv00.net/deepseek.php"

# AI ga qanday ishlashni o'rgatuvchi instruction
SYSTEM_PROMPT = "Siz aqlli va foydali yordamchisiz. Har doim o'zbek tilida javob bering. Javoblaringiz qisqa va tushunarli bo'lsin."

async def setup_ai(client):
    @client.on(events.NewMessage(pattern=r'\.ai(?: (.*))?', outgoing=True))
    async def ai_handler(event):
        # Agar argument bo'lsa o'shani, bo'lmasa replyni olamiz
        query = event.pattern_match.group(1)
        
        if not query and event.is_reply:
            reply_msg = await event.get_reply_message()
            query = reply_msg.text

        if not query:
            await event.edit("<b>Iltimos, AI ga savol bering yoki biror xabarga reply qiling!</b>\n\n<blockquote>Namuna: <code>.ai Salom</code> yoki <code>.ai</code> (xabarga reply qilib)</blockquote>", parse_mode='html')
            return

        await event.edit("<b>AI javob tayyorlamoqda...</b>")
        
        try:
            # AI ga system prompt bilan birga savol yuborish
            full_message = f"{SYSTEM_PROMPT}\n\nSavol: {query}"
            
            payload = {
                "model": "2",
                "message": full_message
            }
            
            # POST request
            response = requests.post(AI_API_URL, data=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    answer = data.get("response")
                    if answer:
                        # Matn uzunligini tekshirish
                        if len(answer) > 4000:
                            answer = answer[:4000] + "..."
                        
                        # Faqat javobni o'zini chiqarish (DeepSeek nomi olib tashlandi)
                        await event.edit(answer)
                    else:
                        await event.edit("<b>AI dan bo'sh javob keldi.</b>")
                else:
                    error_msg = data.get("error", "Noma'lum xato")
                    await event.edit(f"<b>AI Xatosi:</b> <code>{error_msg}</code>")
            else:
                await event.edit(f"<b>Server xatosi: {response.status_code}</b>")
                
        except Exception as e:
            logging.error(f"AI Error: {e}")
            await event.edit(f"<b>Xato yuz berdi:</b> <code>{str(e)}</code>")
