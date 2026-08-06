from telethon import events
import os
import importlib
import logging

# Xavfli kalit so'zlar ro'yxati
DANGEROUS_KEYWORDS = [
    "os.system", "subprocess", "shutil.rmtree", "rm -rf", 
    "exec(", "eval(", "base64.b64decode", "getattr", "__import__",
    "open('/etc/passwd'", ".remove(", "os.kill(", "os.popen(",
]

def is_safe(content):
    """Kodni xavfli buyruqlar bor-yo'qligiga tekshiradi"""
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in content:
            return False, keyword
    return True, None

from config import ADMIN_ID

async def setup_plugins_manager(client):
    @client.on(events.NewMessage(pattern=r'\.install', outgoing=True))
    async def install_plugin(event):
        # Admin tekshiruvi
        if str(event.sender_id) != str(ADMIN_ID):
            await event.edit("🚫 <b>Faqat admin modullarni o'rnatishi mumkin!</b>", parse_mode='html')
            return

        if not event.is_reply:
            await event.edit("🚫 <b>Iltimos, .py fayliga reply qiling!</b>", parse_mode='html')
            return
        
        reply_msg = await event.get_reply_message()
        if not reply_msg.file or not reply_msg.file.name.endswith(".py"):
            await event.edit("🚫 <b>Bu .py fayli emas!</b>", parse_mode='html')
            return

        await event.edit("✅ <b>Modul xavfsizligi tekshirilmoqda...</b>", parse_mode='html')
        
        # Faylni yuklab olish
        plugin_path = await reply_msg.download_media(file="plugins/")
        
        with open(plugin_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Xavfsizlikni tekshirish
        safe, keyword = is_safe(content)
        if not safe:
            os.remove(plugin_path)
            await event.edit(f"🚫 <b>XAVF ANIQLANDI!</b>\nModulda taqiqlangan buyruq topildi: <code>{keyword}</code>\n\n<i>Xavfsizlik maqsadida ushbu modul yuklanmadi.</i>", parse_mode='html')
            return

        try:
            # Modulni dinamik yuklashga urinish (faqat setup funksiyasi bo'lsa)
            module_name = f"plugins.{os.path.basename(plugin_path)[:-3]}"
            module = importlib.import_module(module_name)
            
            # Agar modulda setup_ funksiyasi bo'lsa, uni ishga tushiramiz
            setup_func = None
            for attr in dir(module):
                if attr.startswith("setup_"):
                    setup_func = getattr(module, attr)
                    break
            
            if setup_func:
                await setup_func(client)
                await event.edit(f"✅ <b>Modul o'rnatildi va ishga tushirildi!</b>\nFayl: <code>{os.path.basename(plugin_path)}</code>", parse_mode='html')
            else:
                await event.edit(f"✅ <b>Modul saqlandi, lekin `setup_` topilmadi.</b>", parse_mode='html')
                
        except Exception as e:
            await event.edit(f"🚫 <b>Modul xatosi:</b> <code>{e}</code>", parse_mode='html')
