"""OTLP/JSON encoding helpers.

Protobuf's JSON mapping emits bytes fields (trace/span ids) as base64; the
OTLP file-exporter spec requires hex. b64_ids_to_hex() fixes them in place.
"""

import base64
from typing import Any

_ID_KEYS = frozenset({"traceId", "spanId", "parentSpanId"})


def b64_ids_to_hex(node: Any) -> None:
    """Recursively convert base64-encoded id fields to lowercase hex, in place."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _ID_KEYS and isinstance(value, str):
                node[key] = base64.b64decode(value).hex()
            else:
                b64_ids_to_hex(value)
    elif isinstance(node, list):
        for item in node:
            b64_ids_to_hex(item)
