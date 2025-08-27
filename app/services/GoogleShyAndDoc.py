# import gspread
# import logging
# from oauth2client.service_account import ServiceAccountCredentials
# from googleapiclient.discovery import build

# # -------------------------
# # Logger Setup
# # -------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S"
# )
# logger = logging.getLogger(__name__)

# def _connect_to_google_sheet(json_key_file, sheet_url):
#     try:
#         scope = [
#             "https://spreadsheets.google.com/feeds",
#             "https://www.googleapis.com/auth/drive"
#         ]
#         creds = ServiceAccountCredentials.from_json_keyfile_name(
#             json_key_file, scope
#         )
#         client = gspread.authorize(creds)
#         sheet = client.open_by_url(sheet_url).sheet1
#         logger.info("✅ Connected to Google Sheet successfully")
#         return sheet
#     except Exception as e:
#         logger.error(f"❌ Failed to connect to Google Sheet: {e}")
#         raise


# def _connect_to_google_doc(json_key_file, doc_id):
#     try:
#         scope = ["https://www.googleapis.com/auth/documents.readonly"]
#         creds = ServiceAccountCredentials.from_json_keyfile_name(
#             json_key_file, scope
#         )
#         service = build("docs", "v1", credentials=creds)
#         logger.info("✅ Connected to Google Doc successfully")
#         return service
#     except Exception as e:
#         logger.error(f"❌ Failed to connect to Google Doc: {e}")
#         raise

# # -------------------------
# # Google Sheets Handler
# # -------------------------
# class GoogleSheetsHandler:
#     def __init__(self, json_key_file, sheet_url):
#         self.json_key_file = json_key_file
#         self.sheet_url = sheet_url
#         self.sheet = _connect_to_google_sheet(json_key_file, sheet_url)

#     def _connect(self):
#         try:
#             scope = [
#                 "https://spreadsheets.google.com/feeds",
#                 "https://www.googleapis.com/auth/drive"
#             ]
#             creds = ServiceAccountCredentials.from_json_keyfile_name(
#                 self.json_key_file, scope
#             )
#             client = gspread.authorize(creds)
#             sheet = client.open_by_url(self.sheet_url).sheet1
#             logger.info("✅ Connected to Google Sheet successfully")
#             return sheet
#         except Exception as e:
#             logger.error(f"❌ Failed to connect to Google Sheet: {e}")
#             raise

#     def read(self):
#         try:
#             data = self.sheet.get_all_records()
#             logger.info("📊 Reading Google Sheet data")
#             for row in data:
#                 # logger.info(row)
#                 return data
#         except Exception as e:
#             logger.error(f"❌ Failed to read sheet: {e}")
#             raise

#     def write(self, row_data):
#         try:
#             self.sheet.append_row(row_data)
#             logger.info(f"✅ Row added: {row_data}")
#         except Exception as e:
#             logger.error(f"❌ Failed to write row: {e}")
#             raise

#     def delete(self, row_number):
#         try:
#             self.sheet.delete_rows(row_number)
#             logger.info(f"🗑️ Row {row_number} deleted successfully")
#         except Exception as e:
#             logger.error(f"❌ Failed to delete row {row_number}: {e}")
#             raise

# # -------------------------
# # Google Docs Handler
# # -------------------------
# class GoogleDocsHandler:
#     def __init__(self, json_key_file, doc_id):
#         self.json_key_file = json_key_file
#         self.doc_id = doc_id
#         self.service = _connect_to_google_doc(json_key_file, doc_id)

#     def read(self):
#         try:
#             document = self.service.documents().get(documentId=self.doc_id).execute()
#             title = document.get("title")
#             logger.info(f"📄 Google Doc Title: {title}")

#             logger.info("📄 Reading Google Doc content...")
#             text_content = []
#             for content in document.get("body", {}).get("content", []):
#                 if "paragraph" in content:
#                     elements = content["paragraph"]["elements"]
#                     for elem in elements:
#                         if "textRun" in elem:
#                             text_content.append(elem["textRun"]["content"])

#             full_text = "".join(text_content)
#             logger.info("✅ Document read successfully")
#             return full_text
#         except Exception as e:
#             logger.error(f"❌ Failed to read Google Doc: {e}")
#             raise

