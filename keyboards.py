from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def build_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ])

def build_random_keyboard(service_msg: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(service_msg.get("next_fact", "🔄"), callback_data="next_fact")],
        [InlineKeyboardButton(service_msg.get("finish", "❌"), callback_data="start_menu")]
    ])

def build_exit_keyboard(service_msg: dict):
    button_text = service_msg.get("finish", "Завершити ❌")

    return ReplyKeyboardMarkup(
        [[KeyboardButton(button_text)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def build_talk_keyboard(characters: list[str]) -> ReplyKeyboardMarkup:
    buttons = [[char] for char in characters]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)