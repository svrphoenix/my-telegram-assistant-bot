import logging
from openai import AsyncOpenAI

from baseai import BaseAIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatGptService(BaseAIService):
    def __init__(self, token, model: str = "gpt-5-mini"):
        self.client = AsyncOpenAI(api_key=token)
        self.model = model

    async def send_messages(self, messages: list) -> str:
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=3000,
                temperature=1
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            raise e