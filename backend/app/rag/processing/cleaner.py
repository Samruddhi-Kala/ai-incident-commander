import re


class TextCleaner:
    """
    Sanitizes raw Markdown text by normalizing line endings and redundant whitespace
    while strictly preserving markdown headers, lists, and code blocks.
    """

    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans and normalizes text content.
        """
        if not text:
            return ""

        # 1. Normalize line endings to UNIX style
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Strip trailing whitespace per line (preserving leading indentation for code blocks & lists)
        lines = [line.rstrip() for line in cleaned.split("\n")]
        cleaned = "\n".join(lines)

        # 3. Collapse 3 or more consecutive newline breaks into 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 4. Strip outer whitespace
        return cleaned.strip()
