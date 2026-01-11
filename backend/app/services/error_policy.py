from typing import List, Optional, Tuple

from ..core.config import settings


_DEFAULT_CATEGORIES = [
    ("content_policy", ["content", "policy", "violation", "safety", "nudity", "sexual", "色情", "裸露", "敏感"], False),
    (
        "validation_error",
        ["validation", "schema_error", "schema error", "parameter", "参数错误", "bad request", "prompt text cannot be empty"],
        False,
    ),
    ("rate_limited", ["rate limit", "rate_limited", "too many requests", "429"], True),
    ("timeout", ["timeout", "timed out"], True),
    ("quota_exceeded", ["quota", "insufficient", "余额不足", "balance"], True),
    ("unauthorized", ["unauthorized", "invalid api key", "api key", "401"], True),
    ("forbidden", ["forbidden", "403"], True),
    ("dependency_error", ["dependency", "overloaded"], True),
    ("server_error", ["server error", "service unavailable", "502", "503", "504"], True),
]


def classify_error(message: Optional[str]) -> Tuple[str, bool]:
    if not message:
        return "unknown_error", False
    normalized = message.lower()
    for code, tokens, retryable in _DEFAULT_CATEGORIES:
        if any(token in normalized for token in tokens):
            return code, retryable

    extra_non_retryable = _load_tokens(getattr(settings, "FAILOVER_NON_RETRYABLE_TOKENS", None))
    if any(token in normalized for token in extra_non_retryable):
        return "validation_error", False

    extra_retryable = _load_tokens(getattr(settings, "FAILOVER_RETRYABLE_TOKENS", None))
    if any(token in normalized for token in extra_retryable):
        return "dependency_error", True

    return "unknown_error", False


def _load_tokens(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [token.strip().lower() for token in raw.split(",") if token.strip()]
