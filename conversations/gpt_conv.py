from telegram import Update
from telegram.ext import (
    MessageHandler, filters,
    ContextTypes
)

from baseai import BaseAIService
from constants import States
from conversations.common import start_menu_button_handler, mode_status_check
from util import load_message, load_json, load_prompt, get_ai_reply, send_image, send_text, hide_main_menu
from keyboards import build_exit_keyboard

MAX_HISTORY = 10

async def gpt_mode_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    return States.GPT_MODE


async def gpt_mode_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)
    exit_text = service_msg.get("common",{}).get("finish", "Завершити ❌").strip()
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

    if len(context.user_data["gpt_history"]) > MAX_HISTORY + 1:  # prompt + MAX_HISTORY
        context.user_data["gpt_history"] = [context.user_data["gpt_history"][0]] + context.user_data["gpt_history"][
            -MAX_HISTORY:]

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

    return States.GPT_MODE

def get_gpt_states():
    return {
        States.GPT_MODE: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.GPT_MODE)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_mode_dialog),
        ]
    }