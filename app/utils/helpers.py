import re
import html
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
    """Safely convert AI markdown into Telegram Rich HTML Messages with full entity escaping."""
    if not text:
        return ""

    if "\n---\n" in text:
        text = text.split("\n---\n")[0]
    if "**Translation:**" in text:
        text = text.split("**Translation:**")[0]
    if "**Tarjima:**" in text:
        text = text.split("**Tarjima:**")[0]

    code_blocks = []
    def save_code_block(match):
        code = html.escape(match.group(1).strip())
        code_blocks.append(f'<pre><code>{code}</code></pre>')
        return f'___CODE_BLOCK_{len(code_blocks)-1}___'

    text = re.sub(r'```(?:\w+)?\n?(.*?)```', save_code_block, text, flags=re.DOTALL)
    text = html.escape(text)

    text = re.sub(r'^#{1,3}\s+(.+)$', r'📌 <b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    lines = text.split('\n')
    new_lines = []
    in_quote = False
    quote_buf = []

    for line in lines:
        if line.strip().startswith('&gt;'):
            in_quote = True
            quote_buf.append(line.strip()[4:].strip())
        else:
            if in_quote:
                q_text = ' '.join(quote_buf)
                new_lines.append(f'<blockquote>{q_text}</blockquote>')
                quote_buf = []
                in_quote = False
            new_lines.append(line)
    if in_quote:
        q_text = ' '.join(quote_buf)
        new_lines.append(f'<blockquote>{q_text}</blockquote>')

    text = '\n'.join(new_lines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    for idx, cb in enumerate(code_blocks):
        text = text.replace(f'___CODE_BLOCK_{idx}___', cb)

    return text.strip()

def get_uzb_now() -> datetime:
    return datetime.now(UZB_TZ)
