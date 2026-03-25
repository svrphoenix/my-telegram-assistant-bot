from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from constants import States
from conversations.common import start_menu_button_handler, mode_status_check
from util import load_json, get_ai_reply, send_text, hide_main_menu, send_image, get_service_msg
from keyboards import build_vocabulary_keyboard, build_exit_keyboard

MAX_HISTORY = 20

async def vocab_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await hide_main_menu(update, context)

    if "learned_words" not in context.user_data:
        context.user_data["learned_words"] = []

    s_msg = get_service_msg(context, "vocab")
    await send_image(update, context, 'vocab')
    await send_text(update, context, s_msg.get("vocab_intro", "Вітаємо у тренажері слів! 🎉"))

    return await send_new_word(update, context)

async def send_new_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uk")
    reply_markup = build_vocabulary_keyboard(load_json('service', lang))

    learned_words = context.user_data.get("learned_words", [])

    system_prompt = (
        f"You are a vocabulary tutor for a user whose native language is Ukrainian (lang_code: {lang}). "
        f"Provide one real English word with its translation into Ukrainian and an example sentence. "
        f"STRICT FORMAT: <b>Word</b> - Translation \n<i>Example:</i> sentence in English\n"
        f"STRICT RULE: Your response must be in the format above. Do not include pronunciation or etymology unless asked. "
        f"STRICT RULE: Do not repeat these words: {', '.join(learned_words[-MAX_HISTORY:])}."
    ) # last MAX_HISTORY words in memory (not repeat)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Give me a new word."}
    ]

    chat_gpt = context.bot_data.get("gpt_service")
    response = await get_ai_reply(
        update=update,
        context=context,
        ai_service=chat_gpt,
        reply_markup=reply_markup,
        messages=messages
    )

    if response and '-' in response:
        word = response.split('-')[0].strip()
        if word not in context.user_data["learned_words"]:
            context.user_data["learned_words"].append(word)

    return States.VOCAB_LEARN

async def training_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    s_msg = get_service_msg(context, "vocab")

    words = context.user_data.get("learned_words", [])
    if not words:
        await send_text(update, context, s_msg.get("learned","Ви ще не вивчили жодного слова! 📚"))
        return States.VOCAB_LEARN

    context.user_data["training_index"] = 0
    context.user_data["training_score"] = 0

    header = s_msg.get("vocab_length", "Ваш словниковий запас: {length} слів").format(length=len(words))
    question = s_msg.get("training_start", "Режим тренування! Як перекладається слово: <i>{word}</i>?").format(word=words[0])
    lang = context.user_data.get("lang", "uk")
    exit_markup = build_exit_keyboard(load_json('service', lang))
    await send_text(update, context, f"{header}\n\n{question}", reply_markup=exit_markup)

    return States.VOCAB_TRAINING

async def training_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_answer = update.message.text
    s_msg = get_service_msg(context, "vocab")
    lang = context.user_data.get("lang", "uk")
    exit_markup = build_exit_keyboard(load_json('service', lang))
    service_common = load_json('service', lang).get("common", {})
    if user_answer == service_common.get("finish"):
        return await start_menu_button_handler(update, context)

    index = context.user_data.get("training_index", 0)
    words = context.user_data.get("learned_words", [])
    target_word = words[index]

    validate_prompt = [
        {"role": "system",
         "content": (
             f"You are a language teacher. Check if '{user_answer}' is a correct {lang} translation "
             f"for the English word '{target_word}'. "
             f"If there are minor typos or grammatical mistakes but the meaning is clearly correct, answer 'YES'. "
             f"If the meaning is wrong, answer 'NO'. "
             f"Answer ONLY with 'YES' or 'NO' (one word)."
         )}
    ]

    chat_gpt = context.bot_data.get("gpt_service")
    result = await chat_gpt.send_messages(validate_prompt)
    feedback = s_msg.get("correct") if "YES" in result.upper() else s_msg.get("wrong")
    if "YES" in result.upper():
        context.user_data["training_score"] += 1
    await send_text(update, context, feedback, reply_markup=exit_markup)

    index += 1
    if index < len(words):
        context.user_data["training_index"] = index
        next_quest = s_msg.get("next_word").format(next_word=words[index])
        await send_text(update, context, next_quest, reply_markup=exit_markup)
        return States.VOCAB_TRAINING

    res_text = s_msg.get("training_finished").format(score=context.user_data["training_score"], total=len(words))
    await send_text(update, context, res_text)
    return await start_menu_button_handler(update, context)

async def  vocab_logic_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    s_msg = get_service_msg(context, "vocab")
    more_text = s_msg.get("more", "Ще слово 🆕").strip()
    training_text = s_msg.get("training", "Тренування 🧠").strip()

    if user_choice == more_text:
        return await send_new_word(update, context)
    elif user_choice == training_text:
        return await training_start(update, context)
    else:
        return await start_menu_button_handler(update, context)

def get_vocab_states():
    return {
        States.VOCAB_LEARN: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.VOCAB_LEARN)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, vocab_logic_router)
        ],
        States.VOCAB_TRAINING: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.VOCAB_TRAINING)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, training_process)
        ]
    }