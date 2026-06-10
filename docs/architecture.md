# BorderPilot — Architecture notes

> Goal: keep this short enough to skim, detailed enough to defend in an interview.

## State machine

`build_graph()` in `src/border_pilot/orchestrator.py` constructs a
`langgraph.graph.StateGraph(BorderPilotState)` and wires four nodes:

```
 TrendScout → MarketAnalyst → (decision ? ListingCraft : END)
 └────────► ListingCraft → QualityCheck → END
```

`BorderPilotState` is a `TypedDict(total=False)` (every field optional)
so partial updates from agents merge cleanly. Required inputs are
`seed_query`, `target_marketplaces`, `target_languages`; everything else
is filled as the workflow progresses.

The conditional edge after MarketAnalyst short-circuits when the
analyst returns `decision == "no-go"`. This is the pattern the JD calls
out: *Orchestrator协同者*.

## LLM abstraction

`tools/llm.py` exposes a small `BaseLLM` interface with three providers:

| Provider | When |
|---|---|
| `MockLLM` | default — deterministic & keyless |
| `AnthropicLLM` | `ANTHROPIC_API_KEY` set |
| `HuggingFaceLLM` | `HF_TOKEN` set |

`make_llm()` resolves in this order so the same code path runs in CI,
on HF Spaces cold-start, and in production.

## Per-agent design

| Agent | Inputs | Outputs | Tools |
|---|---|---|---|
| TrendScout | `seed_query`, `target_marketplaces` | `trends[]` | `tools.data.fetch_trends`, LLM re-rank |
| MarketAnalyst | top trend | `market_analysis` (decision + rationale) | LLM with strict JSON schema |
| ListingCraft | analyst brief + marketplaces | per-marketplace `ListingDraft` | LLM with locale prompt + JSON parser |
| QualityCheck | `listings` | `quality_report` (score + checks + recommendation) | deterministic rules + LLM editorial pass |

Each agent owns its own `system` prompt so **prompt engineering** is
visible per node (rather than one monolithic prompt) — this is what the
JD means by *"极限调优：深入折腾 Prompt Engineering"*.

## Compliance rules (QualityCheck)

* Title length ≤200 chars
* Bullets count per marketplace caps (Amazon:5, eBay:3, Shopify:6)
* Description length50–2000 chars
* Banned promotional terms per locale (`best`, `guaranteed`, …)

These are deliberately conservative; marketplace-specific rules live in
`listing_craft._LOCALE_DEFAULTS` and `quality_check._banned_for`.

## Deployment

* **Local**: `python app.py` → Gradio on `:7860`.
* **HF Spaces**: the file is HF-Spaces-compatible. Add `gradio` SDK
 to the Space `README.md` (see `deploy/huggingface/README.md`).
* **CLI**: `python -m border_pilot.cli demo` for a quick terminal run.

## Extending

* Swap a real catalogue (Shopify / Helium10 / Jungle Scout) into
 `tools/data.py` without touching the agents.
* Add a `listing_publisher` node that POSTs to Amazon SP-API.
* Add a `memory` node that pulls prior drafts from a vector store
 (the JD specifically calls out RAG).
