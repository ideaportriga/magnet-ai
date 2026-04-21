"""Unit tests for response validation and litellm exception translation."""

from types import SimpleNamespace

import litellm
import pytest

from services.ai_services.exceptions import (
    LLMContextWindowExceededError,
    LLMEmptyResponseError,
    LLMGuardrailBlockedError,
    LLMProviderAuthError,
    LLMProviderBadRequestError,
    LLMProviderServiceUnavailableError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTruncatedError,
)
from services.ai_services.litellm_call import translate_litellm_exception
from services.ai_services.response_validation import (
    extract_deployment_id,
    extract_finish_reason,
    extract_request_id,
    extract_retry_count,
    is_cache_hit,
    validate_completion,
    validate_streamed_completion,
)


def _mk_response(
    *,
    choices=None,
    hidden_params=None,
    response_id="resp-1",
):
    return SimpleNamespace(
        id=response_id,
        choices=choices if choices is not None else [],
        _hidden_params=hidden_params or {},
    )


def _mk_choice(*, finish_reason=None, content=None, tool_calls=None, role="assistant"):
    message = SimpleNamespace(role=role, content=content, tool_calls=tool_calls)
    return SimpleNamespace(finish_reason=finish_reason, message=message)


# --- validate_completion ---


class TestValidateCompletion:
    def test_valid_response_passes(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content="Hello there")]
        )
        validate_completion(resp)

    def test_empty_choices_raises(self):
        resp = _mk_response(choices=[])
        with pytest.raises(LLMEmptyResponseError) as ei:
            validate_completion(resp, model="gpt-4o", provider="openai")
        assert ei.value.reason == "no_choices"
        assert ei.value.model == "gpt-4o"
        assert ei.value.provider == "openai"

    def test_null_content_without_tool_calls_raises(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content=None, tool_calls=None)]
        )
        with pytest.raises(LLMEmptyResponseError) as ei:
            validate_completion(resp)
        assert ei.value.reason == "null_content"

    def test_content_filter_raises_guardrail(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="content_filter", content=None)]
        )
        with pytest.raises(LLMGuardrailBlockedError) as ei:
            validate_completion(resp)
        assert ei.value.finish_reason == "content_filter"

    def test_length_without_content_raises_truncated(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="length", content=None, tool_calls=None)]
        )
        with pytest.raises(LLMTruncatedError):
            validate_completion(resp)

    def test_length_with_partial_content_passes(self):
        # Truncated but usable — callers prefer partial data over a 5xx
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="length", content="partial answer")]
        )
        validate_completion(resp)

    def test_tool_calls_without_content_passes(self):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(name="search", arguments='{"q": "cats"}')
        )
        resp = _mk_response(
            choices=[
                _mk_choice(
                    finish_reason="tool_calls", content=None, tool_calls=[tool_call]
                )
            ]
        )
        validate_completion(resp)

    def test_empty_string_content_with_stop_passes(self):
        # Model can legitimately produce ""; only `None` is an error
        resp = _mk_response(choices=[_mk_choice(finish_reason="stop", content="")])
        validate_completion(resp)


# --- validate_streamed_completion ---


class TestValidateStreamedCompletion:
    def test_valid_stream_passes(self):
        validate_streamed_completion(
            aggregated_content="hello",
            finish_reason="stop",
            tool_calls_seen=False,
        )

    def test_content_filter_raises(self):
        with pytest.raises(LLMGuardrailBlockedError):
            validate_streamed_completion(
                aggregated_content="",
                finish_reason="content_filter",
                tool_calls_seen=False,
            )

    def test_length_no_content_raises(self):
        with pytest.raises(LLMTruncatedError):
            validate_streamed_completion(
                aggregated_content="",
                finish_reason="length",
                tool_calls_seen=False,
            )

    def test_length_with_content_passes(self):
        validate_streamed_completion(
            aggregated_content="some words",
            finish_reason="length",
            tool_calls_seen=False,
        )

    def test_tool_calls_stream_passes(self):
        validate_streamed_completion(
            aggregated_content="",
            finish_reason="tool_calls",
            tool_calls_seen=True,
        )

    def test_empty_stream_on_stop_passes(self):
        # No content, normal stop — treat as success, model chose silence
        validate_streamed_completion(
            aggregated_content="",
            finish_reason="stop",
            tool_calls_seen=False,
        )


# --- extractors ---


class TestExtractors:
    def test_finish_reason_reads_first_choice(self):
        resp = _mk_response(choices=[_mk_choice(finish_reason="stop", content="ok")])
        assert extract_finish_reason(resp) == "stop"

    def test_finish_reason_missing_returns_none(self):
        assert extract_finish_reason(_mk_response(choices=[])) is None

    def test_request_id_from_headers(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content="ok")],
            hidden_params={
                "additional_headers": {"x-request-id": "req-abc"},
            },
        )
        assert extract_request_id(resp) == "req-abc"

    def test_request_id_fallback_to_response_id(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content="ok")],
            response_id="resp-xyz",
            hidden_params={},
        )
        assert extract_request_id(resp) == "resp-xyz"

    def test_deployment_id_from_hidden(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content="ok")],
            hidden_params={"model_id": "dep-1"},
        )
        assert extract_deployment_id(resp) == "dep-1"

    def test_cache_hit_flag(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content="ok")],
            hidden_params={"cache_hit": True},
        )
        assert is_cache_hit(resp) is True

    def test_retry_count(self):
        resp = _mk_response(
            choices=[_mk_choice(finish_reason="stop", content="ok")],
            hidden_params={"num_retries": 2},
        )
        assert extract_retry_count(resp) == 2


