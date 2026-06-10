"""Smoke tests for BorderPilot - run without any API keys."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Force the mock LLM regardless of any leaked env vars.
os.environ["BORDER_PILOT_LLM"] = "mock"

from border_pilot.orchestrator import build_graph, run  # noqa: E402


def test_build_graph_compiles():
    g = build_graph()
    assert g is not None


def test_workflow_happy_path():
    final = run("wireless earbuds", target_marketplaces=["amazon_us", "amazon_de"])
    assert final["current_step"] == "quality_check.done"
    assert final["trends"], "expected non-empty trends"
    assert final["listings"], "expected at least one listing draft"
    assert final["quality_report"]["overall_score"] > 0
    assert set(final["listings"].keys()) == {"amazon_us", "amazon_de"}
    for mp, draft in final["listings"].items():
        assert draft["title"]
        assert 0 < len(draft["title"]) <= 200
        assert 3 <= len(draft["bullet_points"]) <= 5


def test_workflow_handles_unknown_query():
    final = run("quantum flux capacitor", target_marketplaces=["amazon_us"])
    assert "current_step" in final
    assert final["quality_report"]


def test_quality_check_flags_compliance():
    from border_pilot.agents.quality_check import quality_check_node
    from border_pilot.state import BorderPilotState
    state: BorderPilotState = {
        "listings": {
            "amazon_us": {
                "marketplace": "amazon_us",
                "language": "en",
                "title": "BEST earbuds GUARANTEED to cure your day",
                "bullet_points": ["bullet1", "bullet2", "bullet3", "bullet4", "bullet5"],
                "description": "short",
                "keywords": ["earbuds"],
                "price_hint": "$1",
            },
        },
    }
    out = quality_check_node(state)
    report = out["quality_report"]
    flagged = [c for c in report["checks"] if c["name"] == "no_banned_words"]
    assert flagged and flagged[0]["score"] == 0.0, "banned words should be detected"
    assert report["overall_score"] < 1.0


def test_cli_demo_invocation(capsys):
    from border_pilot.cli import main
    rc = main(["demo"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "BorderPilot" in captured.out
    assert "Analyst brief" in captured.out
