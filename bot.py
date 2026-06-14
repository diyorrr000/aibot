import os
import io
import asyncio
import http.server
import socketserver
import threading
from PIL import Image
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types
import easyocr

# Load environment variables
load_dotenv()

# Verify credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("CRITICAL ERROR: TELEGRAM_BOT_TOKEN or GEMINI_API_KEY is missing!")
    exit(1)

# Initialize Telegram bot
bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize EasyOCR reader for English and Russian
print("Initializing EasyOCR reader (en, ru)...")
reader = easyocr.Reader(['en', 'ru'])
print("EasyOCR reader successfully initialized!")

# In-memory settings and history stores
user_settings = {}
chat_histories = {}
MAX_HISTORY_LENGTH = 20

def get_user_settings(chat_id):
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            "model": DEFAULT_MODEL,
            "grounding": False
        }
    return user_settings[chat_id]

def get_chat_history(chat_id):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    return chat_histories[chat_id]

def add_to_history(chat_id, role, text):
    history = get_chat_history(chat_id)
    history.append({"role": role, "text": text})
    if len(history) > MAX_HISTORY_LENGTH:
        history.pop(0)

# Model definitions and descriptions
MODELS_INFO = {
    'gemini-2.5-flash-lite': {
        'name': 'Gemini 2.5 Flash Lite',
        'desc': "⚡ *Gemini 2.5 Flash Lite*\n\nTezkorlik va tejamkorlik uchun maxsus ishlab chiqilgan yengil model.\n\n✨ *Imkoniyatlari:*\n- Oddiy matnli savol-javoblar uchun eng maqbul tanlov.\n- Tezkor javob qaytaradi."
    },
    'gemini-2.5-flash': {
        'name': 'Gemini 2.5 Flash',
        'desc': "🚀 *Gemini 2.5 Flash*\n\nTezlik va sifat muvozanatiga ega universal model.\n\n✨ *Imkoniyatlari:*\n- Matnlarni tahlil qilish va umumlashtirish.\n- Savollarga tez va to'liq javob berish."
    },
    'gemini-2.5-pro': {
        'name': 'Gemini 2.5 Pro',
        'desc': "🧠 *Gemini 2.5 Pro*\n\nMurakkab mantiqiy fikrlash va eng yuqori sifatli javoblar uchun kuchli model.\n\n✨ *Imkoniyatlari:*\n- Dasturlash kodlarini yozish va tahlil qilish.\n- Murakkab mantiqiy va matematik masalalar."
    },
    'gemini-2.0-flash': {
        'name': 'Gemini 2.0 Flash',
        'desc': "🌟 *Gemini 2.0 Flash*\n\nIkkinchi avlodning tezkor va sifatli modeli.\n\n✨ *Imkoniyatlari:*\n- Kontekstual vazifalarni yuqori darajada tushunish.\n- Barqaror ishlash tezligi."
    },
    'gemini-2.0-flash-lite': {
        'name': 'Gemini 2.0 Flash Lite',
        'desc': "🍃 *Gemini 2.0 Flash Lite*\n\nIkkinchi avlodning yengillashtirilgan va tezkor varianti.\n\n✨ *Imkoniyatlari:*\n- Kichik hajmdagi va tezkor javob talab qiluvchi so'rovlar."
    },
    'gemini-3.1-flash-lite': {
        'name': 'Gemini 3.1 Flash Lite',
        'desc': "💎 *Gemini 3.1 Flash Lite*\n\nUchinchi avlod oilasining eng yangi va zamonaviy yengil modeli.\n\n✨ *Imkoniyatlari:*\n- Yuqori aniqlik va yaxshilangan mantiqiy tushunish darajasi."
    },
    'gemini-3.5-flash': {
        'name': 'Gemini 3.5 Flash',
        'desc': "🔥 *Gemini 3.5 Flash*\n\nEng so'nggi avlodning ilg'or va eng zamonaviy modeli.\n\n✨ *Imkoniyatlari:*\n- Ilg'or tushunish, tahlil qilish va yuqori samaradorlik."
    }
}

# Keyboards for settings menu
def get_settings_keyboard(settings):
    grounding_status = '✅ Yoqilgan' if settings['grounding'] else '❌ O\'chirilgan'
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🤖 Modelni almashtirish", callback_data="menu_models"))
    markup.row(InlineKeyboardButton(f"🔍 Grounding: {grounding_status}", callback_data="toggle_grounding"))
    markup.row(InlineKeyboardButton("❌ Yopish", callback_data="close_settings"))
    return markup

