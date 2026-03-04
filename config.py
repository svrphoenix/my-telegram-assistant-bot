import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    token = os.getenv("BOT_TOKEN")

config = Config()