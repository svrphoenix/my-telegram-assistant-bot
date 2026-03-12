from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, \
    BotCommand, MenuButtonCommands, BotCommandScopeChat, MenuButtonDefault
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
import logging
import os

from baseai import BaseAIService

MESSAGES = {
    "uk": {"wait": "Зачекайте декілька секунд... ⏳", "error": "Сталася помилка GPT ❌"},
    "en": {"wait": "Wait a few seconds... ⏳", "error": "GPT error occurred ❌"}
}

# конвертує об'єкт user в рядок
def dialog_user_info_to_str(user_data) -> str:
    mapper = {'language_from': 'Мова оригіналу', 'language_to': 'Мова перекладу', 'text_to_translate': 'Текст для перекладу'}
    return '\n'.join(map(lambda k, v: (mapper[k], v), user_data.items()))


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
        logging.error(f"Помилка ParseMode {parse_mode}: {e}")
        return await context.bot.send_message(
            chat_id = chat_id,
            text = clean_text
        )

# надсилає в чат текстове повідомлення, та додає до нього кнопки
async def send_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, buttons: dict) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    keyboard = []
    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        keyboard.append([button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(
        update.effective_message.chat_id,
        text=text, reply_markup=reply_markup,
        message_thread_id=update.effective_message.message_thread_id)


# надсилає в чат фото
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> Message:
    with open(f'resources/images/{name}.jpg', 'rb') as image:
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

def _load_resource(folder: str, name: str, lang: str = "uk") -> str:
    path = os.path.join("resources", folder, lang, f"{name}.txt")

    if not os.path.exists(path):
        path = os.path.join("resources", folder, "uk", f"{name}.txt")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Ресурс '{name}' не знайдено ні в '{lang}', ні в 'uk'.")

    with open(path, "r", encoding="utf8") as file:
        return file.read()


def load_message(name: str, lang: str = "uk"):
    return _load_resource("messages", name, lang)


def load_prompt(name: str, lang: str = "uk"):
    return _load_resource("prompts", name, lang)


async def get_ai_reply(
    update: Update,
    ai_service: BaseAIService,
    messages: list,
    lang: str = "uk",
    button_text: str = None,
    button_data: str = None
):
    actual_message = update.message if update.message else update.callback_query.message
    wait_msg = await actual_message.reply_text(MESSAGES[lang]["wait"])
    try:
        response_text = await ai_service.send_messages(messages)

        reply_markup = None
        if button_text and button_data:
            keyboard = [[InlineKeyboardButton(button_text, callback_data=button_data)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

        await wait_msg.edit_text(response_text, reply_markup=reply_markup)
        return response_text

    except Exception as e:
        logging.error(f"AI Service Error: {e}")
        await wait_msg.edit_text(MESSAGES.get(lang, MESSAGES["uk"])["error"])
        return None