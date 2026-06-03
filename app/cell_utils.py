from datetime import datetime, time

import pandas as pd

EMPTY_TOKENS = frozenset({"", "nan", "none", "nat", "<na>", "null"})
SPURIOUS_EMPTY_DISPLAY = frozenset(
    {
        "0",
        "0.0",
        "0:00",
        "00:00",
        "0:00:00",
        "00:00:00",
        "00.00",
        "0.00",
    }
)


def is_empty_value(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, str):
        text = value.strip().casefold()
        return text in EMPTY_TOKENS or text in {item.casefold() for item in SPURIOUS_EMPTY_DISPLAY}
    if isinstance(value, datetime):
        return value.year <= 1910 and value.hour == 0 and value.minute == 0
    if isinstance(value, time):
        return value.hour == 0 and value.minute == 0 and value.second == 0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if pd.isna(value):
            return True
        return float(value) == 0.0
    return False


def normalize_cell(value) -> str:
    if is_empty_value(value):
        return ""
    if isinstance(value, time):
        return f"{value.hour:02d}.{value.minute:02d}"
    if isinstance(value, datetime):
        if value.year <= 1910:
            if value.hour == 0 and value.minute == 0:
                return ""
            return f"{value.hour:02d}.{value.minute:02d}"
        if value.hour == 0 and value.minute == 0 and value.second == 0:
            return value.strftime("%d.%m.%Y")
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, float):
        if 0 < value < 1:
            total_minutes = int(round(value * 24 * 60))
            if total_minutes == 0:
                return ""
            hours, minutes = divmod(total_minutes, 60)
            return f"{hours:02d}.{minutes:02d}"
        if value.is_integer():
            return str(int(value))
    text = str(value).strip()
    if text.casefold() in EMPTY_TOKENS or text in SPURIOUS_EMPTY_DISPLAY:
        return ""
    return text


def format_cell(value) -> str:
    return normalize_cell(value)
