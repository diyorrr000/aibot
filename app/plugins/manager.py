import importlib
import logging
import pkgutil
from typing import Dict, Any, Callable
from aiogram import Bot, types
from app.utils.logger import logger

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
