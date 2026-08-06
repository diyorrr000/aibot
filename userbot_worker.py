from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from config import API_ID, API_HASH
from plugins.commands import setup_commands
from plugins.animations import setup_animations
from plugins.auto_settings import setup_auto_settings
from plugins.quotes import setup_quotes
from plugins.baza import setup_baza
from plugins.reactions import setup_reactions
from plugins.plugins_manager import setup_plugins_manager
from plugins.read_file import setup_read_file
from plugins.downloader import setup_downloader
from plugins.ai_module import setup_ai
from plugins.account_info import setup_account_info
from plugins.gender_guesser import setup_gender_guesser
from plugins.uploader import setup_uploader
from plugins.roulette import setup_roulette
from plugins.shortlink import setup_shortlink
from plugins.yt_search import setup_yt_search
from plugins.text2speech import setup_text2speech
from plugins.telegraph import setup_telegraph
from plugins.random_memes import setup_random_memes
from plugins.weather import setup_weather
from plugins.auto_ad import setup_auto_ad
from plugins.translator import setup_translator
from plugins.currency import setup_currency
from plugins.quote import setup_quote
from plugins.lyrics import setup_lyrics
from plugins.roleplay import setup_roleplay
from plugins.clock import setup_clock
from plugins.character_tts import setup_character_tts
from plugins.timer import setup_timer
from plugins.anime import setup_anime
from plugins.anime_arts import setup_anime_arts
import asyncio

RUNNING_CLIENTS = {}

class UserBotTask:
    def __init__(self, user_id, session_string):
        self.user_id = user_id
        self.session_string = session_string
        self.client = TelegramClient(StringSession(session_string), API_ID, API_HASH)

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print(f"User {self.user_id} is not authorized.")
            return

        print(f"UserBot started for {self.user_id}")
        RUNNING_CLIENTS[self.user_id] = self.client
        
        # Setup plugins
        await setup_commands(self.client)
        await setup_animations(self.client)
        await setup_auto_settings(self.client, self.user_id)
        await setup_quotes(self.client)
        await setup_baza(self.client)
        await setup_reactions(self.client)
        await setup_plugins_manager(self.client)
        await setup_read_file(self.client)
        await setup_downloader(self.client)
        await setup_ai(self.client)
        await setup_account_info(self.client)
        await setup_gender_guesser(self.client)
        await setup_uploader(self.client)
        await setup_roulette(self.client)
        await setup_shortlink(self.client)
        await setup_yt_search(self.client)
        await setup_text2speech(self.client)
        await setup_telegraph(self.client)
        await setup_random_memes(self.client)
        await setup_weather(self.client)
        await setup_auto_ad(self.client)
        await setup_translator(self.client)
        await setup_currency(self.client)
        await setup_quote(self.client)
        await setup_lyrics(self.client)
        await setup_roleplay(self.client)
        await setup_clock(self.client)
        await setup_character_tts(self.client)
        await setup_timer(self.client)
        await setup_anime(self.client)
        await setup_anime_arts(self.client)
        
        # New user welcome message in Saved Messages
        try:
            welcome_text = """<b>😎 DICO USERBOT muvaffaqiyatli ulandi!

Barcha buyruqlarni ko'rish uchun quyidagilarni ishlating:

.help - 🖥 Asosiy buyruqlar ro'yxati
.co - 🎭 Barcha modullar va animatsiyalar
.ping - 🚀 Bot tezligi

Botdan foydalanishni boshlashingiz mumkin!</b>"""
            await self.client.send_message("me", welcome_text, parse_mode='html')
        except:
            pass
        
        # Keep online safely with anti-ban delay
        async def online_loop():
            from storage import is_clock_enabled
            from services.ban_protection import ban_guard
            while True:
                try:
                    await ban_guard.random_sleep(45.0, 75.0)
                    if is_clock_enabled():
                        await ban_guard.safe_execute(
                            self.client(functions.account.UpdateStatusRequest(offline=False))
                        )
                except Exception:
                    pass

        asyncio.create_task(online_loop())

        # Run until disconnected
        await self.client.run_until_disconnected()

async def start_userbot(user_id, session_string):
    ub = UserBotTask(user_id, session_string)
    await ub.start()

async def stop_userbot(user_id):
    if user_id in RUNNING_CLIENTS:
        client = RUNNING_CLIENTS[user_id]
        try:
            await client.disconnect()
        except: pass
        if user_id in RUNNING_CLIENTS:
            del RUNNING_CLIENTS[user_id]
        return True
    return False
