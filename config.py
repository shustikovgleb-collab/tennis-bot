import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")  # JSON-строка с ключом

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID не задан в .env")
if not SPREADSHEET_ID:
    raise ValueError("SPREADSHEET_ID не задан в .env")
if not GOOGLE_CREDENTIALS_JSON:
    raise ValueError("GOOGLE_CREDENTIALS_JSON не задан в .env")
