# from app.agents.base import BaseAgent
# from app.core.types import PipelineContext
# from app.services.llm import LlmService


# class SummaryAgent(BaseAgent):
#     def __init__(self, llm: LlmService):
#         self.llm = llm

#     async def run(self, context: PipelineContext) -> PipelineContext:
#         response = context.response or ""

#         summary_prompt = [
#             {"role": "system", "content": "Summarize this in 25 words."},
#             {"role": "user", "content": response},
#         ]
#         summary = ""
#         async for chunk in self.llm.stream_completion(summary_prompt, max_tokens=300):
#             if chunk:
#                 summary += chunk
#         context.summary = summary

#         subject_prompt = [
#             {"role": "system", "content": "Return only an email subject."},
#             {"role": "user", "content": summary},
#         ]
#         subject = ""
#         async for chunk in self.llm.stream_completion(subject_prompt, max_tokens=20):
#             if chunk:
#                 subject += chunk
#         context.subject = subject.strip().strip('"')
#         return await self.update_trace(context, "SummaryAgent", "completed")


from app.agents.base import BaseAgent
from app.core.types import PipelineContext
from app.services.llm import LlmService


class SummaryAgent(BaseAgent):
    def __init__(self, llm: LlmService):
        self.llm = llm

    async def run(self, context: PipelineContext) -> PipelineContext:
        # Always summarize text from query
        text_to_summarize = context.query or ""

        if not text_to_summarize.strip():
            context.summary = "❌ No input text provided for summarization."
            return await self.update_trace(context, "SummaryAgent", "failed")

        # Summarization
        summary_prompt = [
            {"role": "system", "content": "Summarize this text in about 25 words."},
            {"role": "user", "content": text_to_summarize},
        ]
        summary = ""
        async for chunk in self.llm.stream_completion(summary_prompt, max_tokens=300):
            if chunk:
                summary += chunk
        context.summary = summary.strip()

        # Subject generation
        subject_prompt = [
            {"role": "system", "content": "Return only an email subject for the summarized text."},
            {"role": "user", "content": context.summary},
        ]
        subject = ""
        async for chunk in self.llm.stream_completion(subject_prompt, max_tokens=20):
            if chunk:
                subject += chunk
        context.subject = subject.strip().strip('"')

        return await self.update_trace(context, "SummaryAgent", "completed")
