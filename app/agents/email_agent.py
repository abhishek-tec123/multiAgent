# from app.agents.base import BaseAgent
# from app.core.types import PipelineContext
# from app.services.email import EmailService


# class EmailAgent(BaseAgent):
#     def __init__(self, email: EmailService):
#         self.email = email

#     async def run(self, context: PipelineContext) -> PipelineContext:
#         subject = context.subject or "AI Response"
#         body = context.summary or context.response or ""
#         status = self.email.send_email(subject, body)
#         context.email_status = status
#         return await self.update_trace(context, "EmailAgent", "completed")


from app.core.types import PipelineContext
from app.services.email import EmailService

class EmailAgent:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def run(self, context: PipelineContext) -> PipelineContext:
        subject = getattr(context, "subject", "No Subject")
        body = getattr(context, "body", "No Body")
        to_email = getattr(context, "to_email", None)

        if not to_email:
            context.email_status = "failed: no recipient email provided"
            return context

        status = self.email_service.send_email(subject, body, to_email)
        context.email_status = status
        return context
