import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "my_documents")

HELPDESK_EMAIL = os.getenv("HELPDESK_EMAIL")
# Reserved for future real email sending (not used yet: the demo only drafts emails)
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SEND_REAL_EMAILS = os.getenv("SEND_REAL_EMAILS", "false").lower() == "true"