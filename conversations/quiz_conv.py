from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from constants import States
from conversations.common import start_menu_button_handler, mode_status_check
from util import load_json, get_ai_reply, send_text, hide_main_menu, send_image, load_prompt, get_service_msg
from keyboards import build_quiz_keyboard, build_exit_keyboard, build_quiz_control_keyboard

MAX_HISTORY = 10

async def quiz_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await hide_main_menu(update, context)
    context.user_data["quiz_score"] = 0
    context.user_data["quiz_total"] = 0
    s_msg = get_service_msg(context, "quiz")

    await send_image(update, context, 'quiz')

    lang = context.user_data.get("lang", "uk")
    reply_markup = build_quiz_keyboard(load_json('service', lang))

    await send_text(update, context, s_msg.get("quiz_intro"), reply_markup=reply_markup)
    return States.QUIZ_SELECT_TOPIC

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE, topic_key: str) -> int:
    lang = context.user_data.get("lang", "uk")
    user_rules = load_prompt("quiz", lang)
    context.user_data["current_quiz_topic"] = topic_key

    if "used_questions" not in context.user_data:
        context.user_data["used_questions"] = []
    excluded = "\n".join(context.user_data["used_questions"][-MAX_HISTORY:]) # last questions in history
    system_instruction = (
        f"{user_rules}\n\n"
        "STRICT RULE: Generate ONLY ONE question at a time. "
        "Do not provide answers, lists, or explanations until the user responds. "
        f"NEVER repeat these recent questions:\n{excluded}"
    )
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": topic_key}
    ]
    chat_gpt = context.bot_data.get("gpt_service")

    question = await get_ai_reply(
        update=update,
        context=context,
        ai_service=chat_gpt,
        messages=messages,
        reply_markup=build_exit_keyboard(load_json('service', lang))
    )

    if question:
        context.user_data["current_quiz_question"] = question
        context.user_data["used_questions"].append(question)
        return States.QUIZ_QUESTION

    return States.QUIZ_SELECT_TOPIC


async def quiz_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_answer = update.message.text
    lang = context.user_data.get("lang", "uk")
    s_msg = get_service_msg(context, "quiz")

    if user_answer == s_msg.get("next_question_btn"):
        saved_topic = context.user_data.get("current_quiz_topic", "quiz_prog")
        return await send_quiz_question(update, context, saved_topic)

    if user_answer == s_msg.get("change_topic_btn"):
        return await quiz_run(update, context)

    if user_answer == load_json('service', lang).get("common", {}).get("finish"):
        return await start_menu_button_handler(update, context)

    question = context.user_data.get("current_quiz_question")

    validate_instruction = (
        "Verdict only. If correct: 'YES'. "
        "If wrong: 'NO | correct_answer'. "
        "No prose, no stars, no bold tags."
    )

    messages = [
        {"role": "system", "content": validate_instruction},
        {"role": "user", "content": f"Q: {question}\nA: {user_answer}"}
    ]

    chat_gpt = context.bot_data.get("gpt_service")
    result = await chat_gpt.send_messages(messages)

    is_correct = result.strip().upper().startswith("YES")
    context.user_data["quiz_total"] = context.user_data.get("quiz_total", 0) + 1

    if is_correct:
        context.user_data["quiz_score"] = context.user_data.get("quiz_score", 0) + 1
        final_reply = s_msg.get("correct", "Правильно!")
    else:
        ans = result.split("|")[-1].strip() if "|" in result else "???"
        template = s_msg.get("incorrect_answer", "Неправильно! Правильна відповідь — <b>{}</b>")
        final_reply = template.format(ans)

    await send_text(update, context, final_reply)

    score_msg = s_msg.get("score_status").format(
        score=context.user_data["quiz_score"],
        total=context.user_data["quiz_total"]
    )

    await send_text(
        update,
        context,
        f"{score_msg}\n\n{s_msg.get('next_prompt')}",
        reply_markup=build_quiz_control_keyboard(load_json('service', lang))
    )

    return States.QUIZ_QUESTION

async def quiz_topic_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    s_msg = get_service_msg(context, "quiz")

    mapping = {
        s_msg.get("prog"): "quiz_prog",
        s_msg.get("math"): "quiz_math",
        s_msg.get("biology"): "quiz_biology"
    }

    topic_key = mapping.get(choice)
    if topic_key:
        return await send_quiz_question(update, context, topic_key)

    return await start_menu_button_handler(update, context)

def get_quiz_states():
    return {
        States.QUIZ_SELECT_TOPIC: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.QUIZ_SELECT_TOPIC)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_topic_router)
        ],
        States.QUIZ_QUESTION: [
            MessageHandler(filters.COMMAND, lambda upd, cont: mode_status_check(upd, cont, States.QUIZ_QUESTION)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_answer_handler)
        ]
    }