import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

# Email/SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "sender@example.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your-app-password")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "receiver@example.com")

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # points to /Users/abhishek/Desktop/multiAgentAI/app

FAISS_INDEX_PATH = os.getenv(
    "FAISS_INDEX_PATH",
    os.path.join(PROJECT_ROOT, "faiss_index"),  # ✅ updated
)

RETRIEVER_FILE_PATH = os.getenv(
    "RETRIEVER_FILE_PATH",
    os.path.join(PROJECT_ROOT, "api.txt"),  # ✅ updated
)

# Misc
os.environ["TOKENIZERS_PARALLELISM"] = "false"
