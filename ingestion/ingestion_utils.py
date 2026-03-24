import hashlib
from datetime import datetime

from utils import logger


def generate_article_id(url: str):
    return hashlib.md5(url.encode()).hexdigest() if url else None


def normalize_published_at(date_str: str):
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str.strftime("%Y-%m-%dT%H:%M:%S")

    try:
        # Accept ISO-like strings first
        normalized = date_str.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1]
        if "T" in normalized:
            dt = datetime.fromisoformat(normalized)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass

    patterns = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y %H:%M:%S",
        "%b %d, %Y",
    ]

    for pattern in patterns:
        try:
            dt = datetime.strptime(date_str, pattern)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            continue

    return None


def validate_article(article):
    required_fields = [
        "article_id",
        "source_url",
        "source_title",
        "source_name",
        "published_at",
        "raw_text",
    ]
    if not isinstance(article, dict):
        return False

    for field in required_fields:
        if field not in article or article[field] in (None, ""):
            logger.warning(f"Article missing required field {field}: {article.get('source_url')}")
            return False

    return True
