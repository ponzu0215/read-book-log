"""汎用ユーティリティ関数。"""

from datetime import datetime, date
from typing import Any, Optional


def format_date_jp(dt: Any) -> str:
    """Firestore Timestamp または datetime を日本語日付文字列に変換する。"""
    if dt is None:
        return "不明"
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y年%m月%d日")
    return str(dt)


def to_date(dt: Any) -> Optional[date]:
    """Firestore Timestamp または datetime を date に変換する。"""
    if dt is None:
        return None
    if hasattr(dt, "date"):
        return dt.date()
    if isinstance(dt, date):
        return dt
    return None


def clamp_rating(value: int, min_val: int = 1, max_val: int = 5) -> int:
    """評価値を 1〜5 にクランプする。"""
    return max(min_val, min(max_val, value))
