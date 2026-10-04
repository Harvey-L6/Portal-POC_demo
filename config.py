"""公開 demo 的本機設定；真實值放在不受 Git 追蹤的 .env。"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
MOCK_NAS = BASE_DIR / "mock_storage" / "nas"

def setting(name, default=""):
    value = os.getenv(name, default).strip()
    if value.startswith(("請輸入", "YOUR_")):
        return ""
    return value

GEMINI_API_KEY = setting("GEMINI_API_KEY")
GDRIVE_FOLDER_ID = setting("GDRIVE_FOLDER_ID")
AI_MODEL_VERSION = setting("GEMINI_MODEL") or "gemini-3.1-flash-lite"
