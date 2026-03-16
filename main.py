import logging

from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, PicklePersistence, ConversationHandler, PersistenceInput,
)

from config import config
from conversations.common import start, MENU, language_button_handler, RANDOM_MODE, start_menu_button_handler
from conversations.gpt_conv import get_gpt_handler
from conversations.random_conv import get_random_handlers, random
from gpt import ChatGptService

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
            MENU: [
                get_gpt_handler(),
                CallbackQueryHandler(language_button_handler, pattern="^lang_"),
                CommandHandler("random", random),
            ],
            RANDOM_MODE: get_random_handlers(),
        },

        fallbacks=[
            CallbackQueryHandler(start_menu_button_handler, pattern="^start_menu$"),
            CommandHandler("start", start),
        ],
        persistent=True,
        name="main_conversation",
        per_message=False
    )

    app.add_handler(conv_handler)

    logger.info("Bot started...")
    app.run_polling()