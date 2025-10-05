from __future__ import annotations
import os

API_BASE: str = os.getenv("FR_API_BASE", "http://localhost:8000")
DASH_TITLE: str = os.getenv("FR_DASH_TITLE", "FIFTH REFEREE")

DEFAULT_LAST_N: int = int(os.getenv("FR_LAST_N", "5"))
DEFAULT_NEXT_K: int = int(os.getenv("FR_NEXT_K", "5"))

FEATURE_LEADERS: bool = os.getenv("FR_FEATURE_LEADERS", "true").lower() in ("1","true","yes")
FEATURE_COMPARE: bool = os.getenv("FR_FEATURE_COMPARE", "false").lower() in ("1","true","yes")
