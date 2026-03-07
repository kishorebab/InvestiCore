from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int

class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        pass