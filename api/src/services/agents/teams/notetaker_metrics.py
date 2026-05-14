"""OpenTelemetry metrics for the note-taker pipeline.

A small, opinionated set of signals that map 1:1 onto the alerts in
docs/NOTE_TAKER_RELIABILITY_PLAN.md § P2-6:

* ``notetaker.webhook.received`` — counter, labeled by webhook kind
  ("recordings-ready" / "recordings-lifecycle") and outcome
  ("accepted", "duplicate", "spoofed", "rate_limited", "rejected").
* ``notetaker.stt.duration`` — histogram in seconds, by provider /
  outcome ("completed", "failed", "timeout").
* ``notetaker.integration.failure`` — counter on each integration
  publish failure, labeled by ``integration`` (confluence / salesforce
  / knowledge_graph).
* ``notetaker.pipeline.stage_failures`` — counter for pipeline stages
  outside the integration layer (stage1 / stage2 generic failures).
* ``notetaker.running_jobs`` — observable gauge: number of in-flight
  STT pipelines tracked in ``speech_to_text.service._RUNNING``. Useful
  for both capacity alerts and as a smoke-test that the cleanup in
  § P1-5 keeps the dict bounded.

Counters / histograms are exported through ``otel_meter`` and end up on
the Grafana side via the OTLP exporter that already ships GenAI metrics.
"""

from __future__ import annotations

from logging import getLogger
from typing import Iterable

from opentelemetry.metrics import CallbackOptions, Observation

from services.observability.otel.config.meter import otel_meter

logger = getLogger(__name__)


webhook_received_counter = otel_meter.create_counter(
    name="notetaker.webhook.received",
    description="Microsoft Graph webhook deliveries received by the bot.",
    unit="1",
)

stt_duration_histogram = otel_meter.create_histogram(
    name="notetaker.stt.duration",
    description="End-to-end note-taker STT submit→finish duration.",
    unit="s",
    explicit_bucket_boundaries_advisory=[
        1,
        5,
        10,
        30,
        60,
        120,
        300,
        600,
        900,
        1200,
        1800,
        3600,
    ],
)

integration_failure_counter = otel_meter.create_counter(
    name="notetaker.integration.failure",
    description="Integration publish failures (Confluence / Salesforce / KG).",
    unit="1",
)

pipeline_stage_failure_counter = otel_meter.create_counter(
    name="notetaker.pipeline.stage_failures",
    description="Failures in non-integration pipeline stages (stage1 / stage2).",
    unit="1",
)


def record_webhook_received(*, kind: str, outcome: str) -> None:
    """Emit one webhook.received tick.

    ``kind`` is the webhook stream ("recordings-ready" or
    "recordings-lifecycle"); ``outcome`` is one of "accepted",
    "duplicate", "spoofed", "rate_limited", "rejected".
    """
    try:
        webhook_received_counter.add(1, {"kind": kind, "outcome": outcome})
    except Exception:  # noqa: BLE001 — never let telemetry fail the request
        logger.debug("metrics: webhook_received emit failed", exc_info=True)


def record_stt_duration(*, provider: str | None, outcome: str, seconds: float) -> None:
    """Record one STT job duration in seconds."""
    try:
        stt_duration_histogram.record(
            max(0.0, float(seconds)),
            {"provider": provider or "unknown", "outcome": outcome},
        )
    except Exception:  # noqa: BLE001
        logger.debug("metrics: stt_duration emit failed", exc_info=True)


def record_integration_failure(*, integration: str, error_class: str | None) -> None:
    try:
        integration_failure_counter.add(
            1,
            {
                "integration": integration,
                "error_class": error_class or "unknown",
            },
        )
    except Exception:  # noqa: BLE001
        logger.debug("metrics: integration_failure emit failed", exc_info=True)


def record_pipeline_stage_failure(*, stage: str, error_class: str | None) -> None:
    try:
        pipeline_stage_failure_counter.add(
            1,
            {"stage": stage, "error_class": error_class or "unknown"},
        )
    except Exception:  # noqa: BLE001
        logger.debug("metrics: pipeline_stage_failure emit failed", exc_info=True)


def _observe_running_jobs(_options: CallbackOptions) -> Iterable[Observation]:
    """Yield the current size of the in-process STT task registry.

    Imported lazily inside the callback so a `speech_to_text` import
    error (rare, but happens during partial test setups) doesn't crash
    the meter export. We emit zero in that case — a non-emit would
    drop the series for the whole scrape interval and look like the
    process is gone.
    """
    try:
        from speech_to_text.transcription.service import _RUNNING

        yield Observation(len(_RUNNING))
    except Exception:  # noqa: BLE001 — never let telemetry break the meter
        logger.debug("metrics: running_jobs observe failed", exc_info=True)
        yield Observation(0)


otel_meter.create_observable_gauge(
    name="notetaker.running_jobs",
    description="Number of STT pipelines currently in flight (len _RUNNING).",
    unit="1",
    callbacks=[_observe_running_jobs],
)
