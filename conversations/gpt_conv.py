from telegram import Update
from telegram.ext import (ConversationHandler, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes)

from baseai import BaseAIService
from conversations.common import start_menu_button_handler, start, MENU
from util import load_message, load_json, load_prompt, get_ai_reply, send_image, send_text, hide_main_menu
from keyboards import build_exit_keyboard

GPT_MODE = 1

async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await hide_main_menu(update, context)
    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)
    context.user_data.pop("gpt_history", None)

    await send_image(update, context, 'gpt')
    await send_text(
        update,
        context,
        load_message('gpt', lang),
        reply_markup=build_exit_keyboard(service_msg)
    )
    return GPT_MODE


async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)
    exit_text = service_msg.get("finish", "Завершити ❌").strip()
    user_text = update.message.text.strip()

    if user_text == exit_text:
        context.user_data.pop("gpt_history", None)
        return await start_menu_button_handler(update, context)

    if "gpt_history" not in context.user_data:
        prompt = load_prompt('gpt', lang)
        context.user_data["gpt_history"] = [
            {"role": "system", "content": prompt}
        ]
    context.user_data["gpt_history"].append({"role": "user", "content": update.message.text})

    if len(context.user_data["gpt_history"]) > 11:  # prompt + 10 повідомлень
        context.user_data["gpt_history"] = [context.user_data["gpt_history"][0]] + context.user_data["gpt_history"][
            -20:]

    chat_gpt: BaseAIService = context.bot_data.get("gpt_service")
    response_text = await get_ai_reply(
        update=update,
        context=context,
        ai_service=chat_gpt,
        messages=context.user_data["gpt_history"],
        reply_markup=build_exit_keyboard(service_msg)
    )
    if response_text:
        context.user_data["gpt_history"].append({"role": "assistant", "content": response_text})

    return GPT_MODE

async def gpt_status_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)

    warning_text = service_msg.get("gpt_is_active", "⚠️ Режим GPT активний. Щоб змінити режим, натисніть кнопку 'Закінчити'.")

    await update.message.reply_text(warning_text, reply_markup=build_exit_keyboard(service_msg))
    return GPT_MODE


def get_gpt_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("gpt", gpt)],
        states={
            GPT_MODE: [
                CommandHandler("random", gpt_status_check),
                MessageHandler(filters.COMMAND, gpt_status_check),
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_dialog),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(start_menu_button_handler, pattern="^start_menu$"),
            CommandHandler("start", start),
        ],
        map_to_parent={
            MENU: MENU
        },
        persistent = True,
        name = "gpt_conversation",
        per_message = False
    )