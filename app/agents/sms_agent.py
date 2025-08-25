from app.agents.base import BaseAgent
from app.core.types import PipelineContext
from app.services.sms import SmsService


class SmsAgent(BaseAgent):
    def __init__(self, sms: SmsService):
        self.sms = sms

    async def run(self, context: PipelineContext) -> PipelineContext:
        message = context.summary or context.response or ""
        recipient = context.phone or "unknown"
        context.sms_status = self.sms.send(recipient, message)
        return await self.update_trace(context, "SmsAgent", "completed")


