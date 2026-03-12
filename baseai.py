from abc import ABC, abstractmethod
from typing import List, Optional

class BaseAIService(ABC):
    @abstractmethod
    async def send_messages(self, messages: List[dict]) -> Optional[str]:
        pass