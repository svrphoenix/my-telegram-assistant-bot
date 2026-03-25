from telegram import Update
from telegram.ext import (
    MessageHandler,
    filters, ContextTypes
)

from constants import States
from conversations.common import start_menu_button_handler, mode_status_check
from util import (
    load_message, load_json, load_prompt,
    get_ai_reply, send_image, send_text, hide_main_menu
)
from keyboards import build_talk_keyboard, build_exit_keyboard

async def talk_mode_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await hide_main_menu(update, context)
    lang = context.user_data.get("lang", "uk")

    char_map = load_json("talk_map", lang)
    context.user_data["char_map"] = char_map

    text = load_message("talk", lang)
    keyboard = build_talk_keyboard(list(char_map.values()))

    await send_image(update, context, 'talk')
    await send_text(update, context, text, reply_markup=keyboard)

    return States.TALK_SELECT


async def talk_character_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    char_map = context.user_data.get("char_map", {})

    char_key = next((key for key, value in char_map.items() if value == user_choice), None)

    if not char_key:
        return States.TALK_SELECT

    context.user_data["current_char"] = char_key
    context.user_data.pop("char_map", None)
    context.user_data.pop("talk_history", None)

    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)

    await send_image(update,context,f"talk_{char_key}")
    status_text = service_msg.get("talk",{}).get("character_chosen", "✅ {character} на зв'язку! Чекаю на повідомлення.")
    await send_text(update, context, status_text.format(character=user_choice), reply_markup=build_exit_keyboard(service_msg))

    return States.TALK_DIALOG

async def talk_mode_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    lang = context.user_data.get("lang", "uk")
    service_msg = load_json('service', lang)

    exit_text = service_msg.get("common",{}).get("finish", "Завершити ❌").strip()
    if text == exit_text:
        context.user_data.pop("talk_history", None)
        context.user_data.pop("current_char", None)
        return await start_menu_button_handler(update, context)

    char_key = context.user_data.get("current_char")
    prompt = load_prompt(f"talk_{char_key}", lang)

    if "talk_history" not in context.user_data:
        system_instruction = (
            f"{prompt}\n\n"
            f"Strict Rule: Do not mention that you are an AI, a language model, or an emulation. "
            f"Stay in character 100% of the time. Respond strictly in {lang} language."
        )
        context.user_data["talk_history"] = [{"role": "system", "content": system_instruction}]

    context.user_data["talk_history"].append({"role": "user", "content": text})

    chat_gpt = context.bot_data.get("gpt_service")

    response = await get_ai_reply(
        update=update,
        context=context,
        ai_service=chat_gpt,
        messages=context.user_data["talk_history"],
        reply_markup=build_exit_keyboard(service_msg),
        show_wait=False
    )

    if response:
        context.user_data["talk_history"].append({"role": "assistant", "content": response})

    return States.TALK_DIALOG

def get_talk_states():
    return {
        States.TALK_SELECT: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.TALK_SELECT)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, talk_character_select)
        ],
        States.TALK_DIALOG: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.TALK_DIALOG)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, talk_mode_dialog)
        ],
    }