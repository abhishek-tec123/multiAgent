# from app.agents.base import BaseAgent
# from app.core.types import PipelineContext
# from app.services.reterever import RetrieverService


# class RetrieverAgent(BaseAgent):
#     def __init__(self, retriever: RetrieverService):
#         self.retriever = retriever

#     async def run(self, context: PipelineContext) -> PipelineContext:
#         result = self.retriever.retrieve(context.query)
#         if result:
#             context.response = result
#             context.meta["source"] = "vectorstore"
#         else:
#             context.meta["source"] = "model-fallback"
#         return await self.update_trace(context, "RetrieverAgent", "completed")


# app/agents/retriever_agent.py
from app.agents.base import BaseAgent
from app.core.types import PipelineContext
from app.services.retriever_singleton import get_retriever_service  # 🟢 use lazy singleton


class RetrieverAgent(BaseAgent):
    def __init__(self):
        # always use the singleton retriever
        self.retriever = get_retriever_service()

    async def run(self, context: PipelineContext) -> PipelineContext:
        result = self.retriever.retrieve(context.query)

        if result:
            context.response = result
            context.meta["source"] = "vectorstore"
        else:
            context.response = "I couldn’t find a relevant answer in the knowledge base."
            context.meta["source"] = "model-fallback"

        return await self.update_trace(context, "RetrieverAgent", "completed")
