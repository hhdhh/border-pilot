# 🛰️ BorderPilot

> **Multi-agent workflow platform for cross-border e-commerce** —
> TrendScout → MarketAnalyst → ListingCraft → QualityCheck,
> orchestrated with [LangGraph](https://langchain-ai.github.io/langgraph/).

[![Python3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Built with LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)]()
[![Live demo (HF Spaces)](#-live-demo)](https://github.com/hhdhh/border-pilot)

---

## ✨ What is BorderPilot?

A recruiting-grade demo of how a team of specialised LLM agents can run an
**end-to-end cross-border e-commerce workflow**:

1. **TrendScout** surfaces candidate products from a seed query.
2. **MarketAnalyst** turns the top candidate into a go/no-go brief
 (TAM estimate, sweet spot, competitors, risk flags).
3. **ListingCraft** writes marketplace-ready listings in multiple
 locales (Amazon US/UK/DE/JP, eBay, Shopify, …).
4. **QualityCheck** runs rule-based + LLM-assisted compliance checks
 and emits an approval decision.

The orchestrator is a LangGraph state machine with **conditional edges**:
when the analyst returns `no-go`, the pipeline short-circuits to `END`.

The full workflow runs **with the mock LLM and zero API keys**, so it
boots cleanly on HuggingFace Spaces and in CI. Set
`ANTHROPIC_API_KEY` (Claude) or `HF_TOKEN` (Mistral / Llama) to swap in
a real model at runtime — no code changes required.

---

## 🚀 Live demo

> **HuggingFace Spaces** (link will be added after first deploy)
> → spin up `app.py`, paste a seed query, watch the four agents run.

Run locally:

```bash
git clone https://github.com/hhdhh/border-pilot
cd border-pilot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py # opens Gradio UI on http://127.0.0.1:7860
```

Or run headless:

```bash
PYTHONPATH=src BORDER_PILOT_LLM=mock python -m border_pilot.cli demo
```

---

## 🏗️ Architecture

```
 ┌─────────────┐ ranked trends ┌────────────────┐ decision=go ┌──────────────┐
 │ TrendScout │ ─────────────► │ MarketAnalyst │ ───────────► │ ListingCraft │
 └─────────────┘ └────────────────┘ watch / no-go ──► END └──────────────┘
 │
 ▼ per-locale drafts
 ┌──────────────┐
 │ QualityCheck │ ──► END (overall_score + recommendation)
 └──────────────┘
```

* **LangGraph** wires the nodes; conditional edges branch on analyst decision.
* **Typed state** (`BorderPilotState`) keeps the contract explicit.
* **Tool-using agents**: catalogue retrieval, JSON-constrained LLM output,
 deterministic compliance rules (title length, bullet count, banned words).
* **Pluggable LLM**: `make_llm()` selects `anthropic` / `huggingface` / `mock`
 from env vars. The mock keeps the demo fully offline.

Full design notes live in [`docs/architecture.md`](docs/architecture.md).

---

## 🧪 Tests

```bash
PYTHONPATH=src pytest -q
```

`tests/test_smoke.py` exercises the full graph with the mock LLM, plus
focused tests for `quality_check` (banned words, length rules) and the CLI.

---

## 🗂️ Project layout

```
border-pilot/
├── app.py # Gradio entrypoint (used by HF Spaces)
├── pyproject.toml
├── requirements.txt
├── src/
│ └── border_pilot/
│ ├── state.py # TypedDict state schema
│ ├── orchestrator.py # LangGraph wiring + run() helper
│ ├── cli.py # python -m border_pilot.cli
│ ├── agents/
│ │ ├── trend_scout.py
│ │ ├── market_analyst.py
│ │ ├── listing_craft.py
│ │ └── quality_check.py
│ └── tools/
│ ├── llm.py # Anthropic + HF + Mock providers
│ └── data.py # Trend catalogue / live-search hook
├── tests/
│ └── test_smoke.py
├── examples/
│ └── demo_run.py
├── docs/
│ └── architecture.md
└── deploy/
 └── huggingface/
 └── README.md
```

---

## 🧩 How it maps to the JD

If you came here from the **跨境出海 AI Agent工程师** posting, here is the
explicit trace from this repo to the role:

| Requirement | Where in this repo |
|---|---|
| Python + LangChain/LangGraph | `src/border_pilot/orchestrator.py` |
| Multi-agent / Agentic Workflow | `src/border_pilot/agents/*` |
| Tool-using agents | `src/border_pilot/tools/*`, `_parse_json_array` in trend_scout |
| RAG / prompt engineering hooks | `MockLLM` prompts per agent (each agent has its own system prompt + temperature) |
| Cross-border domain | ListingCraft writes per-marketplace drafts in en / en-GB / de / ja with marketplace caps |
| Shipping a live demo | `app.py` → HuggingFace Space |
| Open-source hygiene | pyproject.toml, tests, CLI, docs, MIT license |

---

## 🔐 Environment variables

| Var | Effect |
|---|---|
| `BORDER_PILOT_LLM=mock` (default) | Use the deterministic mock provider |
| `BORDER_PILOT_LLM=anthropic` + `ANTHROPIC_API_KEY` | Use Claude (`claude-3-5-sonnet-latest`) |
| `BORDER_PILOT_LLM=huggingface` + `HF_TOKEN` | Use HF Inference API (`Mistral-7B-Instruct-v0.3`) |
| `BORDER_PILOT_LIVE_SEARCH=1` | TrendScout will try a live search before falling back to catalogue |

---

## 📦 License

MIT — see [`LICENSE`](LICENSE).

---

> Built end-to-end in one session with an AI-native workflow:
> Cursor + Claude + this agent harness. PRs welcome.
