"""Orchestrator - LangGraph state machine wiring the four agents together."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from border_pilot.agents import (
    listing_craft_node,
    market_analyst_node,
    quality_check_node,
    trend_scout_node,
)
from border_pilot.state import BorderPilotState


def build_graph() -> StateGraph:
    """Build and compile the BorderPilot workflow graph.

    Flow:
        TrendScout -> MarketAnalyst -+-> ListingCraft -> QualityCheck -> END
                                    | (no-go) -> END
    """
    workflow = StateGraph(BorderPilotState)

    workflow.add_node("trend_scout", trend_scout_node)
    workflow.add_node("market_analyst", market_analyst_node)
    workflow.add_node("listing_craft", listing_craft_node)
    workflow.add_node("quality_check", quality_check_node)

    workflow.set_entry_point("trend_scout")
    workflow.add_edge("trend_scout", "market_analyst")

    def _route_after_analyst(state: BorderPilotState) -> str:
        decision = (state.get("market_analysis") or {}).get("decision")
        if decision == "no-go":
            return "end"
        return "listing_craft"

    workflow.add_conditional_edges(
        "market_analyst",
        _route_after_analyst,
        {"listing_craft": "listing_craft", "end": END},
    )

    workflow.add_edge("listing_craft", "quality_check")
    workflow.add_edge("quality_check", END)

    return workflow.compile()


def run(
    seed_query: str,
    *,
    target_marketplaces: Optional[List[str]] = None,
    target_languages: Optional[List[str]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the full BorderPilot workflow synchronously and return the final state."""
    graph = build_graph()
    inputs: BorderPilotState = {
        "seed_query": seed_query,
        "target_marketplaces": target_marketplaces or [],
        "target_languages": target_languages or [],
        "errors": [],
        "trace": [],
    }
    if initial_state:
        inputs.update({
            k: v for k, v in initial_state.items()
            if k in BorderPilotState.__annotations__
        })
    final = graph.invoke(inputs)
    return final
