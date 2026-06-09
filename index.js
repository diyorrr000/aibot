import 'dotenv/config';
import { Telegraf } from 'telegraf';
import { GoogleGenAI } from '@google/genai';
import http from 'http';

// Verify environment variables
if (!process.env.TELEGRAM_BOT_TOKEN) {
  console.error('ERROR: TELEGRAM_BOT_TOKEN is missing in the environment variables!');
  process.exit(1);
}
if (!process.env.GEMINI_API_KEY) {
  console.error('ERROR: GEMINI_API_KEY is missing in the environment variables!');
  process.exit(1);
}

// Initialize Telegraf bot
const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN);

// Initialize Gemini client
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const DEFAULT_MODEL = process.env.GEMINI_MODEL || 'gemini-2.5-flash-lite';

// In-memory store for user settings
// Key: chatId, Value: { model: string, grounding: boolean }
const userSettings = new Map();

function getUserSettings(chatId) {
  if (!userSettings.has(chatId)) {
    userSettings.set(chatId, {
      model: DEFAULT_MODEL,
      grounding: false
    });
  }
  return userSettings.get(chatId);
}

// Model information & display names
const MODELS_INFO = {
  'gemini-2.5-flash-lite': {
    name: 'Gemini 2.5 Flash Lite',
    description: "⚡ *Gemini 2.5 Flash Lite*\n\n" +
      "Bu model tezkorlik va tejamkorlik uchun maxsus ishlab chiqilgan.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Oddiy matnli savol-javoblar uchun eng maqbul tanlov.\n" +
      "- Juda tezkor javob qaytaradi va resurslarni tejaydi.\n" +
      "- Kundalik muloqot va tezkor vazifalarga mo'ljallangan."
  },
  'gemini-2.5-flash': {
    name: 'Gemini 2.5 Flash',
    description: "🚀 *Gemini 2.5 Flash*\n\n" +
      "Tezlik va sifat o'rtasidagi oltin muvozanatga ega bo'lgan model.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Keng ko'lamli matnlarni tahlil qilish va umumlashtirish.\n" +
      "- Savollarga tez va to'liq javob berish.\n" +
      "- Tarjimalar va ijodiy yozishmalar."
  },
  'gemini-2.5-pro': {
    name: 'Gemini 2.5 Pro',
    description: "🧠 *Gemini 2.5 Pro*\n\n" +
      "Murakkab mantiqiy fikrlash va yuqori sifatli javoblar uchun eng kuchli model.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Dasturlash kodlarini yozish va tahlil qilish (coding).\n" +
      "- Murakkab mantiqiy va matematik masalalar.\n" +
      "- Chuqur tahliliy maqolalar va ma'lumotlarni qayta ishlash."
  },
  'gemini-2.0-flash': {
    name: 'Gemini 2.0 Flash',
    description: "🌟 *Gemini 2.0 Flash*\n\n" +
      "Ikkinchi avlodning muvozanatlashgan, tezkor va aqlli modeli.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Matnli va kontekstual topshiriqlarni yuqori darajada tushunish.\n" +
      "- Barqarorlik va yuqori ishlash tezligi."
  },
  'gemini-2.0-flash-lite': {
    name: 'Gemini 2.0 Flash Lite',
    description: "🍃 *Gemini 2.0 Flash Lite*\n\n" +
      "Ikkinchi avlodning eng yengil va tezkor modeli.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Kichik hajmdagi va tezkor javob talab qiluvchi so'rovlar.\n" +
      "- Tejamkor va samarali suhbatlar."
  },
  'gemini-3.1-flash-lite': {
    name: 'Gemini 3.1 Flash Lite',
    description: "💎 *Gemini 3.1 Flash Lite*\n\n" +
      "Uchinchi avlod oilasining eng yangi, yengil va zamonaviy modeli.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Yuqori aniqlik va yaxshilangan mantiqiy tushunish darajasi.\n" +
      "- Yaxshilangan ishlash tezligi va yangilangan ma'lumotlar bazasi."
  },
  'gemini-3.5-flash': {
    name: 'Gemini 3.5 Flash',
    description: "🔥 *Gemini 3.5 Flash*\n\n" +
      "Eng so'nggi avlodning (3.5) ilg'or va eng zamonaviy modeli.\n\n" +
      "✨ *Imkoniyatlari va vazifalari:*\n" +
      "- Eng zamonaviy matnni tahlil qilish va umumlashtirish.\n" +
      "- Yuqori sifatli va mantiqan to'g'ri javoblar.\n" +
      "- Murakkab muloqot va yuqori samaradorlik."
  }
};

