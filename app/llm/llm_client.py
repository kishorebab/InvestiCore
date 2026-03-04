from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for an LLM client."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the raw text response."""
        raise NotImplementedError()


class LocalLLMClient(LLMClient):
    """A mock implementation that returns a fixed placeholder JSON.

    This is useful for development and testing. Replace with a real
    implementation that calls OpenAI, Azure, etc.
    """

    def generate(self, prompt: str) -> str:
        # In a real implementation this would call out to an LLM service.
        # For now we return an empty JSON object which will trigger
        # validation errors and exercise the retry loop in agents.
        return "{}"