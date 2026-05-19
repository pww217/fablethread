"""Structured error types and exception hierarchy for ccya."""

from __future__ import annotations


# ErrorKind: string constants matching existing server/app.py pattern.
# Using strings (not Enum) avoids JSON serialization issues in mixed dict/list contexts like TurnResult.errors.
class ErrorKind:
    # LLM-related errors
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_API_ERROR = "LLM_API_ERROR"

    # Parsing/validation errors
    PARSE_ERROR = "PARSE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Pack/game lifecycle errors
    PACK_LOAD_FAILED = "PACK_LOAD_FAILED"
    SEED_GENERATION_FAILED = "SEED_GENERATION_FAILED"
    PACK_GENERATION_FAILED = "PACK_GENERATION_FAILED"

    # Server/runtime errors
    SERVER_ERROR = "SERVER_ERROR"
    TURN_PROCESSING_FAILED = "TURN_PROCESSING_FAILED"


class LlmcError(Exception):
    """Typed exception hierarchy for LLM client failures.

    Each subclass carries its kind as a class attribute, following Python's standard pattern
    where error classification is fixed per type (e.g., StopIteration, ValueError).
    Callers can distinguish retryable vs non-retryable failures:
    - Retryable: LlmcTimeout, LlmcRateLimit
    - Non-retryable: LlmcApiError (e.g., 400/500 from provider)
    """

    kind: str = "LLM_ERROR"
    retryable: bool = False
    status_code: int | None = None


class LlmcTimeout(LlmcError):
    kind = ErrorKind.LLM_TIMEOUT
    retryable = True


class LlmcRateLimit(LlmcError):
    kind = ErrorKind.LLM_RATE_LIMIT
    retryable = True
    status_code = 429


class LlmcApiError(LlmcError):
    """API error with dynamic HTTP status code from the provider response."""
    kind = ErrorKind.LLM_API_ERROR
    retryable = False

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code
