import logging

from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, PicklePersistence, ConversationHandler, PersistenceInput
)

from config import config
from constants import States
from gpt import ChatGptService
from conversations.common import start, language_button_handler, start_menu_button_handler
from conversations.gpt_conv import gpt_mode_run, get_gpt_states
from conversations.random_conv import random_mode_run, get_random_states
from conversations.talk_conv import talk_mode_run, get_talk_states

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

my_persistence_input = PersistenceInput(
    bot_data=False,
    user_data=True,
    chat_data=True,
    callback_data=True
)

persistence = PicklePersistence(
    filepath="bot_state.pickle",
    update_interval=10,
    store_data=my_persistence_input
)

async def post_init_gpt(application):
    application.bot_data["gpt_service"] = ChatGptService(config.gpt_token)

if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(config.bot_token)
        .persistence(persistence)
        .post_init(post_init_gpt)
        .concurrent_updates(True)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            States.MENU_MODE: [
                CommandHandler("gpt", gpt_mode_run),
                CommandHandler("talk", talk_mode_run),
                CommandHandler("random", random_mode_run),
                CallbackQueryHandler(language_button_handler, pattern="^lang_"),
            ],
            **get_gpt_states(),
            **get_talk_states(),
            **get_random_states()
        },
        fallbacks=[
            CallbackQueryHandler(start_menu_button_handler, pattern="^start_menu$"),
            CommandHandler("start", start),
        ],
        persistent=True,
        name="main_conversation",
    )

    app.add_handler(conv_handler)

    logger.info("Bot started...")
    app.run_polling()