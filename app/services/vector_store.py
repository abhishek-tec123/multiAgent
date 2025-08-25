import os
import glob
from typing import Optional, List

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import FAISS_INDEX_PATH, RETRIEVER_FILE_PATH, MODEL_NAME
from app.core.logging_utils import get_logger


logger = get_logger()


def _is_query_relevant(query: str, docs: List[Document], embeddings_model, threshold: float = 0.3) -> bool:
    if not docs:
        logger.info("No documents for relevance check.")
        return False
    query_embedding = embeddings_model.embed_query(query)
    doc_embedding = embeddings_model.embed_documents([docs[0].page_content])[0]
    similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
    logger.info(f"Cosine similarity score: {similarity:.3f}")
    return similarity >= threshold   # lowered threshold for better recall


class RetrieverService:
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or RETRIEVER_FILE_PATH
        self.embeddings = HuggingFaceEmbeddings()
        self.vectors: Optional[FAISS] = None
        self.prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant. Answer the query based ONLY on the context below.\n\nContext:\n{context}\n\nQuery: {input}"
        )
        self.llm = ChatGroq(model_name=MODEL_NAME, temperature=0.2)
        self.document_chain = create_stuff_documents_chain(self.llm, self.prompt)

    def ensure_index(self) -> str:
        if self.vectors:
            return "FAISS index already loaded."

        if os.path.exists(FAISS_INDEX_PATH) and glob.glob(f"{FAISS_INDEX_PATH}/*"):
            self.vectors = FAISS.load_local(
                FAISS_INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True
            )
            logger.info("Loaded existing FAISS index.")
            return "Loaded existing FAISS index."

        with open(self.file_path, "r", encoding="utf-8") as file:
            text = file.read()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_text(text)
        documents = [Document(page_content=chunk) for chunk in chunks]

        self.vectors = FAISS.from_documents(documents, self.embeddings)
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        self.vectors.save_local(FAISS_INDEX_PATH)
        logger.info("Vector embeddings created and saved.")
        return "Vector embeddings created and saved."

    def retrieve(self, query: str) -> Optional[str]:
        if not self.vectors:
            logger.warning("No FAISS index loaded.")
            return None

        retriever = self.vectors.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        docs = retriever.invoke(query)

        logger.info(f"Retriever raw docs: {[d.page_content[:100] for d in docs]}")

        if not docs or not _is_query_relevant(query, docs, self.embeddings):
            logger.info("Query not relevant to vectorstore. Falling back to MainAgent.")
            return None

        chain = create_retrieval_chain(retriever, self.document_chain)
        result = chain.invoke({"input": query, "context": "\n".join([d.page_content for d in docs])})

        logger.info(f"Retriever result: {result}")
        return result.get("answer")


