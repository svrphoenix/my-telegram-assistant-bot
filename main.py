import logging

from telegram.ext import (
    ApplicationBuilder, PicklePersistence, PersistenceInput
)

from config import config
from conversations.router import get_main_conversation
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

    app.add_handler(get_main_conversation())

    logger.info("Bot started...")
    app.run_polling()