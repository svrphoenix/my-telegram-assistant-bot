from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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

