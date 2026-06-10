"""Gradio demo app - the public face of BorderPilot on HuggingFace Spaces."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gradio as gr  # noqa: E402

from border_pilot.orchestrator import run as run_workflow  # noqa: E402


DEFAULT_MARKETS = ["amazon_us", "amazon_de", "amazon_uk", "amazon_jp"]


def _format_trace(trace):
    return "\n".join(trace or [])


def _format_trends(trends):
    if not trends:
        return "_No trends surfaced._"
    rows = ["| Trend | Marketplace | Score | Note |", "|---|---|---|---|"]
    for t in trends[:6]:
        note = (t.get("demand_signal") or "-")[:80]
        rows.append(
            f"| {t.get('name')} | {t.get('marketplace')} | "
            f"{t.get('score')} | {note} |"
        )
    return "\n".join(rows)


def _format_market(market):
    if not market:
        return "_No analyst brief._"
    parts = [
        f"**Decision:** `{market.get('decision')}` ",
        f"**Rationale:** {market.get('rationale') or '-'}",
        "",
        f"- TAM est.: {market.get('tam_estimate_usd') or '-'}",
        f"- Price sweet spot: {market.get('price_sweet_spot') or '-'}",
        f"- Review threshold: {market.get('review_threshold_to_win') or '-'}",
        f"- Differentiation: {market.get('differentiation_signal') or '-'}",
        f"- Competitors: {', '.join(market.get('top_competitors') or []) or '-'}",
        f"- Risk flags: {', '.join(market.get('risk_flags') or []) or '-'}",
    ]
    return "\n".join(parts)


def _format_listing(mp, draft):
    if not draft:
        return f"### {mp}\n_no draft_\n"
    bullets = "\n".join(f"- {b}" for b in draft.get("bullet_points") or [])
    return (
        f"### {mp} ({draft.get('language')}) - quality {draft.get('quality_score')}\n"
        f"**Title:** {draft.get('title')}\n\n"
        f"**Bullets:**\n{bullets or '_none_'}\n\n"
        f"**Description:**\n{draft.get('description') or '_none_'}\n\n"
        f"**Keywords:** {', '.join(draft.get('keywords') or []) or '-'}\n\n"
        f"**Price hint:** {draft.get('price_hint') or '-'}"
    )


def _format_listings(listings):
    if not listings:
        return "_No listings generated._"
    return "\n\n---\n\n".join(_format_listing(mp, d) for mp, d in listings.items())


def _format_quality(report):
    if not report:
        return "_No quality report._"
    rows = ["| Marketplace | Check | Score | Note |", "|---|---|---|---|"]
    for c in (report.get("checks") or [])[:20]:
        rows.append(
            f"| {c.get('marketplace')} | {c.get('name')} | {c.get('score')} | "
            f"{(c.get('note') or '-')[:80]} |"
        )
    editorial = report.get("editorial_notes") or []
    editorial_md = ""
    if editorial:
        editorial_md = "\n\n**Editorial notes:**\n" + "\n".join(f"- {n}" for n in editorial)
    return (
        f"**Overall score:** `{report.get('overall_score')}` - "
        f"**Recommendation:** `{report.get('recommendation')}`\n\n"
        + "\n".join(rows)
        + editorial_md
    )


def run_pipeline(query: str, marketplaces: str, progress=gr.Progress()):
    if not query or not query.strip():
        raise gr.Error("Please enter a seed query first.")
    markets = [m.strip() for m in (marketplaces or "").split(",") if m.strip()]
    if not markets:
        markets = DEFAULT_MARKETS

    progress(0.1, desc="TrendScout scanning...")
    final = run_workflow(query.strip(), target_marketplaces=markets)

    return (
        _format_trace(final.get("trace")),
        _format_trends(final.get("trends")),
        _format_market(final.get("market_analysis")),
        _format_listings(final.get("listings")),
        _format_quality(final.get("quality_report")),
        json.dumps(final, ensure_ascii=False, indent=2, default=str),
    )


with gr.Blocks(title="BorderPilot", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
# BorderPilot

**Multi-agent workflow for cross-border e-commerce.** Built with LangGraph,
Python, and Gradio. Four agents collaborate end-to-end:

> **TrendScout -> MarketAnalyst -> ListingCraft -> QualityCheck**

Type a seed query (e.g. `wireless earbuds`, `pet water fountain`, `led strip lights`),
pick your target marketplaces, and watch the orchestrator wire up the agents.
The mock LLM keeps the demo fully functional with no API keys; set
`ANTHROPIC_API_KEY` or `HF_TOKEN` in the Space secrets to swap in a real model.
"""
    )
    with gr.Row():
        query = gr.Textbox(
            label="Seed query",
            placeholder="wireless earbuds under $30",
            value="wireless earbuds",
        )
        markets = gr.Textbox(
            label="Target marketplaces (comma-separated)",
            value=",".join(DEFAULT_MARKETS),
        )
        run_btn = gr.Button("Run pipeline", variant="primary")

    with gr.Tabs():
        with gr.TabItem("Trace"):
            out_trace = gr.Markdown()
        with gr.TabItem("Trends"):
            out_trends = gr.Markdown()
        with gr.TabItem("Analyst brief"):
            out_market = gr.Markdown()
        with gr.TabItem("Listings"):
            out_listings = gr.Markdown()
        with gr.TabItem("Quality report"):
            out_quality = gr.Markdown()
        with gr.TabItem("Raw state (JSON)"):
            out_json = gr.Code(language="json")

    run_btn.click(
        run_pipeline,
        inputs=[query, markets],
        outputs=[out_trace, out_trends, out_market, out_listings, out_quality, out_json],
    )

    gr.Markdown(
        """
---
### Why this exists
BorderPilot is a portfolio piece demonstrating:
- **Multi-agent orchestration** with [LangGraph](https://langchain-ai.github.io/langgraph/)
- **Tool-using agents** (catalogue retrieval, JSON-constrained LLM output, rule checks)
- **Production shape**: typed state, conditional edges, smoke tests, CLI + UI
- **Domain fit**: cross-border e-commerce workflow (trend -> analysis -> multi-locale listings -> compliance)

Set `BORDER_PILOT_LLM=anthropic` plus `ANTHROPIC_API_KEY` to swap the mock LLM
for Claude. Set `BORDER_PILOT_LLM=huggingface` plus `HF_TOKEN` to use a free
HuggingFace Inference model. The mock provider is the default so this Space
runs without secrets.
"""
    )


if __name__ == "__main__":
    demo.queue(max_size=8).launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )
