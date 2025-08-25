from datetime import datetime
from typing import AsyncIterator, List, Dict

from groq import AsyncGroq

from app.core.config import MODEL_NAME


class LlmService:
    def __init__(self, model_name: str = MODEL_NAME, temperature: float = 0.5):
        self.client = AsyncGroq()
        self.model_name = model_name
        self.temperature = temperature

    async def stream_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            temperature=self.temperature,
            max_completion_tokens=max_tokens,
            top_p=1,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    @staticmethod
    def build_metadata() -> dict:
        return {
            "model_used": MODEL_NAME,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