def get_settings_text(settings):
    active_model = MODELS_INFO.get(settings['model'], {}).get('name', settings['model'])
    grounding_status = 'Yoqilgan' if settings['grounding'] else 'O\'chirilgan'
    return (
        f"⚙️ *Sozlamalar paneli*\n\n"
        f"🤖 *Faol model:* {active_model}\n"
        f"🔍 *Google Search & Maps Grounding:* {grounding_status}\n\n"
        f"Quyidagi tugmalar orqali sozlamalarni o'zgartirishingiz mumkin:"
    )

def get_models_keyboard():
    markup = InlineKeyboardMarkup()
    for key, info in MODELS_INFO.items():
        markup.row(InlineKeyboardButton(info['name'], callback_data=f"set_model:{key}"))
    markup.row(InlineKeyboardButton("⬅️ Orqaga", callback_data="menu_main"))
    return markup

# HTTP Health check server for Render compatibility
def run_health_check_server():
    PORT = int(os.getenv("PORT", 3000))
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot is running!")
            
        def log_message(self, format, *args):
            pass

    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        print(f"Health check server is listening on port {PORT}")
        httpd.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

# Image optimization helper
def optimize_image(image_bytes, max_size=1280):
    img = Image.open(io.BytesIO(image_bytes))
    
    # Handle transparency
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.convert("RGBA").split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    width, height = img.size
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
    out_io = io.BytesIO()
    img.save(out_io, format="JPEG", quality=85)
    return out_io.getvalue()

# Gemini API call helper with retry and error handling
async def generate_content_with_retry(model, contents, config, retries=3, delay=1.0):
    for i in range(retries):
        try:
            response = await ai_client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response
        except Exception as error:
            # Check for temporary 503 or 429 errors
            error_msg = str(error)
            is_temporary = "503" in error_msg or "429" in error_msg or "high demand" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
            if is_temporary and i < retries - 1:
                print(f"Gemini API call failed temporarily. Retrying in {delay}s... (Attempt {i + 1}/{retries})")
                await asyncio.sleep(delay)
                delay *= 2
                continue
            raise error

# Welcome command (/start)
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    chat_id = message.chat.id
    chat_histories[chat_id] = []
    
    welcome_text = (
        f"👋 Assalomu alaykum, *{message.from_user.first_name or 'do\'stim'}*!\n\n"
        f"Men Gemini modellar oilasi va EasyOCR bilan ishlaydigan aqlli yordamchiman. 🚀\n\n"
        f"✨ *Asosiy imkoniyatlar:*\n"
        f"- Matnli xabarlarga javob berish.\n"
        f"- *OCR (Rasm tahlili):* Matnli rasm yuboring, men matnni o'qib, o'zbekcha imloni tuzataman va savol/masalaga javob beraman.\n"
        f"- Sozlamalar menyusi (/settings) orqali turli Gemini modellarini tanlash va Google Search grounding yoqish.\n\n"
        f"⚙️ *Sozlash uchun:* /settings yozing.\n"
        f"🧹 *Tarixni tozalash:* /reset yozing.\n"
        f"ℹ️ *Yordam:* /help yozing."
    )
    await bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

# Help command (/help)
@bot.message_handler(commands=['help'])
async def send_help(message):
    help_text = (
        f"📖 *Yo'riqnoma:*\n\n"
        f"1. Oddiy savollarni matn sifatida yuboring.\n"
        f"2. Matnli kitob sahifasi, masala yoki savolli rasm yuboring, bot OCR yordamida uni o'qiydi va Gemini orqali javob beradi.\n"
        f"3. Modelni o'zgartirish yoki real vaqtda internet qidiruvini yoqish uchun /settings buyrug'idan foydalaning.\n"
        f"4. Suhbat tarixini yangilash uchun /reset yozing."
    )
    await bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# Reset command (/reset)
@bot.message_handler(commands=['reset'])
async def reset_history(message):
    chat_id = message.chat.id
    chat_histories[chat_id] = []
    await bot.send_message(chat_id, "🧹 Suhbat tarixi muvaffaqiyatli tozalandi! Yangi savol yuborishingiz mumkin.")

