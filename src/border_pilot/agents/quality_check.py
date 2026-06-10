"""QualityCheck agent - validates generated listings against marketplace rules."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from border_pilot.state import BorderPilotState
from border_pilot.tools.llm import LLMMessage, make_llm


_BANNED_WORDS_EN = {"best", "#1", "guaranteed", "cure", "100%"}
_BANNED_WORDS_DE = {"beste", "garantiert", "100%"}
_BANNED_WORDS_JA = {"saikou", "ichiban", "hoshou"}


def quality_check_node(state: BorderPilotState) -> Dict[str, Any]:
    """LangGraph node. Reads: listings, target_marketplaces. Writes: quality_report, trace."""
    listings = state.get("listings") or {}
    if not listings:
        return {
            "quality_report": {
                "overall_score": 0.0,
                "checks": [],
                "recommendation": "REJECTED_NO_DRAFTS",
            },
            "current_step": "quality_check.empty",
            "trace": ["[QualityCheck] no listings to validate -> REJECTED"],
        }

    checks: List[Dict[str, Any]] = []
    overall: List[float] = []

    for marketplace, draft in listings.items():
        title = (draft.get("title") or "").strip()
        desc = (draft.get("description") or "").strip()
        bullets = draft.get("bullet_points") or []
        lang = (draft.get("language") or "en").lower()

        checks.append({
            "marketplace": marketplace,
            "name": "title_length",
            "score": 1.0 if 0 < len(title) <= 200 else 0.0,
            "note": f"title len={len(title)} (limit 200)",
        })
        checks.append({
            "marketplace": marketplace,
            "name": "bullet_count",
            "score": 1.0 if 3 <= len(bullets) <= 5 else (0.7 if 1 <= len(bullets) <= 6 else 0.0),
            "note": f"bullets={len(bullets)}",
        })
        checks.append({
            "marketplace": marketplace,
            "name": "description_length",
            "score": 1.0 if 50 <= len(desc) <= 2000 else (0.7 if len(desc) <= 0 else 0.0),
            "note": f"desc len={len(desc)} (limit 2000)",
        })
        banned = _banned_for(lang)
        joined = f"{title}\n{desc}\n" + "\n".join(bullets).lower()
        hits = [w for w in banned if w.lower() in joined.lower()]
        checks.append({
            "marketplace": marketplace,
            "name": "no_banned_words",
            "score": 1.0 if not hits else 0.0,
            "note": "no banned promotional terms" if not hits else f"banned hits: {hits}",
        })
        n = sum(1 for c in checks if c["marketplace"] == marketplace)
        score = sum(c["score"] for c in checks if c["marketplace"] == marketplace) / max(1, n)
        overall.append(score)
        draft["quality_score"] = round(score, 3)

    overall_score = round(sum(overall) / len(overall), 3) if overall else 0.0
    recommendation = (
        "APPROVED" if overall_score >= 0.8
        else "APPROVED_WITH_REVIEW" if overall_score >= 0.6
        else "REJECTED"
    )

    report = {
        "overall_score": overall_score,
        "checks": checks,
        "recommendation": recommendation,
        "summary_by_marketplace": {
            mp: round(avg, 3) for mp, avg in zip(listings.keys(), overall)
        },
    }

    # Optional editorial pass
    llm = make_llm()
    sys_msg = (
        "You are QualityCheck, a marketplace compliance reviewer. Given a list of\n"
        "drafts, return a JSON object with key `notes`: an array of one short\n"
        "recommendation per marketplace. Output ONLY the JSON."
    )
    user_msg = (
        "Drafts to review:\n"
        f"{json.dumps({mp: dict(d) for mp, d in listings.items()}, ensure_ascii=False, indent=2)}\n"
    )
    raw = llm.chat(
        [
            LLMMessage(role="system", content=sys_msg),
            LLMMessage(role="user", content=user_msg),
        ],
        temperature=0.3,
        max_tokens=500,
    )
    editorial = _parse_json_object(raw) or {}
    if "notes" in editorial:
        report["editorial_notes"] = editorial["notes"]

    return {
        "quality_report": report,
        "current_step": "quality_check.done",
        "trace": [
            f"[QualityCheck] score={overall_score} -> {recommendation} "
            f"({len(listings)} marketplaces reviewed)"
        ],
    }


def _banned_for(language: str) -> set:
    if language.startswith("de"):
        return _BANNED_WORDS_DE
    if language.startswith("ja"):
        return _BANNED_WORDS_JA
    return _BANNED_WORDS_EN


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
        return json.loads(text)
    except Exception:
        return None
