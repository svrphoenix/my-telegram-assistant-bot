from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from baseai import BaseAIService
from constants import States
from keyboards import build_random_keyboard
from util import hide_main_menu, load_json, send_image, load_prompt, get_ai_reply


async def random_mode_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        messages.append({"role": "user", "content": f"Don't repeat these facts:\n{history_str}"})
    else:
        messages.append({"role": "user", "content": "Give me a random interesting fact."})

    chat_gpt: BaseAIService = context.bot_data.get("gpt_service")
    response_text = await get_ai_reply(
        update=update,
        context=context,
        ai_service=chat_gpt,
        messages=messages,
        reply_markup=build_random_keyboard(service_msg)
    )

    if response_text:
        context.user_data["fact_history"].append(response_text)
        if len(context.user_data["fact_history"]) > 10: # delete if facts more than 10
            context.user_data["fact_history"].pop(0)

    return States.RANDOM_MODE

async def next_fact_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await random_mode_run(update, context)

def get_random_states():
    return {
        States.RANDOM_MODE: [
            CallbackQueryHandler(next_fact_button_handler, pattern="^next_fact$"),
        ]
    }