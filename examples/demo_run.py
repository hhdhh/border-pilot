"""End-to-end demo script."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("BORDER_PILOT_LLM", "mock")

from border_pilot.orchestrator import run as run_workflow  # noqa: E402


def main() -> int:
    final = run_workflow(
        "wireless earbuds",
        target_marketplaces=["amazon_us", "amazon_de", "amazon_uk", "amazon_jp"],
    )
    print(json.dumps(final, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
