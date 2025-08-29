from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from dataclasses import is_dataclass, asdict

from app.core.types import PipelineContext
from app.core.config import RETRIEVER_FILE_PATH
from app.services.reterever import RetrieverService
from app.services.llm import LlmService
from app.services.sms import SmsService
from app.services.email import EmailService
from app.agents.retriever_agent import RetrieverAgent
from app.agents.main_agent import MainAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.sms_agent import SmsAgent
from app.agents.email_agent import EmailAgent

# -------------------------------------------------------------------
# 1. Global Retriever Instance
# -------------------------------------------------------------------
retriever_service = RetrieverService()

# -------------------------------------------------------------------
# 2. Agent Registry
# -------------------------------------------------------------------
AGENT_REGISTRY = {
    "retriever": lambda: RetrieverAgent(retriever_service),  # reuse singleton
    "main": lambda: MainAgent(LlmService()),
    "summary": lambda: SummaryAgent(LlmService()),
    "sms": lambda: SmsAgent(SmsService(dev_mode=True)),
    "email": lambda: EmailAgent(EmailService()),
}

# -------------------------------------------------------------------
# 3. FastAPI App
# -------------------------------------------------------------------
app = FastAPI(title="Agent API", version="1.0")

# -------------------------------------------------------------------
# 4. Startup Event
# -------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    msg = retriever_service.ensure_index()
    print(f"[Retriever Init] {msg}")

# -------------------------------------------------------------------
# 5. Request & Response Models
# -------------------------------------------------------------------
class AgentRequest(BaseModel):
    context: Dict[str, Any]

class PipelineRequest(BaseModel):
    agents: list[str]
    context: Dict[str, Any]

# -------------------------------------------------------------------
# 6. Helper to Convert PipelineContext -> dict
# -------------------------------------------------------------------
def context_to_dict(context: PipelineContext) -> dict:
    if is_dataclass(context):
        return asdict(context)
    elif hasattr(context, "to_dict"):
        return context.to_dict()
    else:
        return context.__dict__

# -------------------------------------------------------------------
# 7. Endpoints
# -------------------------------------------------------------------
@app.post("/agent/{agent_id}")
async def run_agent(agent_id: str, request: AgentRequest):
    """
    Run a single agent by ID.
    """
    if agent_id not in AGENT_REGISTRY:
        return {"error": f"Unknown agent '{agent_id}'"}

    context = PipelineContext(**request.context)
    agent = AGENT_REGISTRY[agent_id]()
    context = await agent.run(context)

    return {
        "agent": agent_id,
        "context": context_to_dict(context),
    }

@app.post("/pipeline")
async def run_pipeline(request: PipelineRequest):
    """
    Run multiple agents in sequence.
    Example:
    {
      "agents": ["retriever", "main", "summary", "sms"],
      "context": {"query": "hello", "phone": "+919123456789"}
    }
    """
    context = PipelineContext(**request.context)

    for agent_id in request.agents:
        if agent_id not in AGENT_REGISTRY:
            return {"error": f"Unknown agent '{agent_id}'"}
        agent = AGENT_REGISTRY[agent_id]()
        context = await agent.run(context)

    return context_to_dict(context)

# -------------------------------------------------------------------
# 8. Maintenance Endpoint - Rebuild Index
# -------------------------------------------------------------------
@app.post("/rebuild-index")
async def rebuild_index():
    """
    Rebuild FAISS index from api.txt
    """
    retriever_service.vectors = None
    msg = retriever_service.ensure_index()
    return {"status": "ok", "message": msg}


# # with redis----------------------------------------------------------------------------------


# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import Dict, Any
# from dataclasses import is_dataclass, asdict

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

# # Redis helper
# from app.core.redis_store import save_context, load_context, delete_context

# # -----------------------------
# # Global Retriever Instance
# # -----------------------------
# retriever_service = RetrieverService()

# # -----------------------------
# # Agent Registry
# # -----------------------------
# AGENT_REGISTRY = {
#     "retriever": lambda: RetrieverAgent(retriever_service),
#     "main": lambda: MainAgent(LlmService()),
#     "summary": lambda: SummaryAgent(LlmService()),
#     "sms": lambda: SmsAgent(SmsService(dev_mode=True)),
#     "email": lambda: EmailAgent(EmailService()),
# }

# # -----------------------------
# # FastAPI App
# # -----------------------------
# app = FastAPI(title="Multi-Agent API", version="1.0")

# # -----------------------------
# # Startup Event - Load FAISS Index
# # -----------------------------
# @app.on_event("startup")
# async def startup_event():
#     msg = retriever_service.ensure_index()
#     print(f"[Retriever Init] {msg}")

# # -----------------------------
# # Request Models
# # -----------------------------
# class AgentRequest(BaseModel):
#     session_id: str
#     context: Dict[str, Any]

# class PipelineRequest(BaseModel):
#     session_id: str
#     agents: list[str]
#     context: Dict[str, Any]

# # -----------------------------
# # Helper: Convert Context -> Dict
# # -----------------------------
# def context_to_dict(context: PipelineContext) -> dict:
#     if is_dataclass(context):
#         return asdict(context)
#     elif hasattr(context, "to_dict"):
#         return context.to_dict()
#     else:
#         return context.__dict__

# # -----------------------------
# # Single Agent Endpoint
# # -----------------------------
# @app.post("/agent/{agent_id}")
# async def run_agent(agent_id: str, request: AgentRequest):
#     if agent_id not in AGENT_REGISTRY:
#         return {"error": f"Unknown agent '{agent_id}'"}

#     # Load previous context from Redis or create new
#     context = load_context(request.session_id) or PipelineContext(**request.context)

#     # Run agent
#     agent = AGENT_REGISTRY[agent_id]()
#     context = await agent.run(context)

#     # Save updated context to Redis (1 hour TTL)
#     save_context(request.session_id, context, ttl=3600)

#     return {"agent": agent_id, "context": context_to_dict(context)}

# # -----------------------------
# # Pipeline Endpoint
# # -----------------------------
# @app.post("/pipeline")
# async def run_pipeline(request: PipelineRequest):
#     context = load_context(request.session_id) or PipelineContext(**request.context)

#     for agent_id in request.agents:
#         if agent_id not in AGENT_REGISTRY:
#             return {"error": f"Unknown agent '{agent_id}'"}
#         agent = AGENT_REGISTRY[agent_id]()
#         context = await agent.run(context)

#     save_context(request.session_id, context, ttl=3600)
#     return context_to_dict(context)

# # -----------------------------
# # Rebuild FAISS Index
# # -----------------------------
# @app.post("/rebuild-index")
# async def rebuild_index():
#     retriever_service.vectors = None
#     msg = retriever_service.ensure_index()
#     return {"status": "ok", "message": msg}

# # -----------------------------
# # Inspect Session Context
# # -----------------------------
# @app.get("/session/{session_id}")
# async def get_session(session_id: str):
#     context = load_context(session_id)
#     if not context:
#         return {"error": f"No session found for id '{session_id}'"}
#     return {"session_id": session_id, "context": context_to_dict(context)}

# # -----------------------------
# # Delete Session
# # -----------------------------
# @app.delete("/session/{session_id}")
# async def delete_session(session_id: str):
#     delete_context(session_id)
#     return {"status": "ok", "message": f"Session '{session_id}' deleted"}
