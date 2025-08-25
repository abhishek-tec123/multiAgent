import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

# -------------------------
# Logger Setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def _connect_to_google_sheet(json_key_file, sheet_url):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            json_key_file, scope
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1
        logger.info("✅ Connected to Google Sheet successfully")
        return sheet
    except Exception as e:
        logger.error(f"❌ Failed to connect to Google Sheet: {e}")
        raise


def _connect_to_google_doc(json_key_file, doc_id):
    try:
        scope = ["https://www.googleapis.com/auth/documents.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            json_key_file, scope
        )
        service = build("docs", "v1", credentials=creds)
        logger.info("✅ Connected to Google Doc successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to connect to Google Doc: {e}")
        raise

# -------------------------
# Google Sheets Handler
# -------------------------
class GoogleSheetsHandler:
    def __init__(self, json_key_file, sheet_url):
        self.json_key_file = json_key_file
        self.sheet_url = sheet_url
        self.sheet = _connect_to_google_sheet(json_key_file, sheet_url)

    def _connect(self):
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.json_key_file, scope
            )
            client = gspread.authorize(creds)
            sheet = client.open_by_url(self.sheet_url).sheet1
            logger.info("✅ Connected to Google Sheet successfully")
            return sheet
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheet: {e}")
            raise

    def read(self):
        try:
            data = self.sheet.get_all_records()
            logger.info("📊 Reading Google Sheet data")
            for row in data:
                logger.info(row)
            return data
        except Exception as e:
            logger.error(f"❌ Failed to read sheet: {e}")
            raise

    def write(self, row_data):
        try:
            self.sheet.append_row(row_data)
            logger.info(f"✅ Row added: {row_data}")
        except Exception as e:
            logger.error(f"❌ Failed to write row: {e}")
            raise

    def delete(self, row_number):
        try:
            self.sheet.delete_rows(row_number)
            logger.info(f"🗑️ Row {row_number} deleted successfully")
        except Exception as e:
            logger.error(f"❌ Failed to delete row {row_number}: {e}")
            raise

# -------------------------
# Google Docs Handler
# -------------------------
class GoogleDocsHandler:
    def __init__(self, json_key_file, doc_id):
        self.json_key_file = json_key_file
        self.doc_id = doc_id
        self.service = _connect_to_google_doc(json_key_file, doc_id)

    def read(self):
        try:
            document = self.service.documents().get(documentId=self.doc_id).execute()
            title = document.get("title")
            logger.info(f"📄 Google Doc Title: {title}")

            logger.info("📄 Reading Google Doc content...")
            text_content = []
            for content in document.get("body", {}).get("content", []):
                if "paragraph" in content:
                    elements = content["paragraph"]["elements"]
                    for elem in elements:
                        if "textRun" in elem:
                            text_content.append(elem["textRun"]["content"])

            full_text = "".join(text_content)
            logger.info("✅ Document read successfully")
            return full_text
        except Exception as e:
            logger.error(f"❌ Failed to read Google Doc: {e}")
            raise

# -------------------------
# Main
# -------------------------
# def main():
#     json_key_file = input("Enter path to your JSON key file: ").strip()
#     sheet_url = input("Enter Google Sheet URL: ").strip()

#     # Google Sheets operations
#     sheets = GoogleSheetsHandler(json_key_file, sheet_url)
#     # sheets.read()
#     # sheets.write(["Charlie", "28", "Berlin"])
#     # sheets.delete(2)
#     sheets.read()

#     # Google Docs operations
#     doc_id = input("Enter Google Doc ID (from its URL): ").strip()
#     docs = GoogleDocsHandler(json_key_file, doc_id)
#     content = docs.read()
#     print("\n--- Google Doc Content ---\n")
#     print(content)

# if __name__ == "__main__":
#     main()
