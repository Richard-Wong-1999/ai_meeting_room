from __future__ import annotations

import os
import sys
import warnings
from collections import Counter
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .models import AppConfig


def load_config(path: str | Path = "meeting_config.yaml") -> AppConfig:
    """Load and validate meeting configuration from YAML."""
    path = Path(path)
    if not path.exists():
        print(f"Error: config file not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"Error: invalid YAML in {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        config = AppConfig.model_validate(raw)
    except Exception as exc:
        print(f"Error: config validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    _validate_business_rules(config)
    return config


def _validate_business_rules(config: AppConfig) -> None:
    """Check duplicate names, priorities; warn on duplicate models."""
    names = [p.name for p in config.participants]
    name_dupes = [n for n, c in Counter(names).items() if c > 1]
    if name_dupes:
        print(
            f"Error: duplicate participant names: {', '.join(name_dupes)}",
            file=sys.stderr,
        )
        sys.exit(1)

    priorities = [p.priority for p in config.participants]
    prio_dupes = [str(p) for p, c in Counter(priorities).items() if c > 1]
    if prio_dupes:
        print(
            f"Error: duplicate priorities: {', '.join(prio_dupes)}",
            file=sys.stderr,
        )
        sys.exit(1)

    models = [p.model for p in config.participants]
    model_dupes = [m for m, c in Counter(models).items() if c > 1]
    if model_dupes:
        warnings.warn(
            f"Multiple participants share model(s): {', '.join(model_dupes)}",
            stacklevel=2,
        )


def require_api_key() -> str:
    """Load .env and return POE_API_KEY, or exit with error."""
    load_dotenv()
    key = os.environ.get("POE_API_KEY", "").strip()
    if not key:
        print(
            "Error: POE_API_KEY environment variable is not set.\n"
            "Create a .env file with POE_API_KEY=your_key or export it.",
            file=sys.stderr,
        )
        sys.exit(1)
    return key
