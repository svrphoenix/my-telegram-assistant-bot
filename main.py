import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, PicklePersistence
)

from config import config
from baseai import BaseAIService
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu, load_prompt, get_ai_reply)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="bot_data.pickle")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f'Hello, {update.effective_user.first_name}!\n\nОберіть мову / Choose language:',
        reply_markup=reply_markup
    )


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "uk")

    if "fact_history" not in context.user_data:
        context.user_data["fact_history"] = []

    prompt = load_prompt("random", lang)
    messages = [{"role": "system", "content": prompt}]

    if context.user_data["fact_history"]:
        history_str = "\n".join(context.user_data["fact_history"][-5:]) #last 5 facts
        exclude_msg = f"Don't repeat these facts:\n{history_str}" if lang == "en" else f"Не повторюй ці факти:\n{history_str}"
        messages.append({"role": "user", "content": exclude_msg})
    else:
        messages.append({"role": "user", "content": "Give me a random interesting fact."})

    chat_gpt:BaseAIService = context.bot_data.get("gpt_service")
    response_text = await get_ai_reply(
        update=update,
        ai_service=chat_gpt,
        messages=messages,
        lang=lang,
        button_text="Ще один факт 🔄" if lang == "uk" else "One more fact 🔄",
        button_data="next_fact"
    )

    if response_text:
        context.user_data["fact_history"].append(response_text)
        if len(context.user_data["fact_history"]) > 10: # delete if facts more than 10
            context.user_data["fact_history"].pop(0)

async def language_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang_code = query.data.replace("lang_", "")
    context.user_data["lang"] = lang_code

    if lang_code == "uk":
        commands = {
            'start': 'Головне меню', 'random': 'Випадковий факт 🧠',
            'gpt': 'Питання GPT 🤖', 'talk': 'Поговорити з зіркою 👤', 'quiz': 'Квіз ❓'
        }
        await query.edit_message_text(text="Мову змінено на українську! ✅")
    else:
        commands = {
            'start': 'Main menu', 'random': 'Random fact 🧠',
            'gpt': 'Ask GPT 🤖', 'talk': 'Talk to celebrity 👤', 'quiz': 'Quiz ❓'
        }
        await query.edit_message_text(text="Language changed to English! ✅")

    text = load_message('main', lang_code)
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, commands)


async def next_fact_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await random(update, context)

async def post_init_gpt(application):
    application.bot_data["gpt_service"] = ChatGptService(config.gpt_token)

if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(config.bot_token)
        .persistence(persistence)
        .post_init(post_init_gpt)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler('random', random))
    app.add_handler(CallbackQueryHandler(language_button_handler, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(next_fact_button_handler, pattern="^next_fact$"))

    logger.info("Bot started...")
    app.run_polling()