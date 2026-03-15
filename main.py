import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, PicklePersistence
)

from config import config
from baseai import BaseAIService
from gpt import ChatGptService
from keyboards import build_language_keyboard, build_random_keyboard
from util import (load_message, send_text, send_image, show_main_menu, load_prompt, get_ai_reply, load_json,
                  hide_main_menu)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="bot_data.pickle", update_interval=10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = build_language_keyboard()
    await update.message.reply_text(
        f'Hello, {update.effective_user.first_name}!\n\nОберіть мову / Choose language:',
        reply_markup=reply_markup
    )

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await hide_main_menu(update, context)
    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)

    if update.message:
        await send_image(update, context, 'random')

    if "fact_history" not in context.user_data:
        context.user_data["fact_history"] = []

    prompt = load_prompt("random", lang)
    messages = [{"role": "system", "content": prompt}]

    if context.user_data["fact_history"]:
        history_str = "\n".join(context.user_data["fact_history"][-5:]) #last 5 facts
        exclude_text = service_msg.get("exclude_facts", "Не повторюй ці факти:")
        messages.append({"role": "user", "content": f"{exclude_text}\n{history_str}"})
    else:
        messages.append({"role": "user", "content": "Give me a random interesting fact."})

    chat_gpt:BaseAIService = context.bot_data.get("gpt_service")
    response_text = await get_ai_reply(
        update=update,
        ai_service=chat_gpt,
        messages=messages,
        lang=lang,
        reply_markup=build_random_keyboard(service_msg)
    )

    if response_text:
        context.user_data["fact_history"].append(response_text)
        if len(context.user_data["fact_history"]) > 10: # delete if facts more than 10
            context.user_data["fact_history"].pop(0)


async def show_main_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "uk")
    text = load_message('main', lang)
    commands = load_json('menu', lang)

    await send_image(update, context, 'main')
    await send_text(update, context, text)

    await show_main_menu(update, context, commands)


async def language_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang_code = query.data.replace("lang_", "")
    context.user_data["lang"] = lang_code

    status_msgs = load_json('service', lang_code)
    success_text = status_msgs.get("lang_changed", "Мову змінено! ✅")

    await query.edit_message_text(text=success_text)
    await show_main_screen(update, context)


async def start_menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await show_main_screen(update, context)

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
    app.add_handler(CallbackQueryHandler(start_menu_button_handler, pattern="^start_menu$"))

    logger.info("Bot started...")
    app.run_polling()