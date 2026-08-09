"""File-based OTLP exporters."""

import json
from collections.abc import Sequence
from pathlib import Path

from google.protobuf.json_format import MessageToDict
from opentelemetry.exporter.otlp.proto.common.metrics_encoder import encode_metrics
from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
from opentelemetry.sdk.metrics.export import MetricExporter, MetricExportResult, MetricsData
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from arlogi.otel._encode import b64_ids_to_hex
from arlogi.otel._files import _RotatingJsonlWriter


class RotatingJsonlSpanExporter(SpanExporter):
    """Writes each export batch as one OTLP/JSON ResourceSpans object per line."""

    def __init__(
        self,
        directory: str | Path,
        prefix: str = "traces",
        rotate_hours: int = 24,
        retention_count: int = 20,
    ) -> None:
        self._writer = _RotatingJsonlWriter(directory, prefix, rotate_hours, retention_count)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            payload = MessageToDict(encode_spans(spans))
        except Exception:
            return SpanExportResult.FAILURE
        b64_ids_to_hex(payload)
        ok = self._writer.write_line(json.dumps(payload, separators=(",", ":")))
        return SpanExportResult.SUCCESS if ok else SpanExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True  # write_line flushes on every batch

    def shutdown(self) -> None:
        self._writer.close()


class RotatingJsonlMetricExporter(MetricExporter):
    """Writes each export as one OTLP/JSON ResourceMetrics object per line."""

    def __init__(
        self,
        directory: str | Path,
        prefix: str = "metrics",
        rotate_hours: int = 24,
        retention_count: int = 20,
    ) -> None:
        # Installed opentelemetry-sdk's MetricExporter.__init__ accepts
        # preferred_temporality/preferred_aggregation, both defaulting to None, so no
        # explicit args are required here.
        super().__init__()
        self._writer = _RotatingJsonlWriter(directory, prefix, rotate_hours, retention_count)

    def export(self, metrics_data: MetricsData, timeout_millis: float = 10_000, **kwargs: object) -> MetricExportResult:
        try:
            payload = MessageToDict(encode_metrics(metrics_data))
        except Exception:
            return MetricExportResult.FAILURE
        b64_ids_to_hex(payload)
        ok = self._writer.write_line(json.dumps(payload, separators=(",", ":")))
        return MetricExportResult.SUCCESS if ok else MetricExportResult.FAILURE

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        return True

    def shutdown(self, timeout_millis: float = 30_000, **kwargs: object) -> None:
        self._writer.close()
