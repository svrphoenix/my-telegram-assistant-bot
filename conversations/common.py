from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from keyboards import build_language_keyboard
from util import load_message, load_json, send_image, send_text, show_main_menu

(
    MENU,
    RANDOM_MODE
) = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = build_language_keyboard()
    await update.message.reply_text(
        f'Hello, {update.effective_user.first_name}!\n\nОберіть мову / Choose language:',
        reply_markup=reply_markup
    )
    return MENU

async def show_main_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup=None):
    lang = context.user_data.get("lang", "uk")
    text = load_message('main', lang)
    commands = load_json('menu', lang)

    await show_main_menu(update, context, commands)
    await send_image(update, context, 'main')
    await send_text(update, context, text, reply_markup=reply_markup)

    return MENU

async def language_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.replace("lang_", "")
    context.user_data["lang"] = lang_code
    status_msgs = load_json('service', lang_code)

    await query.edit_message_text(text=status_msgs.get("lang_changed", "Мову змінено! ✅"))
    await show_main_screen(update, context)

    return MENU

async def start_menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()

    await show_main_screen(update, context, reply_markup=ReplyKeyboardRemove())
    return MENU
