import json
import redis
from dataclasses import asdict, is_dataclass
from app.core.types import PipelineContext

# -----------------------------
# Redis Cloud Credentials
# -----------------------------
REDIS_HOST = "redis-14714.c90.us-east-1-3.ec2.redns.redis-cloud.com"
REDIS_PORT = 14714
REDIS_PASSWORD = "1v6D0dGsoGqlLcBXXji3ZoxpI4m2TAru"

# Connect to Redis Cloud
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

SESSION_PREFIX = "agent_session:"

# -----------------------------
# Helper functions
# -----------------------------
def context_to_dict(context: PipelineContext) -> dict:
    if is_dataclass(context):
        return asdict(context)
    elif hasattr(context, "to_dict"):
        return context.to_dict()
    else:
        return context.__dict__

def save_context(session_id: str, context: PipelineContext, ttl: int = 3600):
    """Save context to Redis with TTL"""
    key = f"{SESSION_PREFIX}{session_id}"
    redis_client.setex(key, ttl, json.dumps(context_to_dict(context)))

def load_context(session_id: str) -> PipelineContext | None:
    """Load context from Redis"""
    key = f"{SESSION_PREFIX}{session_id}"
    data = redis_client.get(key)
    if not data:
        return None
    return PipelineContext(**json.loads(data))

def delete_context(session_id: str):
    """Delete session"""
    key = f"{SESSION_PREFIX}{session_id}"
    redis_client.delete(key)
