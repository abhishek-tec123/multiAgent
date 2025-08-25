from app.agents.base import BaseAgent
from app.core.types import PipelineContext
from app.services.llm import LlmService


class MainAgent(BaseAgent):
    def __init__(self, llm: LlmService):
        self.llm = llm

    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.response and context.meta.get("source") == "vectorstore":
            return context
        prompt = [
            {"role": "system", "content": "You are an AI expert."},
            {"role": "user", "content": f"Answer this in 50 words: {context.query}"},
        ]
        response = ""
        async for chunk in self.llm.stream_completion(prompt, max_tokens=1024):
            response += chunk
        context.response = response
        context.meta.update(self.llm.build_metadata())
        return await self.update_trace(context, "MainAgent", "completed")