# Settings command (/settings)
@bot.message_handler(commands=['settings'])
async def show_settings(message):
    chat_id = message.chat.id
    settings = get_user_settings(chat_id)
    await bot.send_message(
        chat_id, 
        get_settings_text(settings), 
        parse_mode="Markdown", 
        reply_markup=get_settings_keyboard(settings)
    )

# Callback queries for settings menu
@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    settings = get_user_settings(chat_id)
    
    try:
        if data == 'menu_main':
            await bot.edit_message_text(
                get_settings_text(settings),
                chat_id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=get_settings_keyboard(settings)
            )
        elif data == 'menu_models':
            await bot.edit_message_text(
                "🤖 *Kerakli modelni tanlang:*",
                chat_id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=get_models_keyboard()
            )
        elif data == 'toggle_grounding':
            settings['grounding'] = not settings['grounding']
            await bot.edit_message_text(
                get_settings_text(settings),
                chat_id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=get_settings_keyboard(settings)
            )
        elif data == 'close_settings':
            await bot.delete_message(chat_id, call.message.message_id)
        elif data.startswith('set_model:'):
            selected_model = data.split(':')[1]
            if selected_model in MODELS_INFO:
                settings['model'] = selected_model
                info = MODELS_INFO[selected_model]
                info_text = f"{info['desc']}\n\n✅ *Ushbu model faollashtirildi!*"
                
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("⬅️ Ro'yxatga qaytish", callback_data="menu_models"),
                    InlineKeyboardButton("⚙️ Bosh menyu", callback_data="menu_main")
                )
                await bot.edit_message_text(
                    info_text,
                    chat_id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
        
        await bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Error handling callback: {e}")
        await bot.answer_callback_query(call.id, "Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

# Handle image uploads (OCR + Gemini)
@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    chat_id = message.chat.id
    settings = get_user_settings(chat_id)
    
    # Send initial status
    status_msg = await bot.send_message(chat_id, "🔍 Rasm tahlil qilinmoqda, iltimos kuting...")
    
    try:
        # 1. Download file
        file_info = await bot.get_file(message.photo[-1].file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        # 2. Optimize image (resizing large files to save RAM/Time)
        optimized_bytes = optimize_image(file_bytes)
        
        # 3. Extract text using EasyOCR (running synchronous block in executor to prevent freezing async loop)
        loop = asyncio.get_event_loop()
        ocr_text = await loop.run_in_executor(None, lambda: "\n".join(reader.readtext(optimized_bytes, detail=0)))
        
        if not ocr_text.strip():
            await bot.edit_message_text("⚠️ Rasmdan hech qanday matn aniqlanmadi. Iltimos, sifatliroq rasm yuboring.", chat_id, status_msg.message_id)
            return
        
        # 4. Prepare prompt with Uzbek o' and g' character recovery and analysis instruction
        prompt = (
            f"Quyidagi matn rasmdan OCR (matn aniqlash) orqali olingan.\n"
            f"Matnda nimalar yozilganini va bu matn/rasm aslida nima haqida ekanini (uning ma'nosi, mohiyati va tarkibini) to'liq tahlil qilib o'zbek tilida tushuntirib ber.\n"
            f"O'zbek tilidagi imlo va OCR xatolarini tuzat, ayniqsa o' va g' harflari uchun noto'g'ri o'qilgan belgilarni to'g'rilab tikla.\n"
            f"Agar matnda biron bir savol, topshiriq yoki masala bo'lsa, unga ham to'liq va aniq javob ber.\n\n"
            f"OCR MATN:\n"
            f"{ocr_text}"
        )
        
        # 5. Send to Gemini
        # Prepare Config
        thinking_config = None
        if "gemini-2.5" in settings['model']:
            thinking_config = types.ThinkingConfig(thinking_budget=0)
        elif "gemini-3" in settings['model']:
            thinking_config = types.ThinkingConfig(thinking_level="MINIMAL")

        tools = [types.Tool(google_search=types.GoogleSearch())] if settings['grounding'] else None
        
        config = types.GenerateContentConfig(
            thinking_config=thinking_config,
            tools=tools,
            system_instruction=(
                "You are a helpful and polite assistant. You must write and respond exclusively in the Uzbek language. "
                "In your responses, NEVER use bold markdown formatting (do not use **). Keep the text beautiful, "
                "elegant, and readable by separating key ideas using newlines, bullet points, or lists. "
                "When you write or show code, always wrap it inside standard code blocks (using triple backticks) "
                "to format it properly. All explanations, comments, and replies must be fully in Uzbek. "
                "Do not output any thinking process, reasoning, thoughts, or internal chain-of-thought blocks."
            )
        )
        
        # Call API
        response = await generate_content_with_retry(
            model=settings['model'],
            contents=prompt,
            config=config
        )
        
        bot_response = response.text
        if not bot_response:
            raise Error("Empty response from Gemini API")
            
        # 6. Return response to user
        await bot.delete_message(chat_id, status_msg.message_id)
        
        try:
            await bot.send_message(chat_id, bot_response, parse_mode="Markdown")
        except Exception as markdown_error:
            print(f"Markdown format error, falling back to plain text: {markdown_error}")
            await bot.send_message(chat_id, bot_response)
            
    except Exception as e:
        print(f"Error handling photo: {e}")
        await bot.delete_message(chat_id, status_msg.message_id)
        
        # Quota/API error check
        error_msg = str(e)
        is_quota = "429" in error_msg or "quota" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
        if is_quota:
            await bot.send_message(chat_id, "⚠️ Bepul so'rovlar limiti tugadi! Siz foydalanayotgan model uchun bepul API kalitning limiti tugagan bo'lishi mumkin.\n\n👉 /settings buyrug'i orqali boshqa modelni tanlab ko'ring yoki biroz kutib qayta urining.")
        else:
            await bot.send_message(chat_id, "⚠️ Rasmni qayta ishlashda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring.")

# Handle text messages
@bot.message_handler(content_types=['text'])
async def handle_text(message):
    chat_id = message.chat.id
    user_message = message.text
    settings = get_user_settings(chat_id)
    
    # Send typing status
    await bot.send_chat_action(chat_id, 'typing')
    
    # Get and format history
    history = get_chat_history(chat_id)
    contents = []
    for item in history:
        contents.append(types.Content(
            role=item['role'],
            parts=[types.Part.from_text(text=item['text'])]
        ))
    
    # Add new message
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)]
    ))
    
    try:
        # Prepare Config
        thinking_config = None
        if "gemini-2.5" in settings['model']:
            thinking_config = types.ThinkingConfig(thinking_budget=0)
        elif "gemini-3" in settings['model']:
            thinking_config = types.ThinkingConfig(thinking_level="MINIMAL")

        tools = [types.Tool(google_search=types.GoogleSearch())] if settings['grounding'] else None
        
        config = types.GenerateContentConfig(
            thinking_config=thinking_config,
            tools=tools,
            system_instruction=(
                "You are a helpful and polite assistant. You must write and respond exclusively in the Uzbek language. "
                "In your responses, NEVER use bold markdown formatting (do not use **). Keep the text beautiful, "
                "elegant, and readable by separating key ideas using newlines, bullet points, or lists. "
                "When you write or show code, always wrap it inside standard code blocks (using triple backticks) "
                "to format it properly. All explanations, comments, and replies must be fully in Uzbek. "
                "Do not output any thinking process, reasoning, thoughts, or internal chain-of-thought blocks."
            )
        )
        
        # Call API
        response = await generate_content_with_retry(
            model=settings['model'],
            contents=contents,
            config=config
        )
        
        bot_response = response.text
        if not bot_response:
            raise Error("Empty response from Gemini API")
            
        # Save to history
        add_to_history(chat_id, "user", user_message)
        add_to_history(chat_id, "model", bot_response)
        
        # Reply to user
        try:
            await bot.send_message(chat_id, bot_response, parse_mode="Markdown")
        except Exception as markdown_error:
            print(f"Markdown format error, falling back to plain text: {markdown_error}")
            await bot.send_message(chat_id, bot_response)
            
    except Exception as e:
        print(f"Error handling text: {e}")
        # Quota/API error check
        error_msg = str(e)
        is_quota = "429" in error_msg or "quota" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
        if is_quota:
            await bot.send_message(chat_id, "⚠️ Bepul so'rovlar limiti tugadi! Siz foydalanayotgan model uchun bepul API kalitning limiti tugagan bo'lishi mumkin.\n\n👉 /settings buyrug'i orqali boshqa modelni tanlab ko'ring yoki biroz kutib qayta urining.")
        else:
            await bot.send_message(chat_id, "⚠️ Kechirasiz, so'rovingizni qayta ishlashda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring.")

# Main launch
if __name__ == '__main__':
    print("🤖 Telegram bot is starting in Python...")
    import asyncio
    asyncio.run(bot.polling(non_stop=True))
