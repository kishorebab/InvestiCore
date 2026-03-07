import httpx
import logging
from .llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

# This is the JSON schema Ollama will force Phi-3 to follow exactly.
# This is far more reliable than asking nicely in the prompt.
PLAN_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "planId": {"type": "string"},
        "overallReasoning": {"type": "string"},
        "estimatedComplexity": {
            "type": "string",
            "enum": ["low", "medium", "high"]
        },
        "confidence": {"type": "number"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "stepNumber": {"type": "integer"},
                    "toolName": {"type": "string"},
                    "arguments": {"type": "object"},
                    "reasoning": {"type": "string"},
                    "dependsOn": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                },
                "required": ["stepNumber", "toolName", "arguments", "reasoning", "dependsOn"]
            }
        }
    },
    "required": ["planId", "overallReasoning", "estimatedComplexity", "confidence", "steps"]
}

class OllamaClient(LLMClient):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            "stream": False,
            "format": PLAN_OUTPUT_SCHEMA,   # <-- structured output enforcement
            "options": {
                "temperature": 0.1,   # Low temperature = more deterministic JSON
                "num_predict": 1024
            }
        }

        logger.info(f"Calling Ollama model={self.model}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        content = data["message"]["content"]
        logger.info(f"Ollama response received, tokens={data.get('eval_count', 0)}")

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0)
        )