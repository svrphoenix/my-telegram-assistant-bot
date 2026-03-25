from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def build_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ])

def build_random_keyboard(service_msg: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(service_msg.get("random",{}).get("next_fact", "🔄"), callback_data="next_fact")],
        [InlineKeyboardButton(service_msg.get("common",{}).get("finish", "❌"), callback_data="start_menu")]
    ])

def build_exit_keyboard(service_msg: dict) -> ReplyKeyboardMarkup:
    button_text = service_msg.get("common",{}).get("finish", "Завершити ❌")

    return ReplyKeyboardMarkup(
        [[KeyboardButton(button_text)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def build_talk_keyboard(characters: list[str]) -> ReplyKeyboardMarkup:
    buttons = [[char] for char in characters]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def build_vocabulary_keyboard(service_msg: dict) -> ReplyKeyboardMarkup:
    button_finish = service_msg.get("common",{}).get("finish", "Завершити ❌")
    button_more = service_msg.get("vocab",{}).get("more", "Ще слово 🆕")
    button_training = service_msg.get("vocab",{}).get("training", "Тренування 🧠")

    keyboard = [
        [KeyboardButton(button_more), KeyboardButton(button_training)],
        [KeyboardButton(button_finish)]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

from telegram import ReplyKeyboardMarkup, KeyboardButton

def build_quiz_keyboard(service_msg: dict) -> ReplyKeyboardMarkup:
    v_msg = service_msg.get("quiz", {})
    keyboard = [
        [KeyboardButton(v_msg.get("prog")), KeyboardButton(v_msg.get("math"))],
        [KeyboardButton(v_msg.get("biology"))],
        [KeyboardButton(service_msg.get("common", {}).get("finish"))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def build_quiz_control_keyboard(service_msg: dict) -> ReplyKeyboardMarkup:
    v_msg = service_msg.get("quiz", {})
    keyboard = [
        [KeyboardButton(v_msg.get("next_question_btn"))],
        [KeyboardButton(v_msg.get("change_topic_btn"))],
        [KeyboardButton(service_msg.get("common", {}).get("finish"))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)