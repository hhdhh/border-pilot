"""Shared state schema for the BorderPilot agent workflow."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class ListingDraft(TypedDict, total=False):
    """A single marketplace-ready listing draft in one locale."""
    marketplace: str  # e.g. "amazon_us", "ebay_uk", "shopify_de"
    language: str  # ISO 639-1, e.g. "en", "de", "ja"
    title: str
    bullet_points: List[str]
    description: str
    keywords: List[str]
    price_hint: Optional[str]
    quality_score: Optional[float]  # 0..1, filled by QualityCheck


class BorderPilotState(TypedDict, total=False):
    """TypedDict describing the state flowing through the LangGraph workflow."""
    # Inputs
    seed_query: str
    target_marketplaces: List[str]
    target_languages: List[str]

    # Stage outputs
    trends: List[Dict[str, Any]]
    market_analysis: Dict[str, Any]
    listings: Dict[str, ListingDraft]
    quality_report: Dict[str, Any]

    # Workflow control
    current_step: str
    errors: List[str]
    trace: List[str]
