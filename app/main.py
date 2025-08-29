# with authetication----------------------------------------------------------

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any
from dataclasses import is_dataclass, asdict
import jwt, datetime

from app.core.types import PipelineContext
from app.services.email import EmailService
from app.agents.email_agent import EmailAgent
from app.agents.retriever_agent import RetrieverAgent
from app.services.retriever_singleton import get_retriever_service
from app.agents.main_agent import MainAgent
from app.services.llm import LlmService
from app.agents.summary_agent import SummaryAgent
from app.agents.sms_agent import SmsAgent
from app.services.sms import SmsService
from app.agents.google_sheet_doc_agents import GoogleSheetsAgent, GoogleDocsAgent
from app.agents.createKBagent import CreateKBAgent
from langchain_huggingface import HuggingFaceEmbeddings


# -------------------------------------------------------------------
# Init
# -------------------------------------------------------------------
app = FastAPI(title="Email Agent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# JWT Auth Setup
# -------------------------------------------------------------------
security = HTTPBearer()
JWT_SECRET = "supersecretkey"   # ⚠️ Change in production
JWT_ALGORITHM = "HS256"

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# -------------------------------------------------------------------
# Startup
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    print("[Retriever Init] Skipping FAISS index load. A new index will be created by CreateKBAgent.")
    # Ensure retriever is constructed once on first access
    _ = get_retriever_service()


# -------------------------------------------------------------------
# Agent Registry
# -------------------------------------------------------------------
AGENT_REGISTRY = {
    "retriever": lambda: RetrieverAgent(),
    "main": lambda: MainAgent(LlmService()),
    "email": lambda: EmailAgent(EmailService()),
    "summary": lambda: SummaryAgent(LlmService()),
    "google_sheets": lambda: GoogleSheetsAgent(),
    "google_docs": lambda: GoogleDocsAgent(),
    "create_kb": lambda: CreateKBAgent(),
    # "sms": lambda: SmsAgent(SmsService(dev_mode=True)),
}


# -------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------
class AgentRequest(BaseModel):
    context: Dict[str, Any]

class PipelineRequest(BaseModel):
    agents: list[str]
    context: Dict[str, Any]

class LoginRequest(BaseModel):
    username: str
    password: str


# -------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------
def context_to_dict(context: PipelineContext) -> dict:
    if is_dataclass(context):
        return asdict(context)
    elif hasattr(context, "to_dict"):
        return context.to_dict()
    else:
        return context.__dict__


# -------------------------------------------------------------------
# API Router with prefix /api/v1
# -------------------------------------------------------------------
router = APIRouter(prefix="/api/v1")

@router.get("/health")
async def health():
    return {"status": "ok", "message": "API is running 🚀"}

@router.post("/login")
async def login(request: LoginRequest):
    if request.username == "admin" and request.password == "password123":
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        payload = {"user": request.username, "exp": expiration}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@router.post("/pipeline")
async def run_pipeline(request: PipelineRequest):
    context = PipelineContext(**request.context)
    for agent_id in request.agents:
        if agent_id not in AGENT_REGISTRY:
            return {"error": f"Unknown agent '{agent_id}'"}
        agent = AGENT_REGISTRY[agent_id]()
        context = await agent.run(context)
    return context_to_dict(context)

@router.post("/agent/{agent_id}")
async def run_agent(agent_id: str, request: AgentRequest, payload: dict = Depends(verify_jwt)):
    if agent_id not in AGENT_REGISTRY:
        return {"error": f"Unknown agent '{agent_id}'"}
    context = PipelineContext(**request.context)
    agent = AGENT_REGISTRY[agent_id]()
    context = await agent.run(context)
    return {"agent": agent_id, "context": context_to_dict(context), "user": payload}


# Register router
app.include_router(router)
