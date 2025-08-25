# with vector store

import logging
import json
import os
import glob
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from sklearn.metrics.pairwise import cosine_similarity

# === CONFIG ===
MODEL_NAME = "llama3-70b-8192"
SENDER_EMAIL = "sender@example.com"
SENDER_PASSWORD = "yourpassword"
RECEIVER_EMAIL = "receiver@example.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FAISS_INDEX_PATH = "vector_index"
RETRIEVER_FILE_PATH = "/Users/abhishek/Desktop/multiAgentAI/mainAagent/ProjectMcp/api.txt"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv()

# === LOGGING ===
logger = logging.getLogger("ai-pipeline")
logging.basicConfig(level=logging.INFO)

# === CONTEXT & BASE AGENT ===
@dataclass
class PipelineContext:
    query: str
    response: Optional[str] = None
    summary: Optional[str] = None
    subject: Optional[str] = None
    phone: Optional[str] = None
    email_status: Optional[str] = None
    sms_status: Optional[str] = None
    trace: List[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

class BaseAgent(ABC):
    @abstractmethod
    async def run(self, context: PipelineContext) -> PipelineContext:
        pass

    async def update_trace(self, context: PipelineContext, agent_name: str, status: str):
        context.trace.append({"agent": agent_name, "status": status})
        return context

# === UTILS ===
def is_query_relevant(query: str, docs: list, embeddings_model, threshold=0.5) -> bool:
    if not docs:
        logger.info("⚠️ No documents for relevance check.")
        return False
    query_embedding = embeddings_model.embed_query(query)
    doc_embedding = embeddings_model.embed_documents([docs[0].page_content])[0]
    similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
    logger.info(f"🔍 Cosine similarity score: {similarity:.3f}")
    return similarity >= threshold

# === RETRIEVER ===
class Retriever:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.embeddings = HuggingFaceEmbeddings()
        self.vectors = None
        self.prompt = ChatPromptTemplate.from_template("Answer this and should be consise and structured, not to long based on query: {context}")
        self.llm = ChatGroq(model_name=MODEL_NAME, temperature=0.5)
        self.document_chain = create_stuff_documents_chain(self.llm, self.prompt)

    def vector_embedding(self):
        if self.vectors:
            return {"status": "FAISS index already loaded."}

        if os.path.exists(FAISS_INDEX_PATH) and glob.glob(f"{FAISS_INDEX_PATH}/*"):
            self.vectors = FAISS.load_local(FAISS_INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True)
            return {"status": "Loaded existing FAISS index."}

        with open(self.file_path, 'r') as file:
            text = file.read()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = text_splitter.split_text(text)
        documents = [Document(page_content=chunk) for chunk in chunks]
        self.vectors = FAISS.from_documents(documents, self.embeddings)
        self.vectors.save_local(FAISS_INDEX_PATH)
        return {"status": "Vector embeddings created and saved."}

    def retrieval(self, query: str):
        if not self.vectors:
            return None

        retriever = self.vectors.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        docs = retriever.invoke(query)

        if not is_query_relevant(query, docs, self.embeddings):
            logger.info("🔎 Query not relevant to vectorstore. Falling back to MainAgent.")
            return None

        chain = create_retrieval_chain(retriever, self.document_chain)
        result = chain.invoke({"input": query})
        return result.get("answer")

# === AGENTS ===
from groq import AsyncGroq

class RetrieverAgent(BaseAgent):
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    async def run(self, context: PipelineContext) -> PipelineContext:
        result = self.retriever.retrieval(context.query)
        if result:
            context.response = result
            context.meta["source"] = "vectorstore"
        else:
            context.meta["source"] = "model-fallback"
        return await self.update_trace(context, "RetrieverAgent", "completed")

class MainAgent(BaseAgent):
    def __init__(self):
        self.client = AsyncGroq()

    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.response and context.meta.get("source") == "vectorstore":
            return context

        prompt = [
            {"role": "system", "content": "You are an AI expert."},
            {"role": "user", "content": f"Answer this in 100 words: {context.query}"}
        ]

        response = ""
        stream = await self.client.chat.completions.create(
            messages=prompt, model=MODEL_NAME,
            temperature=0.5, max_completion_tokens=1024, top_p=1, stream=True
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                response += content

        context.response = response
        context.meta.update({
            "model_used": MODEL_NAME,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        return await self.update_trace(context, "MainAgent", "completed")

class Summary(BaseAgent):
    def __init__(self):
        self.client = AsyncGroq()

    async def run(self, context: PipelineContext) -> PipelineContext:
        response = context.response

        summary_prompt = [
            {"role": "system", "content": "Summarize this."},
            {"role": "user", "content": response}
        ]
        summary = ""
        stream = await self.client.chat.completions.create(
            messages=summary_prompt, model=MODEL_NAME,
            temperature=0.5, max_completion_tokens=300, top_p=1, stream=True
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                summary += content
        context.summary = summary

        subject_prompt = [
            {"role": "system", "content": "Return only an email subject."},
            {"role": "user", "content": summary}
        ]
        subject = ""
        stream = await self.client.chat.completions.create(
            messages=subject_prompt, model=MODEL_NAME,
            temperature=0.3, max_completion_tokens=20, top_p=1, stream=True
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                subject += content
        context.subject = subject.strip().strip('"')
        context.email_status = "mocked"
        return await self.update_trace(context, "Summary", "completed")

class SmsAgent(BaseAgent):
    def __init__(self, dev_mode=True):
        self.dev_mode = dev_mode

    async def run(self, context: PipelineContext) -> PipelineContext:
        message = context.summary or context.response
        recipient = context.phone or "unknown"

        if self.dev_mode:
            logger.info(f"[MOCK SMS] Would send to {recipient}:\n{message}")
            context.sms_status = "mocked"
        else:
            context.sms_status = "failed"
        return await self.update_trace(context, "SmsAgent", "completed")

class EmailAgent(BaseAgent):
    async def run(self, context: PipelineContext) -> PipelineContext:
        subject = context.subject or "AI Response"
        body = context.summary or context.response
        status = self.send_email(subject, body)
        context.email_status = status
        return await self.update_trace(context, "EmailAgent", "completed")

    def send_email(self, subject: str, body: str) -> str:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
            logger.info("✅ Email sent successfully.")
            return "success"
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")
            return f"failed: {e}"

# === MAIN ===
async def main():
    retriever = Retriever(file_path=RETRIEVER_FILE_PATH)
    logger.info(retriever.vector_embedding())

    context = PipelineContext(query="what is electroni device", phone="+919123456789")

    pipeline = [
        RetrieverAgent(retriever),
        MainAgent(),
        Summary(),
        SmsAgent(dev_mode=True),
        EmailAgent()
    ]

    for agent in pipeline:
        if isinstance(agent, MainAgent) and context.meta.get("source") == "vectorstore":
            continue
        context = await agent.run(context)

    print(json.dumps({
        "agents": context.trace,
        "final_context": {
            "query": context.query,
            "response": context.response,
            "summary": context.summary,
            "subject": context.subject,
            "phone": context.phone,
            "email_status": context.email_status,
            "sms_status": context.sms_status,
            "meta": context.meta
        }
    }, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
