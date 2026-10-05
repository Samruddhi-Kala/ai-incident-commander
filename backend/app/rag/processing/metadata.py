import re
from pathlib import Path
from typing import List, Tuple, Optional


def extract_headings(content: str) -> List[Tuple[int, str]]:
    """
    Extracts Markdown headers with their level and title text.
    e.g. [(1, "Payment Service Runbook"), (2, "Common Failures & Diagnostic Steps")]
    """
    headings: List[Tuple[int, str]] = []
    for line in content.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((level, title))
    return headings


def estimate_token_count(text: str) -> int:
    """
    Approximates token count based on whitespace word segmentation
    and character heuristic (~4 characters per token).
    """
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    # Balanced heuristic between words and character length
    return max(1, max(words, chars // 4))


def extract_service_hint(content: str, file_path: str) -> Optional[str]:
    """
    Extracts target service name if mentioned in headers, metadata labels, or filename.
    e.g., '**Service Name**: `payment-service`' or filename 'payment-service.md'
    """
    # 1. Regex check for common metadata labels in runbooks/postmortems
    label_patterns = [
        r"\*\*Service Name\*\*:\s*`?([a-zA-Z0-9\-_]+)`?",
        r"\*\*Affected Service\*\*:\s*`?([a-zA-Z0-9\-_]+)`?",
        r"service:\s*`?([a-zA-Z0-9\-_]+)`?",
    ]
    for pattern in label_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # 2. Check if filename matches a canonical service pattern (e.g. payment-service.md)
    stem = Path(file_path).stem.lower()
    if "-service" in stem or "_service" in stem:
        return stem

    return None
