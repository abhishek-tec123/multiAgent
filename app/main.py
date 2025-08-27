# import json
# import asyncio
# from typing import AsyncIterator, Dict, Any

# from app.core.logging_utils import get_logger
# from app.core.types import PipelineContext
# from app.core.config import RETRIEVER_FILE_PATH
# from app.services.vector_store import RetrieverService
# from app.services.llm import LlmService
# from app.services.sms import SmsService
# from app.services.email import EmailService
# from app.agents.retriever_agent import RetrieverAgent
# from app.agents.main_agent import MainAgent
# from app.agents.summary_agent import SummaryAgent
# from app.agents.sms_agent import SmsAgent
# from app.agents.email_agent import EmailAgent


# logger = get_logger()


# async def run_pipeline(query: str, phone: str = "") -> dict:
#     retriever = RetrieverService(file_path=RETRIEVER_FILE_PATH)
#     logger.info(retriever.ensure_index())

#     context = PipelineContext(query=query, phone=phone)

#     llm = LlmService()
#     pipeline = [
#         RetrieverAgent(retriever),
#         MainAgent(llm),
#         SummaryAgent(llm),
#         SmsAgent(SmsService(dev_mode=True)),
#         EmailAgent(EmailService()),
#     ]

#     for agent in pipeline:
#         if isinstance(agent, MainAgent) and context.meta.get("source") == "vectorstore":
#             continue
#         context = await agent.run(context)

#     return {
#         "agents": context.trace,
#         "final_context": {
#             "query": context.query,
#             "response": context.response,
#             "summary": context.summary,
#             "subject": context.subject,
#             "phone": context.phone,
#             "email_status": context.email_status,
#             "sms_status": context.sms_status,
#             "meta": context.meta,
#         },
#     }


# async def run_pipeline_stream(query: str, phone: str = "") -> AsyncIterator[Dict[str, Any]]:
#     retriever = RetrieverService(file_path=RETRIEVER_FILE_PATH)
#     logger.info(retriever.ensure_index())

#     context = PipelineContext(query=query, phone=phone)

#     llm = LlmService()
#     pipeline = [
#         RetrieverAgent(retriever),
#         MainAgent(llm),
#         SummaryAgent(llm),
#         SmsAgent(SmsService(dev_mode=True)),
#         EmailAgent(EmailService()),
#     ]

#     for agent in pipeline:
#         if isinstance(agent, MainAgent) and context.meta.get("source") == "vectorstore":
#             # Skip MainAgent if vectorstore already answered
#             continue
#         context = await agent.run(context)
#         yield {
#             "agent": agent.__class__.__name__,
#             "status": "completed",
#             "context": {
#                 "query": context.query,
#                 "response": context.response,
#                 "summary": context.summary,
#                 "subject": context.subject,
#                 "phone": context.phone,
#                 "email_status": context.email_status,
#                 "sms_status": context.sms_status,
#                 "meta": context.meta,
#             },
#         }


# async def main():
#     async for event in run_pipeline_stream("what is electroni device", phone="+919123456789"):
#         print(json.dumps(event, indent=2, ensure_ascii=False))


# if __name__ == "__main__":
#     asyncio.run(main())


# email, sms number take input from user -------------------------------------------------------------------


from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from dataclasses import is_dataclass, asdict

from app.core.types import PipelineContext
from app.services.email import EmailService
from app.agents.email_agent import EmailAgent
from app.agents.retriever_agent import RetrieverAgent
from app.services.vector_store import RetrieverService
from app.agents.main_agent import MainAgent
from app.services.llm import LlmService
from app.agents.summary_agent import SummaryAgent
from app.agents.sms_agent import SmsAgent
from app.services.sms import SmsService

from app.agents.google_sheet_doc_agents import GoogleSheetsAgent, GoogleDocsAgent

retriever_service = RetrieverService()

app = FastAPI(title="Email Agent API", version="1.0")

@app.on_event("startup")
async def startup_event():
    msg = retriever_service.ensure_index()
    print(f"[Retriever Init] {msg}")
# -------------------------------------------------------------------
# Agent Registry
# -------------------------------------------------------------------
AGENT_REGISTRY = {
    "retriever": lambda: RetrieverAgent(retriever_service),  # reuse singleton
    "main": lambda: MainAgent(LlmService()),
    "email": lambda: EmailAgent(EmailService()),
    "summary": lambda: SummaryAgent(LlmService()),

    "google_sheets": lambda: GoogleSheetsAgent(),
    "google_docs": lambda: GoogleDocsAgent(),
}

# -------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------
class AgentRequest(BaseModel):
    context: Dict[str, Any]

# -------------------------------------------------------------------
# Helper to convert PipelineContext -> dict
# -------------------------------------------------------------------
def context_to_dict(context: PipelineContext) -> dict:
    if is_dataclass(context):
        return asdict(context)
    elif hasattr(context, "to_dict"):
        return context.to_dict()
    else:
        return context.__dict__
    
# -------------------------------------------------------------------
# Endpoint: run multiple agents in pipeline
# -------------------------------------------------------------------
class PipelineRequest(BaseModel):
    agents: list[str]
    context: Dict[str, Any]

@app.post("/pipeline")
async def run_pipeline(request: PipelineRequest):
    context = PipelineContext(**request.context)

    for agent_id in request.agents:
        if agent_id not in AGENT_REGISTRY:
            return {"error": f"Unknown agent '{agent_id}'"}
        agent = AGENT_REGISTRY[agent_id]()
        context = await agent.run(context)

    return context_to_dict(context)

# -------------------------------------------------------------------
# Endpoint: run single agent
# -------------------------------------------------------------------
@app.post("/agent/{agent_id}")
async def run_agent(agent_id: str, request: AgentRequest):
    if agent_id not in AGENT_REGISTRY:
        return {"error": f"Unknown agent '{agent_id}'"}

    context = PipelineContext(**request.context)
    agent = AGENT_REGISTRY[agent_id]()
    context = await agent.run(context)

    return {
        "agent": agent_id,
        "context": context_to_dict(context),
    }


#     # "sms": lambda: SmsAgent(SmsService(dev_mode=True)),