// Function to generate the main settings menu keyboard
function getSettingsKeyboard(settings) {
  const groundingText = settings.grounding ? '✅ Yoqilgan' : '❌ O\'chirilgan';
  
  return {
    inline_keyboard: [
      [
        { text: '🤖 Modelni almashtirish', callback_data: 'menu_models' }
      ],
      [
        { text: `🔍 Grounding (Search/Maps): ${groundingText}`, callback_data: 'toggle_grounding' }
      ],
      [
        { text: '❌ Yopish', callback_data: 'close_settings' }
      ]
    ]
  };
}

// Function to generate the main settings text
function getSettingsText(settings) {
  const modelInfo = MODELS_INFO[settings.model] || { name: settings.model };
  const groundingStatus = settings.grounding ? 'Yoqilgan' : 'O\'chirilgan';
  
  return `⚙️ *Sozlamalar paneli*\n\n` +
    `🤖 *Faol model:* ${modelInfo.name}\n` +
    `🔍 *Google Search & Maps Grounding:* ${groundingStatus}\n\n` +
    `Quyidagi tugmalar orqali sozlamalarni o'zgartirishingiz mumkin:`;
}

// Function to generate the models selection keyboard
function getModelsKeyboard() {
  const buttons = Object.keys(MODELS_INFO).map(key => [
    { text: MODELS_INFO[key].name, callback_data: `set_model:${key}` }
  ]);
  
  // Add Back button
  buttons.push([{ text: '⬅️ Orqaga', callback_data: 'menu_main' }]);
  
  return { inline_keyboard: buttons };
}

// In-memory store for chat history
// Key: chatId, Value: Array of { role: 'user' | 'model', text: string }
const chatHistories = new Map();
const MAX_HISTORY_LENGTH = 20; // Keep last 20 messages for context

// Helper to get or initialize chat history
function getChatHistory(chatId) {
  if (!chatHistories.has(chatId)) {
    chatHistories.set(chatId, []);
  }
  return chatHistories.get(chatId);
}

// Helper to add message to history
function addToHistory(chatId, role, text) {
  const history = getChatHistory(chatId);
  history.push({ role, text });
  // Trim history if it exceeds limit
  if (history.length > MAX_HISTORY_LENGTH) {
    history.shift();
  }
}

