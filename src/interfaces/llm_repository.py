from abc import ABC, abstractmethod
from typing import List, Optional


class LLMRepository(ABC):
    """Abstract interface for Large Language Model interactions."""

    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the LLM given a prompt and optional context."""
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for the given text."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available and responding."""
        pass