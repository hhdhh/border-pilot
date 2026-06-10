# 🛰️ BorderPilot · 跨境电商 AI Agent 工作流平台

> **多 Agent 工作流 for 跨境出海** — TrendScout → MarketAnalyst → ListingCraft → QualityCheck，
> 用 [LangGraph](https://langchain-ai.github.io/langgraph/) 编排。

> **Multi-agent workflow platform for cross-border e-commerce** —
> TrendScout → MarketAnalyst → ListingCraft → QualityCheck,
> orchestrated with [LangGraph](https://langchain-ai.github.io/langgraph/).

[![Python3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Built with LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)]()
[![Live demo (HF Spaces)](#-live-demo)](https://github.com/hhdhh/border-pilot)

---

## 🇨🇳 中文说明

### ✨ 这是什么？

BorderPilot 是一个**端到端的跨境电商 AI Agent 协作平台**，展示了一组专业化
LLM Agent 如何跑通整个出海业务链条：

1. **TrendScout（趋势侦察）** —— 根据种子词（如 "wireless earbuds"）挖出候选爆品。
2. **MarketAnalyst（市场分析）** —— 对头部候选做 go/no-go 判断（市场规模、竞品、风险）。
3. **ListingCraft（多语言 Listing）** —— 针对 Amazon / eBay / Shopify 等多平台、多语言
 （en / en-GB / de / ja）批量生成合规 Listing。
4. **QualityCheck（合规校验）** —— 跑规则（标题长度、bullet 数量、违禁词）+ LLM 兜底审校。

Orchestrator 用 **LangGraph** 状态机编排，分析师返回 `no-go` 时自动短路退出 —— 这就是
JD 里反复提到的 "Orchestrator（协同者）"模式。

### 🧩 为什么能直接对接这个 JD？

| JD 要求 | 本项目对应实现 |
|---|---|
| Python + LangChain/LangGraph | `src/border_pilot/orchestrator.py`（LangGraph 状态机） |
| 多 Agent / Agentic Workflow | `src/border_pilot/agents/`（4 个独立 Agent） |
| Tool-using Agent | 每个 Agent 都用工具：目录检索、JSON 约束 LLM 输出、规则引擎 |
| 跨境出海/ERP/CRM | ListingCraft 输出多市场多语言 Listing，覆盖 Amazon/eBay/Shopify |
| 部署 + GitHub 链接 | 已部署 Gradio Demo，可对接 HF Spaces |
| 折腾欲 + 调优 | 每个 Agent 独立 system prompt + 温度，便于分节点调优 |
| 真实业务场景 | "选品 → 分析 → Listing → 合规"端到端跑通 |

### 🚀 一分钟跑起来

```bash
git clone https://github.com/hhdhh/border-pilot
cd border-pilot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py # 浏览器打开 http://127.0.0.1:7860
```

无需任何 API Key —— 默认走 mock LLM，全流程在本地 / Space 上都能跑。
设置 `ANTHROPIC_API_KEY` 后切到 Claude；设置 `HF_TOKEN` 切到 HuggingFace 免费模型。

### 📊 测试

```bash
PYTHONPATH=src pytest -q
```

**5/5 测试通过**，包含完整工作流 + 合规规则 + CLI。

---

## 🇬🇧 English

### ✨ What is BorderPilot?

A recruiting-grade demo of how a team of specialised LLM agents can run an
**end-to-end cross-border e-commerce workflow**:

1. **TrendScout** surfaces candidate products from a seed query.
2. **MarketAnalyst** turns the top candidate into a go/no-go brief
   (TAM estimate, sweet spot, competitors, risk flags).
3. **ListingCraft** writes marketplace-ready listings in multiple
   locales (Amazon US/UK/DE/JP, eBay, Shopify, ...).
4. **QualityCheck** runs rule-based + LLM-assisted compliance checks
   and emits an approval decision.

The orchestrator is a LangGraph state machine with **conditional edges**:
when the analyst returns `no-go`, the pipeline short-circuits to `END`.

The full workflow runs **with the mock LLM and zero API keys**, so it
boots cleanly on HuggingFace Spaces and in CI. Set
`ANTHROPIC_API_KEY` (Claude) or `HF_TOKEN` (Mistral / Llama) to swap in
a real model at runtime — no code changes required.

### 🧩 How it maps to the JD

If you came here from the **跨境出海 AI Agent工程师** posting, here is the
explicit trace from this repo to the role:

| Requirement | Where in this repo |
|---|---|
| Python + LangChain/LangGraph | `src/border_pilot/orchestrator.py` |
| Multi-agent / Agentic Workflow | `src/border_pilot/agents/*` |
| Tool-using agents | `src/border_pilot/tools/*`, `_parse_json_array` in trend_scout |
| RAG / prompt engineering hooks | `MockLLM` prompts per agent (each agent has its own system prompt + temperature) |
| Cross-border domain | ListingCraft writes per-marketplace drafts in en / en-GB / de / ja with marketplace caps |
| Shipping a live demo | `app.py` -> HuggingFace Space |
| Open-source hygiene | pyproject.toml, tests, CLI, docs, MIT license |

### 🚀 Quickstart

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

### 🏗️ Architecture

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

### 🧪 Tests

```bash
PYTHONPATH=src pytest -q
```

`tests/test_smoke.py` exercises the full graph with the mock LLM, plus
focused tests for `quality_check` (banned words, length rules) and the CLI.

---

## 🗂️ Project layout / 项目结构

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
>
> 一个会话内全栈搭出来：Cursor + Claude + 这个 Agent 脚手架。欢迎提 PR。