// Helper to call generateContent with retry on 503/429
async function generateContentWithRetry(ai, model, contents, config, retries = 3, delay = 1000) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await ai.models.generateContent({
        model,
        contents,
        config,
      });
      return response;
    } catch (error) {
      const isTemporary = error.status === 503 || error.status === 429 || (error.message && (error.message.includes('503') || error.message.includes('high demand') || error.message.includes('429')));
      if (isTemporary && i < retries - 1) {
        console.warn(`Gemini API call failed with temporary error. Retrying in ${delay}ms... (Attempt ${i + 1}/${retries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2;
        continue;
      }
      throw error;
    }
  }
}

// Welcome message (/start)
bot.start((ctx) => {
  const chatId = ctx.chat.id;
  chatHistories.set(chatId, []); // Reset history on start
  
  const welcomeText = `👋 Assalomu alaykum, *${ctx.from.first_name || 'do\'stim'}*!\n\n` +
    `Men Gemini modellar oilasi bilan ishlaydigan aqlli yordamchiman. 🚀\n\n` +
    `✨ *Asosiy imkoniyatlar:*\n` +
    `- Sozlamalar menyusi (/settings) orqali turli Gemini modellarini (2.5, 2.0, 3.1, 3.5) tanlashingiz mumkin.\n` +
    `- Google Search & Maps Grounding funksiyasi orqali real vaqtda internetdan ma'lumot olishingiz mumkin.\n\n` +
    `⚙️ *Sozlash uchun:* /settings yozing.\n` +
    `🧹 *Suhbat tarixini o'chirish uchun:* /reset yozing.\n` +
    `ℹ️ *Yordam olish uchun:* /help yozing.`;

  ctx.replyWithMarkdown(welcomeText);
});

// Help command (/help)
bot.help((ctx) => {
  const helpText = `📖 *Bot Yo'riqnomasi:*\n\n` +
    `1. Savolingizni oddiy matn ko'rinishida yozib yuboring.\n` +
    `2. Bot siz tanlagan model yordamida javob qaytaradi va suhbat tarixini eslab qoladi.\n` +
    `3. Modelni yoki qidiruv (Search/Maps) grounding funksiyasini yoqish uchun /settings buyrug'ini ishlating.\n` +
    `4. Muloqotni yangidan boshlamoqchi bo'lsangiz, /reset buyrug'ini yuboring.`;
  
  ctx.replyWithMarkdown(helpText);
});

// Settings command (/settings)
bot.command('settings', (ctx) => {
  const chatId = ctx.chat.id;
  const settings = getUserSettings(chatId);
  ctx.replyWithMarkdown(getSettingsText(settings), {
    reply_markup: getSettingsKeyboard(settings)
  });
});

// Reset command (/reset)
bot.command('reset', (ctx) => {
  const chatId = ctx.chat.id;
  chatHistories.set(chatId, []);
  ctx.reply('🧹 Suhbat tarixi muvaffaqiyatli tozalandi! Yangi savol yuborishingiz mumkin.');
});

// Callback query dispatcher
bot.on('callback_query', async (ctx) => {
  const chatId = ctx.chat.id;
  const data = ctx.callbackQuery.data;
  const settings = getUserSettings(chatId);

  try {
    if (data === 'menu_main') {
      await ctx.editMessageText(getSettingsText(settings), {
        parse_mode: 'Markdown',
        reply_markup: getSettingsKeyboard(settings)
      });
    } else if (data === 'menu_models') {
      await ctx.editMessageText('🤖 *Kerakli modelni tanlang:*', {
        parse_mode: 'Markdown',
        reply_markup: getModelsKeyboard()
      });
    } else if (data === 'toggle_grounding') {
      settings.grounding = !settings.grounding;
      await ctx.editMessageText(getSettingsText(settings), {
        parse_mode: 'Markdown',
        reply_markup: getSettingsKeyboard(settings)
      });
    } else if (data === 'close_settings') {
      await ctx.deleteMessage().catch(() => {});
    } else if (data.startsWith('set_model:')) {
      const selectedModel = data.split(':')[1];
      if (MODELS_INFO[selectedModel]) {
        settings.model = selectedModel;
        
        const info = MODELS_INFO[selectedModel];
        const infoText = `${info.description}\n\n` +
          `✅ *Ushbu model faollashtirildi!*`;
          
        await ctx.editMessageText(infoText, {
          parse_mode: 'Markdown',
          reply_markup: {
            inline_keyboard: [
              [
                { text: '⬅️ Model ro\'yxati', callback_data: 'menu_models' },
                { text: '⚙️ Bosh menyu', callback_data: 'menu_main' }
              ]
            ]
          }
        });
      }
    }
    
    // Answer callback query to stop loading state on the button
    await ctx.answerCbQuery().catch(() => {});
  } catch (err) {
    console.error('Error in callback query handling:', err);
    await ctx.answerCbQuery('Xatolik yuz berdi. Iltimos qayta urinib ko\'ring.').catch(() => {});
  }
});

// Handle incoming text messages
bot.on('text', async (ctx) => {
  const chatId = ctx.chat.id;
  const userMessage = ctx.message.text;
  const settings = getUserSettings(chatId);

  // Send typing action to Telegram
  try {
    await ctx.sendChatAction('typing');
  } catch (err) {
    console.error('Failed to send typing chat action:', err);
  }

  // Retrieve existing history
  const history = getChatHistory(chatId);

  // Format history for Gemini API
  const contents = history.map(item => ({
    role: item.role,
    parts: [{ text: item.text }]
  }));

  // Add the current user message to contents
  contents.push({
    role: 'user',
    parts: [{ text: userMessage }]
  });

  // Keep a typing indicator active if response takes longer
  const intervalId = setInterval(() => {
    ctx.sendChatAction('typing').catch(() => {});
  }, 4000);

  try {
    // Call Gemini API with retry mechanism
    const response = await generateContentWithRetry(
      ai,
      settings.model,
      contents,
      {
        thinkingConfig: {
          thinkingBudget: 0
        },
        tools: settings.grounding ? [{ googleSearch: {} }] : undefined,
        systemInstruction: 
          "You are a helpful and polite assistant. You must write and respond exclusively in the Uzbek language. " +
          "In your responses, NEVER use bold markdown formatting (do not use **). Keep the text beautiful, " +
          "elegant, and readable by separating key ideas using newlines, bullet points, or lists. " +
          "When you write or show code, always wrap it inside standard code blocks (using triple backticks) " +
          "to format it properly. All explanations, comments, and replies must be fully in Uzbek. " +
          "Do not output any thinking process, reasoning, thoughts, or internal chain-of-thought blocks."
      }
    );

    clearInterval(intervalId);

    const botResponse = response.text;

    if (!botResponse) {
      throw new Error('Empty response received from Gemini API');
    }

    // Save to history
    addToHistory(chatId, 'user', userMessage);
    addToHistory(chatId, 'model', botResponse);

    // Reply to user (Markdown format supported by Gemini is compatible with MarkdownV2 or Markdown)
    try {
      await ctx.reply(botResponse, { parse_mode: 'Markdown' });
    } catch (markdownError) {
      console.warn('Failed to send response with Markdown formatting, falling back to plain text:', markdownError);
      await ctx.reply(botResponse);
    }

  } catch (error) {
    clearInterval(intervalId);
    console.error('Error in handling message:', error);
    const isQuotaExceeded = error.status === 429 || (error.message && (error.message.includes('429') || error.message.includes('quota') || error.message.includes('Limit exceeded') || error.message.includes('RESOURCE_EXHAUSTED')));
    if (isQuotaExceeded) {
      ctx.reply('⚠️ Bepul so\'rovlar limiti tugadi! Siz foydalanayotgan model uchun bepul API kalitning kunlik yoki daqiqalik limiti tugagan bo\'lishi mumkin.\n\n👉 /settings buyrug\'i orqali boshqa modelni tanlab ko\'ring yoki biroz kutib qayta urining.');
    } else {
      ctx.reply('⚠️ Kechirasiz, so\'rovingizni qayta ishlashda xatolik yuz berdi. Iltimos, birozdan so\'ng qayta urinib ko\'ring.');
    }
  }
});

// Create a simple HTTP server for Render health checks (keeps Web Service active)
const PORT = process.env.PORT || 3000;
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Bot is running!');
});

server.listen(PORT, () => {
  console.log(`Health check server is listening on port ${PORT}`);
});

// Launch bot
bot.launch()
  .then(() => {
    console.log('🤖 Telegram bot has been started successfully with multi-model support!');
    console.log(`Default model: ${DEFAULT_MODEL}`);
  })
  .catch((err) => {
    console.error('Failed to start Telegram bot:', err);
    process.exit(1);
  });

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
