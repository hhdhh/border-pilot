"""ListingCraft agent - generates marketplace-ready listings per locale."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from border_pilot.state import BorderPilotState, ListingDraft
from border_pilot.tools.llm import LLMMessage, make_llm


# Map marketplace -> ISO locale code + currency
_LOCALE_DEFAULTS: Dict[str, Dict[str, str]] = {
    "amazon_us": {"language": "en", "currency": "USD"},
    "amazon_uk": {"language": "en-GB", "currency": "GBP"},
    "amazon_de": {"language": "de", "currency": "EUR"},
    "amazon_jp": {"language": "ja", "currency": "JPY"},
    "ebay_us": {"language": "en", "currency": "USD"},
    "ebay_uk": {"language": "en-GB", "currency": "GBP"},
    "ebay_de": {"language": "de", "currency": "EUR"},
    "shopify_us": {"language": "en", "currency": "USD"},
    "shopify_de": {"language": "de", "currency": "EUR"},
}


_SYSTEM_PROMPT = (
    "You are ListingCraft, an expert marketplace listing copywriter.\n"
    "You write listings that comply with Amazon / eBay / Shopify style guides\n"
    "(no superlatives, no subjective claims, no prohibited words like 'best' or\n"
    "'guaranteed' unless substantiated). Always return a single JSON object with\n"
    "keys: marketplace, language, title, bullet_points (array), description,\n"
    "keywords (array), price_hint. Output ONLY the JSON object, no prose."
)


def listing_craft_node(state: BorderPilotState) -> Dict[str, Any]:
    """LangGraph node. Reads: market_analysis, target_marketplaces. Writes: listings, trace."""
    market = state.get("market_analysis") or {}
    if market.get("decision") == "no-go":
        return {
            "listings": {},
            "current_step": "listing_craft.skipped",
            "trace": ["[ListingCraft] skipped - analyst returned no-go"],
        }

    targets: List[str] = list(state.get("target_marketplaces") or [])
    if not targets:
        m = market.get("marketplace")
        targets = [m] if m else ["amazon_us"]

    # Always include at least one English variant
    if not any(_LOCALE_DEFAULTS[t]["language"].startswith("en") for t in targets):
        targets.append("amazon_us")

    llm = make_llm()
    listings: Dict[str, ListingDraft] = {}
    for marketplace in targets:
        locale = _LOCALE_DEFAULTS.get(marketplace, {"language": "en", "currency": "USD"})
        user_msg = _build_user_prompt(state, marketplace, locale["language"])
        raw = llm.chat(
            [
                LLMMessage(role="system", content=_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_msg),
            ],
            temperature=0.6,
            max_tokens=900,
        )
        draft = _parse_listing(raw, marketplace, locale["language"])
        listings[marketplace] = draft

    return {
        "listings": listings,
        "current_step": "listing_craft.done",
        "trace": [
            f"[ListingCraft] produced {len(listings)} locale drafts: "
            + ", ".join(sorted(listings.keys()))
        ],
    }


def _build_user_prompt(state: BorderPilotState, marketplace: str, language: str) -> str:
    market = state.get("market_analysis") or {}
    candidate = market.get("candidate") or state.get("seed_query") or "product"
    return (
        f"Candidate product: {candidate!r}\n"
        f"Target marketplace: {marketplace}\n"
        f"Target language (ISO code): {language}\n"
        f"Analyst brief (use the differentiators & price sweet spot):\n"
        f"{json.dumps(market, ensure_ascii=False, indent=2)}\n\n"
        "Write one marketplace-ready listing. Strict rules:\n"
        "- Title <= 200 characters, no promotional superlatives.\n"
        "- 5 bullet points (or fewer if marketplace limits; amazon_us: 5, ebay: max 3).\n"
        "- Description <= 2000 characters.\n"
        "- Localise currency & units in price_hint (e.g. EUR for amazon_de).\n"
        "Return a single JSON object as specified."
    )


def _parse_listing(raw: str, marketplace: str, language: str) -> ListingDraft:
    parsed = _parse_json_object(raw)
    if parsed is None:
        return ListingDraft(
            marketplace=marketplace,
            language=language,
            title="[draft generation failed]",
            bullet_points=[],
            description="",
            keywords=[],
            price_hint="-",
        )
    caps = {
        "amazon_us": 5, "amazon_uk": 5, "amazon_de": 5, "amazon_jp": 5,
        "ebay_us": 3, "ebay_uk": 3, "ebay_de": 3,
        "shopify_us": 6, "shopify_de": 6,
    }
    cap = caps.get(marketplace, 5)
    bullets = list(parsed.get("bullet_points", []) or [])[:cap]
    return ListingDraft(
        marketplace=marketplace,
        language=language,
        title=str(parsed.get("title", "")).strip(),
        bullet_points=[str(b).strip() for b in bullets if str(b).strip()],
        description=str(parsed.get("description", "")).strip(),
        keywords=[str(k).strip() for k in (parsed.get("keywords") or []) if str(k).strip()],
        price_hint=str(parsed.get("price_hint", "-")).strip() or "-",
    )


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
