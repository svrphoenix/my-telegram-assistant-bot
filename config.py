from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    bot_token = getenv("BOT_TOKEN")
    gpt_token = getenv("GPT_TOKEN")

config = Config()