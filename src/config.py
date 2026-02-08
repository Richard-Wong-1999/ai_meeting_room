from __future__ import annotations

import os
import sys

from dotenv import load_dotenv


def require_api_key() -> str:
    """Load .env and return POE_API_KEY, or exit with error."""
    load_dotenv()
    key = os.environ.get("POE_API_KEY", "").strip()
    if not key:
        print(
            "錯誤：未設定 POE_API_KEY 環境變數。\n"
            "請建立 .env 檔案並設定 POE_API_KEY=your_key，或以 export 匯出。",
            file=sys.stderr,
        )
        sys.exit(1)
    return key
