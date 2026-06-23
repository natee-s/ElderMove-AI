"""Report serialization; raw video is intentionally excluded."""

from __future__ import annotations

import json
from typing import Any


def report_as_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=True)

