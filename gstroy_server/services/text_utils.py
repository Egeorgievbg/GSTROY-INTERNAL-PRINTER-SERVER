import re
from typing import Any


def clean_text(text: Any) -> str:
    if not text:
        return ""
    return str(text).replace("^", "").replace("~", "").replace("\n", " ").strip()


def format_smart_numbers(text: str) -> str:
    if not text:
        return ""

    def replacer(match):
        num_str = match.group()
        try:
            value = float(num_str)
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}".rstrip("0").rstrip(".")
        except ValueError:
            return num_str

    return re.sub(r"\d+\.\d+", replacer, text)
