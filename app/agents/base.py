from abc import ABC, abstractmethod

from app.core.types import PipelineContext


class BaseAgent(ABC):
    @abstractmethod
    async def run(self, context: PipelineContext) -> PipelineContext:
        raise NotImplementedError

    async def update_trace(self, context: PipelineContext, agent_name: str, status: str) -> PipelineContext:
        context.trace.append({"agent": agent_name, "status": status})
        return context


