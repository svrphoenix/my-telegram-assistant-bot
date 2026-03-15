from typing import Optional, List
import json
import logging
from pathlib import Path
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Message,
    BotCommand, MenuButtonCommands, BotCommandScopeChat, MenuButtonDefault
)
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from baseai import BaseAIService

BASE_PATH = Path("resources")
RESOURCE_PATHS = {
    "messages": BASE_PATH / "messages",
    "prompts": BASE_PATH / "prompts",
    "images" : BASE_PATH / "images",
}

# надсилає в чат текстове повідомлення
async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str, parse_mode: str = ParseMode.HTML) -> Message:
    clean_text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    chat_id = update.effective_chat.id

    try:
        return await context.bot.send_message(
            chat_id = chat_id,
            text = clean_text,
            parse_mode = parse_mode
        )
    except Exception as e:
        logging.error(f"Error in ParseMode {parse_mode}: {e}")
        return await context.bot.send_message(
            chat_id = chat_id,
            text = clean_text
        )

# надсилає в чат фото
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> Message:
    lang = context.user_data.get("lang", "uk")
    service_data = load_json("service", lang)
    error_message = service_data.get("image_not_found", "Image not found...")

    image_path = RESOURCE_PATHS["images"] / f"{name}.jpg"

    if not image_path.exists():
        logging.error(f"Image not found: {image_path}")
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=error_message
        )

    with open(image_path, 'rb') as image:
        return await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image)


# відображає команду та головне меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, commands: dict):
    command_list = [BotCommand(key, value) for key, value in commands.items()]

    await context.bot.set_my_commands(command_list, scope=BotCommandScopeChat(chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonCommands(), chat_id=update.effective_chat.id)

# видаляємо команди для конкретного чату
async def hide_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_my_commands(
        scope=BotCommandScopeChat(chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonDefault(),
                                           chat_id=update.effective_chat.id)

def _load_resource(folder_key: str, name: str, lang: str = "uk") -> str:
    path = RESOURCE_PATHS[folder_key] / lang / f"{name}.txt"
    if not path.exists():
        logging.error(f"Resource '{name}' not found at: {path}")
        return ""
    return path.read_text(encoding="utf8")

def load_message(name: str, lang: str = "uk"):
    return _load_resource("messages", name, lang)

def load_prompt(name: str, lang: str = "uk"):
    return _load_resource("prompts", name, lang)

def load_json(filename: str, lang: str) -> dict:
    path = RESOURCE_PATHS["messages"] / lang / f"{filename}.json"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON {path}: {e}")
        return {}

async def get_ai_reply(
    update: Update,
    ai_service: BaseAIService,
    messages: list,
    lang: str = "uk",
    reply_markup: Optional[InlineKeyboardMarkup] = None
):
    actual_message = update.effective_message

    service_data = load_json("service", lang)
    wait_text = service_data.get("wait", "Please wait...")
    error_text = service_data.get("error", "Error occurred.")
    wait_msg = await actual_message.reply_text(wait_text)

    try:
        response_text = await ai_service.send_messages(messages)

        await wait_msg.edit_text(response_text, reply_markup=reply_markup)
        return response_text

    except Exception as e:
        logging.error(f"AI Service Error: {e}")
        await wait_msg.edit_text(error_text)
        return None