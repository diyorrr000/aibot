import re
from datetime import datetime, timezone, timedelta

UZB_TZ = timezone(timedelta(hours=5))

BOLD_DIGITS = {
    '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
    '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗',
    ':': ':', ' ': ' ',
}

def to_bold_time(time_str: str) -> str:
    return "".join(BOLD_DIGITS.get(c, c) for c in time_str)

def clean_ai_markdown(text: str) -> str:
    """Clean unwanted AI bold markers, translation headers and extra spaces."""
    if not text:
        return ""
    if "\n---\n" in text:
        text = text.split("\n---\n")[0]
    if "**Translation:**" in text:
        text = text.split("**Translation:**")[0]
    if "**Tarjima:**" in text:
        text = text.split("**Tarjima:**")[0]

    # Remove bold/italic markdown
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\*{1,2}', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def get_uzb_now() -> datetime:
    return datetime.now(UZB_TZ)
