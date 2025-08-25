# from app.services.GoogleShyAndDoc import GoogleSheetsHandler
# from app.services.GoogleShyAndDoc import GoogleDocsHandler

# # json_path = "/Users/abhishek/Desktop/multiAgentAI/gen-lang-client-0562348499-ab2d48999dfe.json"

# def read_google_sheet(json_key_file: str, sheet_url: str) -> str:

#     sheets = GoogleSheetsHandler(json_key_file, sheet_url)
#     data = sheets.read()

#     # Convert list of dicts to pretty string
#     lines = []
#     for row in data:
#         line = " | ".join(f"{k}: {v}" for k, v in row.items())
#         lines.append(line)
    
#     return "\n".join(lines)

# # url = "https://docs.google.com/spreadsheets/d/1zt-IMn-oYt1ZpVycvBCxIIE1on3RRprTqluaACoN3gw/edit?gid=847287878#gid=847287878"
# # sheet__content = read_google_sheet(json_path,url)
# # print(sheet__content)

# def read_google_doc(json_key_file: str, doc_id: str) -> str:

#     docs = GoogleDocsHandler(json_key_file, doc_id)
#     content = docs.read()
#     # Join list of text fragments into one string (if handler returns list)
#     if isinstance(content, list):
#         return "\n".join(content)
#     return str(content)

# # # Example usage
# # doc_id = "1p34JJev0itr5Td8xdxuo-q82T0NcIeEQRBuICk7xUpI"
# # doc_cotent = read_google_doc(json_path, doc_id)
# # print(doc_cotent)




from app.agents.base import BaseAgent
from app.core.types import PipelineContext
from app.services.GoogleShyAndDoc import GoogleSheetsHandler, GoogleDocsHandler


JSON_KEY_FILE = "/Users/abhishek/Desktop/multiAgentAI/gen-lang-client-0562348499-ab2d48999dfe.json"


class GoogleSheetsAgent(BaseAgent):
    def __init__(self, json_key_file: str = JSON_KEY_FILE):
        self.json_key_file = json_key_file

    async def run(self, context: PipelineContext) -> PipelineContext:
        if not context.meta.get("sheet_url"):
            context.response = "Missing 'sheet_url' in request context"
            return await self.update_trace(context, "GoogleSheetsAgent", "failed")

        sheet_url = context.meta["sheet_url"]
        sheets = GoogleSheetsHandler(self.json_key_file, sheet_url)
        data = sheets.read()
        # Convert list of dicts to pretty string
        lines = [" | ".join(f"{k}: {v}" for k, v in row.items()) for row in data]
        context.response = "\n".join(lines)
        return await self.update_trace(context, "GoogleSheetsAgent", "completed")


class GoogleDocsAgent(BaseAgent):
    def __init__(self, json_key_file: str = JSON_KEY_FILE):
        self.json_key_file = json_key_file

    async def run(self, context: PipelineContext) -> PipelineContext:
        if not context.meta.get("doc_id"):
            context.response = "Missing 'doc_id' in request context"
            return await self.update_trace(context, "GoogleDocsAgent", "failed")

        doc_id = context.meta["doc_id"]
        docs = GoogleDocsHandler(self.json_key_file, doc_id)
        content = docs.read()

        if isinstance(content, list):
            context.response = "\n".join(content)
        else:
            context.response = str(content)

        return await self.update_trace(context, "GoogleDocsAgent", "completed")
