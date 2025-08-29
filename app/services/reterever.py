import os
from typing import Optional, List

from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from sklearn.metrics.pairwise import cosine_similarity
import tiktoken

from app.core.config import FAISS_INDEX_PATH, MODEL_NAME
from app.core.logging_utils import get_logger

logger = get_logger()


def _is_query_relevant(query: str, docs: List[Document], embeddings_model, threshold: float = 0.3) -> bool:
    """Check if query is relevant to the top retrieved document using cosine similarity."""
    if not docs:
        logger.info("No documents for relevance check.")
        return False
    query_embedding = embeddings_model.embed_query(query)
    doc_embedding = embeddings_model.embed_documents([docs[0].page_content])[0]
    similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
    logger.info(f"Cosine similarity score: {similarity:.3f}")
    return similarity >= threshold


class RetrieverService:
    def __init__(self, embeddings, file_path: Optional[str] = None):
        self.file_path = file_path
        self.embeddings = embeddings
        self.vectors: Optional[FAISS] = None
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # LLM + prompt setup
        self.prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant. Answer the query based ONLY on the context below.\n\nContext:\n{context}\n\nQuery: {input}"
        )
        self.llm = ChatGroq(model_name=MODEL_NAME, temperature=0.2)
        self.document_chain = create_stuff_documents_chain(self.llm, self.prompt)

        # 🚫 Do NOT auto-load FAISS index
        logger.info("[Retriever Init] Skipping FAISS auto-load. Waiting for create_kb.")

    def reload_index(self):
        """Reload FAISS index after CreateKB builds it (always fresh)."""
        if os.path.exists(FAISS_INDEX_PATH):
            try:
                self.vectors = FAISS.load_local(
                    FAISS_INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True
                )
                logger.info("[Retriever] FAISS index loaded successfully.")
            except Exception as e:
                logger.error(f"[Retriever] Failed to load FAISS index: {e}")
                self.vectors = None
        else:
            logger.warning("[Retriever] No FAISS index found. Run create_kb first.")

    def retrieve(self, query: str) -> Optional[str]:
        """Retrieve and answer query using FAISS + LLM."""
        if not self.vectors:
            logger.warning("No FAISS index loaded. Run create_kb first.")
            return None

        retriever = self.vectors.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        docs = retriever.invoke(query)

        logger.info(f"Retriever raw docs: {[d.page_content[:100] for d in docs]}")

        if not docs or not _is_query_relevant(query, docs, self.embeddings):
            logger.info("Query not relevant to vectorstore. Falling back to MainAgent.")
            return None

        chain = create_retrieval_chain(retriever, self.document_chain)
        result = chain.invoke({"input": query, "context": "\n".join([d.page_content for d in docs])})

        return result.get("answer")


