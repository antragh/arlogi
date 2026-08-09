"""File-based OTLP exporters."""

import json
from collections.abc import Sequence
from pathlib import Path

from google.protobuf.json_format import MessageToDict
from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
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