# # -------------------------
# # Main
# # -------------------------
# # def main():
# #     json_key_file = input("Enter path to your JSON key file: ").strip()
# #     sheet_url = input("Enter Google Sheet URL: ").strip()

# #     # Google Sheets operations
# #     sheets = GoogleSheetsHandler(json_key_file, sheet_url)
# #     # sheets.read()
# #     # sheets.write(["Charlie", "28", "Berlin"])
# #     # sheets.delete(2)
# #     sheets.read()

# #     # Google Docs operations
# #     doc_id = input("Enter Google Doc ID (from its URL): ").strip()
# #     docs = GoogleDocsHandler(json_key_file, doc_id)
# #     content = docs.read()
# #     print("\n--- Google Doc Content ---\n")
# #     print(content)

# # if __name__ == "__main__":
# #     main()

# hybrid solution:
# If the Google Sheet/Doc is public → fetch data without authentication.
# If it’s private → fall back to using the JSON key (service account).

import requests
import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from io import StringIO

# -------------------------
# Logger Setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# -------------------------
# Sheets Handler
# -------------------------
class GoogleSheetsHandler:
    def __init__(self, sheet_url, json_key_file=None):
        self.sheet_url = sheet_url
        self.json_key_file = json_key_file
        self.sheet = None

    def _connect_private(self):
        """Connect using Service Account (for private sheets)."""
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.json_key_file, scope
        )
        client = gspread.authorize(creds)
        self.sheet = client.open_by_url(self.sheet_url).sheet1
        logger.info("✅ Connected to PRIVATE Google Sheet successfully")

    def read(self):
        """Try public access first; if fails, fallback to private auth."""
        try:
            # Extract Sheet ID
            sheet_id = self.sheet_url.split("/d/")[1].split("/")[0]
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"

            response = requests.get(url)
            if response.status_code == 200 and "html" not in response.text.lower():
                df = pd.read_csv(StringIO(response.text))
                logger.info("📊 Read PUBLIC Google Sheet successfully")
                return df.to_dict(orient="records")
            else:
                raise Exception("Not a public sheet, trying private...")
        except Exception:
            if not self.json_key_file:
                raise Exception("❌ Sheet is private. Please provide a JSON key file.")
            self._connect_private()
            data = self.sheet.get_all_records()
            return data


# -------------------------
# Docs Handler
# -------------------------
class GoogleDocsHandler:
    def __init__(self, doc_id, json_key_file=None):
        self.doc_id = doc_id
        self.json_key_file = json_key_file
        self.service = None

    def _connect_private(self):
        """Connect using Service Account (for private docs)."""
        scope = ["https://www.googleapis.com/auth/documents.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.json_key_file, scope
        )
        self.service = build("docs", "v1", credentials=creds)
        logger.info("✅ Connected to PRIVATE Google Doc successfully")

    def read(self):
        """Try public access first; if fails, fallback to private auth."""
        try:
            # Public Docs can be published as HTML
            url = f"https://docs.google.com/document/d/{self.doc_id}/export?format=txt"
            response = requests.get(url)

            if response.status_code == 200:
                logger.info("📄 Read PUBLIC Google Doc successfully")
                return response.text
            else:
                raise Exception("Not a public doc, trying private...")
        except Exception:
            if not self.json_key_file:
                raise Exception("❌ Doc is private. Please provide a JSON key file.")
            self._connect_private()
            try:
                document = self.service.documents().get(documentId=self.doc_id).execute()
                text_content = []
                for content in document.get("body", {}).get("content", []):
                    if "paragraph" in content:
                        elements = content["paragraph"]["elements"]
                        for elem in elements:
                            if "textRun" in elem:
                                text_content.append(elem["textRun"]["content"])
                return "".join(text_content)
            except HttpError as e:
                logger.error(f"❌ Failed to read private Google Doc: {e}")
                raise

# Public Sheet Example
# sheet_url = "https://docs.google.com/spreadsheets/d/1zt-IMn-oYt1ZpVycvBCxIIE1on3RRprTqluaACoN3gw/edit?gid=847287878#gid=847287878"
# sheets = GoogleSheetsHandler(sheet_url)
# print(sheets.read())   # Works if public, else asks for JSON

# # Public Doc Example
# doc_id = "your_doc_id"
# docs = GoogleDocsHandler(doc_id)
# print(docs.read())     # Works if published, else asks for JSON