# --- translate_litellm_exception ---


class TestTranslateLiteLLMException:
    def test_rate_limit(self):
        raw = litellm.exceptions.RateLimitError(
            message="rate limited",
            llm_provider="openai",
            model="gpt-4o",
        )
        translated = translate_litellm_exception(
            raw, source="provider", model="gpt-4o", provider="openai"
        )
        assert isinstance(translated, LLMRateLimitError)
        assert translated.source == "provider"
        assert translated.provider == "openai"

    def test_timeout(self):
        raw = litellm.exceptions.Timeout(
            message="slow", llm_provider="openai", model="gpt-4o"
        )
        translated = translate_litellm_exception(
            raw, source="router", model="gpt-4o", provider="openai"
        )
        assert isinstance(translated, LLMTimeoutError)
        assert translated.source == "router"

    def test_context_window(self):
        raw = litellm.exceptions.ContextWindowExceededError(
            message="too long", model="gpt-4o", llm_provider="openai"
        )
        assert isinstance(
            translate_litellm_exception(
                raw, source="provider", model="gpt-4o", provider="openai"
            ),
            LLMContextWindowExceededError,
        )

    def test_content_policy_violation(self):
        raw = litellm.exceptions.ContentPolicyViolationError(
            message="blocked", model="gpt-4o", llm_provider="openai"
        )
        translated = translate_litellm_exception(
            raw, source="provider", model="gpt-4o", provider="openai"
        )
        assert isinstance(translated, LLMGuardrailBlockedError)

    def test_auth_error(self):
        raw = litellm.exceptions.AuthenticationError(
            message="bad key", llm_provider="openai", model="gpt-4o"
        )
        assert isinstance(
            translate_litellm_exception(
                raw, source="provider", model="gpt-4o", provider="openai"
            ),
            LLMProviderAuthError,
        )

    def test_service_unavailable(self):
        raw = litellm.exceptions.ServiceUnavailableError(
            message="503", llm_provider="openai", model="gpt-4o"
        )
        assert isinstance(
            translate_litellm_exception(
                raw, source="provider", model="gpt-4o", provider="openai"
            ),
            LLMProviderServiceUnavailableError,
        )

    def test_bad_request(self):
        raw = litellm.exceptions.BadRequestError(
            message="bad", model="gpt-4o", llm_provider="openai"
        )
        assert isinstance(
            translate_litellm_exception(
                raw, source="provider", model="gpt-4o", provider="openai"
            ),
            LLMProviderBadRequestError,
        )


# --- HTTP status mapping ---


class TestSpanErrorStamping:
    """Validate that _stamp_llm_error_attributes writes structured fields."""

    def _collect(self, exc):
        import json

        from services.observability.decorators import ObservabilityContext

        attrs: dict[str, object] = {}

        class _Span:
            def set_attribute(self, key, value):
                attrs[key] = json.loads(value) if isinstance(value, str) else value

        ObservabilityContext()._stamp_llm_error_attributes(_Span(), exc)
        return attrs

    def test_guardrail_error_stamps_all_fields(self):
        attrs = self._collect(
            LLMGuardrailBlockedError(
                "Blocked",
                source="provider",
                provider="openai",
                model="gpt-5-mini",
                status_code=200,
                request_id="req-abc",
                finish_reason="content_filter",
            )
        )
        assert attrs["magnet_ai.extra_data.error_type"] == "LLMGuardrailBlockedError"
        assert attrs["magnet_ai.extra_data.error_source"] == "provider"
        assert attrs["magnet_ai.extra_data.error_provider"] == "openai"
        assert attrs["magnet_ai.extra_data.error_model"] == "gpt-5-mini"
        assert attrs["magnet_ai.extra_data.error_status_code"] == 200
        assert attrs["magnet_ai.extra_data.error_request_id"] == "req-abc"
        assert attrs["magnet_ai.extra_data.error_finish_reason"] == "content_filter"
        assert attrs["magnet_ai.extra_data.error_message"] == "Blocked"

    def test_rate_limit_stamps_retry_after(self):
        attrs = self._collect(
            LLMRateLimitError(
                "Rate limited",
                source="provider",
                provider="openai",
                retry_after=30.0,
            )
        )
        assert attrs["magnet_ai.extra_data.error_type"] == "LLMRateLimitError"
        assert attrs["magnet_ai.extra_data.error_retry_after"] == 30.0

    def test_non_llm_exception_is_ignored(self):
        attrs = self._collect(RuntimeError("boom"))
        assert attrs == {}


class TestHTTPStatusCodes:
    def test_rate_limit_is_429(self):
        assert LLMRateLimitError("x").http_status_code == 429

    def test_guardrail_is_422(self):
        assert LLMGuardrailBlockedError().http_status_code == 422

    def test_context_window_is_400(self):
        assert LLMContextWindowExceededError("x").http_status_code == 400

    def test_auth_is_502(self):
        # Invalid credentials is our misconfiguration, not the client's fault
        assert LLMProviderAuthError("x").http_status_code == 502

    def test_timeout_is_504(self):
        assert LLMTimeoutError("x").http_status_code == 504

    def test_empty_response_is_502(self):
        assert LLMEmptyResponseError().http_status_code == 502

    def test_truncated_is_502(self):
        assert LLMTruncatedError().http_status_code == 502
