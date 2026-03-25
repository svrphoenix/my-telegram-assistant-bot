from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler
from constants import States
from conversations.common import start, language_button_handler, start_menu_button_handler
from conversations.quiz_conv import quiz_run, get_quiz_states
from conversations.vocabulary_conv import vocab_run, get_vocab_states
from conversations.gpt_conv import gpt_mode_run, get_gpt_states
from conversations.random_conv import random_mode_run, get_random_states
from conversations.talk_conv import talk_mode_run, get_talk_states

def get_main_conversation() -> ConversationHandler:
    all_states = {
        States.MENU_MODE: [
            CommandHandler("gpt", gpt_mode_run),
            CommandHandler("talk", talk_mode_run),
            CommandHandler("random", random_mode_run),
            CommandHandler('quiz', quiz_run),
            CommandHandler("vocabulary", vocab_run),
            CallbackQueryHandler(language_button_handler, pattern="^lang_"),
        ]
    }

    all_states.update(get_gpt_states())
    all_states.update(get_talk_states())
    all_states.update(get_random_states())
    all_states.update(get_quiz_states())
    all_states.update(get_vocab_states())

    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=all_states,
        fallbacks=[
            CallbackQueryHandler(start_menu_button_handler, pattern="^start_menu$"),
            CommandHandler("start", start),
        ],
        persistent=True,
        name="main_conversation",
    )