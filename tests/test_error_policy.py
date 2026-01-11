from backend.app.services.error_policy import classify_error


def test_classify_error_content_policy():
    code, retryable = classify_error("Content policy violation detected")
    assert code == "content_policy"
    assert retryable is False


def test_classify_error_rate_limit():
    code, retryable = classify_error("rate limit exceeded (429)")
    assert code == "rate_limited"
    assert retryable is True


def test_classify_error_timeout():
    code, retryable = classify_error("request timed out after 30s")
    assert code == "timeout"
    assert retryable is True


def test_classify_error_unknown():
    code, retryable = classify_error("unexpected error")
    assert code == "unknown_error"
    assert retryable is False
