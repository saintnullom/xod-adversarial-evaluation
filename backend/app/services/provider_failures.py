"""Safe classification and presentation of AI provider failures."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
import logging
from time import perf_counter
from typing import Literal
from uuid import uuid4

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    UnprocessableEntityError,
)
from pydantic import ValidationError


logger = logging.getLogger("xod.provider")
ProviderOperation = Literal["SPAR", "TRIBUNAL"]


class ProviderFailureCategory(str, Enum):
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK = "NETWORK"
    STRUCTURED_OUTPUT_VALIDATION = "STRUCTURED_OUTPUT_VALIDATION"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    PROVIDER_REJECTED_REQUEST = "PROVIDER_REJECTED_REQUEST"
    UNSUPPORTED_FORMAT_OR_MODEL = "UNSUPPORTED_FORMAT_OR_MODEL"
    INTERNAL_PROVIDER_ERROR = "INTERNAL_PROVIDER_ERROR"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"


RETRYABLE_CATEGORIES = {
    ProviderFailureCategory.TIMEOUT,
    ProviderFailureCategory.RATE_LIMIT,
    ProviderFailureCategory.NETWORK,
    ProviderFailureCategory.INTERNAL_PROVIDER_ERROR,
}

SAFE_MESSAGES = {
    ProviderFailureCategory.TIMEOUT: "XOD's provider timed out before completing the analysis.",
    ProviderFailureCategory.RATE_LIMIT: "XOD's provider is temporarily rate limited.",
    ProviderFailureCategory.NETWORK: "XOD cannot reach its provider right now.",
    ProviderFailureCategory.STRUCTURED_OUTPUT_VALIDATION: "XOD received a response that did not match the required structure.",
    ProviderFailureCategory.MALFORMED_RESPONSE: "XOD received an incomplete provider response.",
    ProviderFailureCategory.PROVIDER_REJECTED_REQUEST: "XOD's provider rejected this request configuration.",
    ProviderFailureCategory.UNSUPPORTED_FORMAT_OR_MODEL: "XOD's configured provider model or response format is not supported.",
    ProviderFailureCategory.INTERNAL_PROVIDER_ERROR: "XOD's provider encountered an internal error.",
    ProviderFailureCategory.PROVIDER_NOT_CONFIGURED: "XOD cannot analyze because its provider is not configured.",
}

HTTP_STATUS_BY_CATEGORY = {
    ProviderFailureCategory.TIMEOUT: 504,
    ProviderFailureCategory.RATE_LIMIT: 429,
    ProviderFailureCategory.NETWORK: 503,
    ProviderFailureCategory.STRUCTURED_OUTPUT_VALIDATION: 502,
    ProviderFailureCategory.MALFORMED_RESPONSE: 502,
    ProviderFailureCategory.PROVIDER_REJECTED_REQUEST: 400,
    ProviderFailureCategory.UNSUPPORTED_FORMAT_OR_MODEL: 422,
    ProviderFailureCategory.INTERNAL_PROVIDER_ERROR: 502,
    ProviderFailureCategory.PROVIDER_NOT_CONFIGURED: 503,
}


class ProviderFailure(RuntimeError):
    """A safe provider failure that retains its original exception through chaining."""

    def __init__(
        self,
        category: ProviderFailureCategory,
        operation: ProviderOperation,
        provider: str,
        model: str | None,
        latency_ms: int | None,
    ) -> None:
        self.error_id = f"XOD-{uuid4()}"
        self.category = category
        self.operation = operation
        self.provider = provider
        self.model = model
        self.latency_ms = latency_ms
        self.retryable = category in RETRYABLE_CATEGORIES
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(SAFE_MESSAGES[category])

    def event(self) -> dict[str, object]:
        return {
            "error_id": self.error_id,
            "category": self.category.value,
            "operation": self.operation,
            "provider": self.provider,
            "model": self.model,
            "retryable": self.retryable,
            "latency_ms": self.latency_ms,
            "occurred_at": self.timestamp,
        }

    def safe_detail(self) -> dict[str, object]:
        return {
            "message": str(self),
            "category": self.category.value,
            "error_id": self.error_id,
            "retryable": self.retryable,
        }


class ProviderUnavailableError(ProviderFailure):
    def __init__(self, operation: ProviderOperation, model: str | None) -> None:
        super().__init__(
            ProviderFailureCategory.PROVIDER_NOT_CONFIGURED,
            operation,
            provider="openai",
            model=model,
            latency_ms=None,
        )


def elapsed_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)


def classify_provider_exception(error: Exception) -> ProviderFailureCategory:
    if isinstance(error, (APITimeoutError, TimeoutError)):
        return ProviderFailureCategory.TIMEOUT
    if isinstance(error, RateLimitError):
        return ProviderFailureCategory.RATE_LIMIT
    if isinstance(error, APIConnectionError):
        return ProviderFailureCategory.NETWORK
    if isinstance(error, ValidationError):
        return ProviderFailureCategory.STRUCTURED_OUTPUT_VALIDATION
    if isinstance(error, NotFoundError):
        return ProviderFailureCategory.UNSUPPORTED_FORMAT_OR_MODEL
    if isinstance(error, (BadRequestError, UnprocessableEntityError)):
        return ProviderFailureCategory.PROVIDER_REJECTED_REQUEST
    if isinstance(error, InternalServerError):
        return ProviderFailureCategory.INTERNAL_PROVIDER_ERROR
    if isinstance(error, APIStatusError):
        if error.status_code >= 500:
            return ProviderFailureCategory.INTERNAL_PROVIDER_ERROR
        return ProviderFailureCategory.PROVIDER_REJECTED_REQUEST
    return ProviderFailureCategory.INTERNAL_PROVIDER_ERROR


def provider_failure_from_exception(
    error: Exception,
    operation: ProviderOperation,
    provider: str,
    model: str | None,
    started_at: float,
) -> ProviderFailure:
    return ProviderFailure(
        classify_provider_exception(error),
        operation,
        provider=provider,
        model=model,
        latency_ms=elapsed_ms(started_at),
    )


def malformed_response_failure(
    operation: ProviderOperation, provider: str, model: str | None, started_at: float
) -> ProviderFailure:
    return ProviderFailure(
        ProviderFailureCategory.MALFORMED_RESPONSE,
        operation,
        provider=provider,
        model=model,
        latency_ms=elapsed_ms(started_at),
    )


def log_provider_failure(failure: ProviderFailure) -> None:
    """Emit operation metadata only; never prompts, responses, headers, or key material."""
    logger.error("xod_provider_failure %s", json.dumps(failure.event(), sort_keys=True))


def provider_failure_status(failure: ProviderFailure) -> int:
    return HTTP_STATUS_BY_CATEGORY[failure.category]
