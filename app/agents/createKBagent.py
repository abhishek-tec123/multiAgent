# from app.services.create_KB import VectorStore
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


# def build_vectorstore_from_url(url: str) -> str:

#     vectorstore = VectorStore()
#     result = vectorstore.ensure_index(url)
#     return result

# app/agents/create_kb_agent.py
# app/agents/create_kb_agent.py
from app.services.create_KB import VectorStore
from app.core.types import PipelineContext
from app.services.retriever_singleton import get_retriever_service

class CreateKBAgent:
    async def run(self, context: PipelineContext) -> PipelineContext:
        if not context.url:
            context.response = "❌ No URL provided for knowledge base creation."
            return context

        # 🔥 Use the global retriever's embeddings (no duplicate model load)
        retriever_service = get_retriever_service()
        vectorstore = VectorStore(retriever_service.embeddings)

        # Create / update FAISS index
        result = vectorstore.ensure_index(context.url)

        # 🟢 Instead of reload from disk, reuse in-memory index
        retriever_service.vectors = vectorstore.vectors  

        context.response = result
        context.trace.append({
            "agent": "create_kb",
            "status": "done",
            "url": context.url
        })
        return context




# # Example usage:
# if __name__ == "__main__":
#     test_url = "https://docs.google.com/spreadsheets/d/1zt-IMn-oYt1ZpVycvBCxIIE1on3RRprTqluaACoN3gw/edit?gid=847287878#gid=847287878"
#     print(build_vectorstore_from_url(test_url))
