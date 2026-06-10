"""MarketAnalyst agent - turns a candidate into an actionable go/no-go brief."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from border_pilot.state import BorderPilotState
from border_pilot.tools.llm import LLMMessage, make_llm


_SYSTEM_PROMPT = (
    "You are MarketAnalyst, an e-commerce strategist specialised in cross-border\n"
    "DTC brands. Given a product candidate, produce a concise go/no-go brief.\n"
    "Return a JSON object with keys: tam_estimate_usd, top_competitors (array),\n"
    "price_sweet_spot, review_threshold_to_win, differentiation_signal,\n"
    "risk_flags (array), decision (go | watch | no-go), rationale (1-2 sentences).\n"
    "Output ONLY the JSON block, no prose."
)


def market_analyst_node(state: BorderPilotState) -> Dict[str, Any]:
    """LangGraph node. Reads: trends (top pick), seed_query. Writes: market_analysis, trace."""
    trends = state.get("trends") or []
    if not trends:
        return {
            "market_analysis": {"decision": "no-go", "rationale": "no trends to analyse"},
            "current_step": "market_analyst.empty",
            "trace": ["[MarketAnalyst] no trends to analyse -> no-go"],
        }

    top = trends[0]
    llm = make_llm()
    user_msg = (
        f"Seed query: {state.get('seed_query', '')!r}\n"
        f"Top candidate trend:\n{json.dumps(top, ensure_ascii=False, indent=2)}\n\n"
        "Produce a go/no-go brief. Be specific with numbers and competitors."
    )
    raw = llm.chat(
        [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_msg),
        ],
        temperature=0.4,
        max_tokens=700,
    )

    parsed = _parse_json_object(raw)
    if parsed is None:
        parsed = {
            "decision": "watch",
            "rationale": "analyst output unparseable; defaulting to watch",
            "tam_estimate_usd": "n/a",
            "top_competitors": [],
            "price_sweet_spot": top.get("price_band", "-"),
            "review_threshold_to_win": "n/a",
            "differentiation_signal": "n/a",
            "risk_flags": ["analyst output not parseable as JSON"],
        }
    parsed["candidate"] = top.get("name")
    parsed["marketplace"] = top.get("marketplace")

    return {
        "market_analysis": parsed,
        "current_step": "market_analyst.done",
        "trace": [
            f"[MarketAnalyst] candidate={top.get('name')!r} "
            f"-> decision={parsed.get('decision', 'watch')}"
        ],
    }


def _parse_json_object(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None
