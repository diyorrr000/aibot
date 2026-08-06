from telethon import events
import io
import requests
import json
import os

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_uploader(client):
    async def get_file_for_upload(event):
        """Faylni yuklab olish va io.BytesIO ob'ektiga aylantirish"""
        reply = await event.get_reply_message()
        if not reply:
            await event.edit(f"{ERROR_EMOJI} <b>Faylga reply qiling!</b>\n\n<blockquote>Namuna: <code>.catbox</code> (faylga reply qilib)</blockquote>", parse_mode='html')
            return None
            
        await event.edit(f"{CHECK_EMOJI} <b>Fayl tayyorlanmoqda...</b>", parse_mode='html')
        
        if reply.media:
            # Faylni xotiraga yuklab olish
            file_data = await client.download_media(reply.media, bytes)
            file = io.BytesIO(file_data)
            if hasattr(reply.media, "document"):
                file.name = (reply.file.name if reply.file else None) or f"file_{reply.file.id}"
            else:
                file.name = f"photo_{reply.id}.jpg"
        else:
            # Agar xabarda faqat matn bo'lsa
            file = io.BytesIO(bytes(reply.raw_text, "utf-8"))
            file.name = "text.txt"
            
        return file

    @client.on(events.NewMessage(pattern=r'\.catbox', outgoing=True))
    async def catbox_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>Catbox.moe ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post(
                "https://catbox.moe/user/api.php",
                files={"fileToUpload": file},
                data={"reqtype": "fileupload"},
                timeout=30
            )
            if response.ok:
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{response.text}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.envs', outgoing=True))
    async def envs_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>Envs.sh ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post("https://envs.sh", files={"file": file}, timeout=30)
            if response.ok:
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{response.text.strip()}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.kappa', outgoing=True))
    async def kappa_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>Kappa.lol ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post("https://kappa.lol/api/upload", files={"file": file}, timeout=30)
            if response.ok:
                data = response.json()
                url = f"https://kappa.lol/{data['id']}"
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{url}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.oxo', outgoing=True))
    @client.on(events.NewMessage(pattern=r'\.0x0', outgoing=True))
    async def oxo_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>0x0.st ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post("https://0x0.st", files={"file": file}, data={"secret": True}, timeout=30)
            if response.ok:
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{response.text.strip()}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.x0', outgoing=True))
    async def x0_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>x0.at ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post("https://x0.at", files={"file": file}, timeout=30)
            if response.ok:
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{response.text.strip()}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.tmpfiles', outgoing=True))
    async def tmpfiles_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>Tmpfiles.org ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": file}, timeout=30)
            if response.ok:
                data = response.json()
                url = data["data"]["url"]
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{url}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.pomf', outgoing=True))
    async def pomf_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>Pomf.lain.la ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.post("https://pomf.lain.la/upload.php", files={"files[]": file}, timeout=30)
            if response.ok:
                data = response.json()
                url = data["files"][0]["url"]
                await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{url}</code>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.bash', outgoing=True))
    async def bash_handler(event):
        file = await get_file_for_upload(event)
        if not file: return
        await event.edit(f"{CHECK_EMOJI} <b>Bashupload.com ga yuklanmoqda...</b>", parse_mode='html')
        try:
            response = requests.put("https://bashupload.com", data=file.read(), timeout=30)
            if response.ok:
                urls = [line for line in response.text.split("\n") if "wget" in line]
                if urls:
                    url = urls[0].split()[-1]
                    await event.edit(f"{CHECK_EMOJI} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{url}</code>", parse_mode='html')
                else:
                    await event.edit(f"{ERROR_EMOJI} <b>Link topilmadi!</b>", parse_mode='html')
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Xato: {response.status_code}</b>", parse_mode='html')
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>Xato: {str(e)}</b>", parse_mode='html')
