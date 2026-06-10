"""TrendScout agent - surfaces candidate products for a seed query."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from border_pilot.state import BorderPilotState
from border_pilot.tools.data import fetch_trends
from border_pilot.tools.llm import LLMMessage, make_llm


_SYSTEM_PROMPT = (
    "You are TrendScout, a senior product-discovery analyst for cross-border e-commerce.\n"
    "Your job is to rank candidate products by trend strength, marketplace fit, and\n"
    "sourcing viability. You always respond with a single JSON array named `trends`.\n"
    "Each trend object MUST include: name, trend (rising|stable|declining),\n"
    "marketplace, price_band, demand_signal, sourcing_hint, score (0..1).\n"
    "Output ONLY the JSON block, no prose."
)


def trend_scout_node(state: BorderPilotState) -> Dict[str, Any]:
    """LangGraph node. Reads: seed_query, target_marketplaces. Writes: trends, trace."""
    query = state.get("seed_query", "").strip()
    targets = state.get("target_marketplaces") or []

    snapshot = fetch_trends(query, marketplaces=targets or None)
    candidate_rows: List[Dict[str, Any]] = snapshot.get("trends", [])
    if not candidate_rows:
        return {
            "trends": [],
            "current_step": "trend_scout.empty",
            "trace": [f"[TrendScout] no candidates for query={query!r}"],
        }

    # Ask the LLM to re-rank & score the candidates
    llm = make_llm()
    user_msg = (
        f"Seed query: {query!r}\n"
        f"Target marketplaces: {targets or 'any'}\n"
        f"Candidate catalogue:\n"
        f"{json.dumps(candidate_rows, ensure_ascii=False, indent=2)}\n\n"
        "Re-rank these by trend strength, marketplace fit, and sourcing viability.\n"
        "Return a JSON array of objects with keys: name, trend, marketplace,\n"
        "price_band, demand_signal, sourcing_hint, score (0..1)."
    )
    raw = llm.chat(
        [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_msg),
        ],
        temperature=0.4,
        max_tokens=900,
    )

    ranked = _parse_json_array(raw) or candidate_rows
    cleaned: List[Dict[str, Any]] = []
    for row in ranked:
        cleaned.append({
            "name": row.get("name", "Unknown"),
            "trend": row.get("trend", "stable"),
            "marketplace": row.get("marketplace", (targets or ["amazon_us"])[0]),
            "price_band": row.get("price_band", row.get("price_band_usd", "-")),
            "demand_signal": row.get("demand_signal", ""),
            "sourcing_hint": row.get("sourcing_hint", ""),
            "score": float(row.get("score", 0.5)),
        })

    return {
        "trends": cleaned,
        "current_step": "trend_scout.done",
        "trace": [
            f"[TrendScout] query={query!r} -> {len(cleaned)} ranked trends "
            f"(top: {cleaned[0]['name'] if cleaned else 'none'})"
        ],
    }


def _parse_json_array(text: str):
    """Robustly extract a JSON array from model output, even if wrapped in prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "trends" in parsed:
            return parsed["trends"]
    except Exception:
        return None
    return None
