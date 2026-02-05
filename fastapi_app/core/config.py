import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

HISTORY_PATH = PROJECT_ROOT / "history.json"

GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID", "")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET", "")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")
GIGACHAT_CA_CERT = os.getenv("GIGACHAT_CA_CERT", "")
GIGACHAT_SKIP_VERIFY = os.getenv("GIGACHAT_SKIP_VERIFY", "").strip().lower() in {
    "1",
    "true",
    "yes",
}

YC_API_KEY = os.getenv("YC_API_KEY", "")
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")
YC_ART_MODEL_URI = os.getenv(
    "YC_ART_MODEL_URI", f"art://{YC_FOLDER_ID}/yandex-art/latest" if YC_FOLDER_ID else ""
)
YC_SKIP_VERIFY = os.getenv("YC_SKIP_VERIFY", "").strip().lower() in {"1", "true", "yes"}

CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", "")
