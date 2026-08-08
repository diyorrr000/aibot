import importlib
import logging
import pkgutil
import difflib
from typing import Dict, Any, Callable, Optional, Tuple
from aiogram import Bot, types
from app.utils.logger import logger

COMMAND_USAGE: Dict[str, str] = {
    ".weather": ".weather Tashkent (yoki Xorazm, Urgench, Toshkent)",
    ".tr": ".tr en Salom dunyo (yoki matnga reply qilib)",
    ".tts": ".tts Salom dunyo (matnni ovozga aylantirish)",
    ".ai": ".ai O'zbekiston poytaxti qayer? (Gemini AI bilan muloqot)",
    ".gemini": ".gemini Savolingiz",
    ".currency": ".currency (Markaziy bank valyuta kurslari)",
    ".kurs": ".kurs (Valyuta kurslari)",
    ".shortlink": ".shortlink https://link.com",
    ".shlink": ".shlink https://link.com",
    ".gender": ".gender Sardor",
    ".telegraph": ".telegraph Sarlavha | Matn mazmuni",
    ".yt": ".yt Uzbek tili darslari",
    ".acc": ".acc @username (Akkunt haqida ma'lumot)",
    ".art": ".art (Yoqimli anime surati)",
    ".nsfwart": ".nsfwart (NSFW anime surati)",
    ".auto": ".auto @guruhlink 60 | Sotiladi iPhone 15!",
    ".stopauto": ".stopauto @guruhlink",
    ".time": ".time (Taymer)",
    ".settime": ".settime 01.01.2027 | Yangi yilgacha {date} qoldi",
    ".rf": ".rf (Faylga reply qilib matn o'qish)",
    ".read": ".read (Faylga reply qilib o'qish)",
    ".q": ".q (Matnli xabarga reply qilib stiker yaratish)",
    ".r": ".r (Reply qilingan xabardan quote stiker)",
    ".catbox": ".catbox (Faylga reply qilib yuklash)",
    ".envs": ".envs (Faylga reply qilib envs.sh ga yuklash)",
    ".0x0": ".0x0 (Faylga reply qilib 0x0.st ga yuklash)",
    ".tmpfiles": ".tmpfiles (Faylga reply qilib tmpfiles ga yuklash)",
    ".me": ".me qahva ichmoqda",
    ".do": ".do Xonada chiroq yandi",
    ".try": ".try Kalit bilan eshikni ochish",
    ".todo": ".todo Xat yozish | pochtaga tashlash",
    ".ro": ".ro (Rus ruletkasi o'yini)",
    ".roulette": ".roulette (Rus ruletkasi)",
    ".ping": ".ping (Bot tezligini tekshirish)",
    ".co": ".co (Barcha buyruqlar va modullar)",
    ".func": ".func (Barcha modullar)",
    ".komandalar": ".komandalar (Barcha buyruqlar)"
}

class PluginManager:
    def __init__(self):
        self.commands: Dict[str, Callable] = {}

    def register_command(self, cmd_name: str, handler: Callable):
        self.commands[cmd_name.lower()] = handler
        logger.info(f"Registered plugin command: {cmd_name}")

    def load_plugins(self, package_name: str = "app.plugins.modules"):
        try:
            package = importlib.import_module(package_name)
        except Exception as e:
            logger.warning(f"Could not import plugin package {package_name}: {e}")
            return

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            full_name = f"{package_name}.{module_name}"
            try:
                mod = importlib.import_module(full_name)
                if hasattr(mod, "register"):
                    mod.register(self)
                logger.info(f"Loaded plugin module: {module_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {module_name}: {e}", exc_info=True)

    def get_suggestion(self, cmd_name: str) -> Optional[Tuple[str, str]]:
        cmd = cmd_name.lower().strip()
        all_cmds = list(self.commands.keys()) + [
            ".love", ".snow", ".xd", ".police", ".kill", ".ari", ".load",
            ".god", ".snake", ".ghost", ".cosmo", ".knife", ".chaqmoq",
            ".home", ".ayriliq", ".puq", ".money", ".search", ".dance",
            ".yurak", ".fuck", ".ping", ".help"
        ]
        matches = difflib.get_close_matches(cmd, all_cmds, n=1, cutoff=0.4)
        if matches:
            suggested = matches[0]
            usage = COMMAND_USAGE.get(suggested, f"{suggested}")
            return suggested, usage
        return None

    async def dispatch(self, cmd_name: str, bot: Bot, message: types.Message, conn_id: str, args: str) -> bool:
        handler = self.commands.get(cmd_name.lower())
        if handler:
            try:
                await handler(bot, message, conn_id, args)
            except Exception as e:
                logger.error(f"Error executing plugin command {cmd_name}: {e}", exc_info=True)
                try:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=f"🚫 '{cmd_name}' buyrug'ida xatolik yuz berdi: {e}",
                        business_connection_id=conn_id,
                        parse_mode=None
                    )
                except Exception:
                    pass
            return True
        return False

plugin_manager = PluginManager()
