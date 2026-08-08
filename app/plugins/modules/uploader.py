import aiohttp
from aiogram import Bot, types
from aiogram.enums import ChatAction

async def send_fb(bot: Bot, message: types.Message, conn_id: str, text: str, parse_mode="HTML"):
    try:
        await bot.send_message(chat_id=message.chat.id, text=text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode=parse_mode)

async def get_reply_bytes(bot: Bot, message: types.Message):
    reply = message.reply_to_message
    if not reply:
        return None, None
    if reply.document:
        f_info = await bot.get_file(reply.document.file_id)
        content = await bot.download_file(f_info.file_path)
        return content.read(), reply.document.file_name or "file.bin"
    if reply.photo:
        f_info = await bot.get_file(reply.photo[-1].file_id)
        content = await bot.download_file(f_info.file_path)
        return content.read(), "photo.jpg"
    if reply.text:
        return reply.text.encode("utf-8"), "text.txt"
    return None, None

async def cmd_upload(bot: Bot, message: types.Message, conn_id: str, args: str, service: str = "catbox"):
    b_data, filename = await get_reply_bytes(bot, message)
    if not b_data:
        await send_fb(bot, message, conn_id, "🚫 <b>Faylga reply qiling!</b>")
        return

    try:
        async with aiohttp.ClientSession() as session:
            if service == "catbox":
                data = aiohttp.FormData()
                data.add_field("reqtype", "fileupload")
                data.add_field("fileToUpload", b_data, filename=filename)
                async with session.post("https://catbox.moe/user/api.php", data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    link = (await resp.text()).strip()
                    await send_fb(bot, message, conn_id, f"✅ <b>Catbox Link:</b> <code>{link}</code>")
            elif service == "envs":
                data = aiohttp.FormData()
                data.add_field("file", b_data, filename=filename)
                async with session.post("https://envs.sh", data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    link = (await resp.text()).strip()
                    await send_fb(bot, message, conn_id, f"✅ <b>Envs Link:</b> <code>{link}</code>")
            elif service == "0x0":
                data = aiohttp.FormData()
                data.add_field("file", b_data, filename=filename)
                async with session.post("https://0x0.st", data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    link = (await resp.text()).strip()
                    await send_fb(bot, message, conn_id, f"✅ <b>0x0 Link:</b> <code>{link}</code>")
            elif service == "tmpfiles":
                data = aiohttp.FormData()
                data.add_field("file", b_data, filename=filename)
                async with session.post("https://tmpfiles.org/api/v1/upload", data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    res = await resp.json()
                    link = res["data"]["url"]
                    await send_fb(bot, message, conn_id, f"✅ <b>Tmpfiles Link:</b> <code>{link}</code>")
            else:
                data = aiohttp.FormData()
                data.add_field("fileToUpload", b_data, filename=filename)
                data.add_field("reqtype", "fileupload")
                async with session.post("https://catbox.moe/user/api.php", data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    link = (await resp.text()).strip()
                    await send_fb(bot, message, conn_id, f"✅ <b>Link:</b> <code>{link}</code>")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Yuklash xatosi:</b> <code>{e}</code>")

def register(pm):
    for cmd in [".catbox", ".upload"]:
        pm.register_command(cmd, lambda b, m, c, a: cmd_upload(b, m, c, a, "catbox"))
    pm.register_command(".envs", lambda b, m, c, a: cmd_upload(b, m, c, a, "envs"))
    for cmd in [".oxo", ".0x0", ".x0"]:
        pm.register_command(cmd, lambda b, m, c, a: cmd_upload(b, m, c, a, "0x0"))
    pm.register_command(".tmpfiles", lambda b, m, c, a: cmd_upload(b, m, c, a, "tmpfiles"))
