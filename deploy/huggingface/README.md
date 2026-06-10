---
title: BorderPilot
emoji: 🛰️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version:4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Multi-agent cross-border e-commerce workflow (LangGraph)
---

# 🛰️ BorderPilot

Multi-agent workflow for cross-border e-commerce, built with LangGraph.
See [`README.md`](../../README.md) for the full tour.

This Space runs the **mock LLM by default** — paste a seed query, pick
your target marketplaces, and watch TrendScout → MarketAnalyst →
ListingCraft → QualityCheck run end-to-end with no API keys required.

### Optional: swap in a real LLM

Add a secret named `ANTHROPIC_API_KEY` and set `BORDER_PILOT_LLM=anthropic`
in the Space variables to use Claude.
Or add `HF_TOKEN` and set `BORDER_PILOT_LLM=huggingface` to use a free
HuggingFace Inference model.
