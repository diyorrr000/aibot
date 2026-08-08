from abc import ABC, abstractmethod
from typing import List, Any, Optional

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        timeout: float = 25.0,
        retries: int = 2,
    ) -> str:
        pass
