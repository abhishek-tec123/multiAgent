from app.agents.base import BaseAgent
from app.core.types import PipelineContext
from app.services.vector_store import RetrieverService


class RetrieverAgent(BaseAgent):
    def __init__(self, retriever: RetrieverService):
        self.retriever = retriever

    async def run(self, context: PipelineContext) -> PipelineContext:
        result = self.retriever.retrieve(context.query)
        if result:
            context.response = result
            context.meta["source"] = "vectorstore"
        else:
            context.meta["source"] = "model-fallback"
        return await self.update_trace(context, "RetrieverAgent", "completed")


