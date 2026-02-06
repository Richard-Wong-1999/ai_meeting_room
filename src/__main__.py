import asyncio
import sys

from .config import require_api_key
from .setup import run_setup
from .app import MeetingApp


def main() -> None:
    api_key = require_api_key()
    config = asyncio.run(run_setup(api_key))
    if config is None:
        print("已取消。")
        sys.exit(0)
    app = MeetingApp(config, api_key)
    app.run()


main()
