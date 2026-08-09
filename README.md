<div align="center">
  <img src="frontend/public/logo.png" alt="Assumption Zero Logo" width="120" />
  <h1>Assumption Zero — MVP Validation Engine</h1>
  <img src="https://i.ibb.co/C3sbq4pq/Screenshot-2026-08-05-232315.png" alt="Screenshot" />
  <p><strong>The open-source MVP validation engine.</strong><br><em>Stress-test your idea before you build it.</em></p>
</div>

> [!IMPORTANT]  
> **Disclaimer:** Assumption Zero provides decision support and risk analysis. It is not a financial prediction or a substitute for direct customer validation. Every claim is grounded in evidence retrieved from primary research sources.

---

## Overview

Assumption Zero is an open-source validation engine designed to stress-test startup and product ideas before writing code. It combines live multi-source research with multiple independent AI analysis perspectives to calculate a deterministic **Opportunity Score (0–100)** and generate actionable validation experiments.

---

## Features & Capabilities

- 🔍 **Multi-Source Primary Research**  
  Retrieves live evidence from 7 sources: Live Web Search, News & Media, Arxiv Papers, GitHub Repositories, Hacker News, Reddit, and Wikipedia.
  
- 🧠 **Multi-Perspective AI Evaluation**  
  Evaluates ideas across 3 distinct perspectives:
  - **Market Analyst**: TAM, demand signals, monetization & pricing power.
  - **Skeptical Investor**: Competitive moats, switching costs, CAC & fatal failure modes.
  - **Practical Builder**: 90-day execution roadmap, tech stack risks & trust compliance.

- 📊 **Deterministic Scoring Engine**  
  Calculates a 0–100 Opportunity Score across 7 weighted dimensions using pure Python math rather than subjective AI score generation.

- 🛡️ **Citation & Hallucinated Evidence Filtering**  
  Cross-references AI citations against verified evidence items. Hallucinated or non-existent source references are flagged and rejected automatically.

- ⚡ **Decision Intelligence & Next Steps**  
  Identifies critical assumption risks per perspective, measures evidence quality metrics, and generates 5 immediate, prioritized validation actions.

- 💻 **Formal, High-Legibility CLI & Modern Web UI**  
  Includes a formal, clean CLI (`azero`) optimized for clarity and enterprise reporting, as well as a full React/TypeScript web app.

---

## Opportunity Score Breakdown

The Opportunity Score is calculated deterministically across 7 dimensions:

| Dimension | Weight | Description |
|---|:---:|---|
| **Problem Evidence** | **20%** | Real customer pain signals and existing workarounds |
| **Demand Signals** | **20%** | Active search volume, market growth, purchase intent |
| **Competitive Gap** | **15%** | Differentiation vs existing market competitors |
| **Distribution Feasibility** | **15%** | Go-to-market channels & CAC efficiency |
| **Unit Economics** | **15%** | Margins, willingness to pay & pricing viability |
| **Founder / Project Fit** | **10%** | Technical skills and runway alignment |
| **Legal & Operational Risk** | **5%** | Regulatory, compliance & data privacy risks |

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+** (for web frontend)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ramizz1/assumption-zero.git
   cd assumption-zero
   ```

2. **Setup the Python backend:**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate      # On Windows
   # source .venv/bin/activate # On Linux/macOS
   pip install -e "."
   ```

3. **Configure Environment:**
   Copy `.env.example` to `.env` in the root directory:
   ```bash
   cp .env.example .env
   ```

---

## OpenRouter API Key Setup

Assumption Zero works without an AI key by running a clearly labelled, deterministic baseline over collected evidence. For deeper qualitative perspectives, configure your own **OpenRouter API Key** (or another supported provider):

1. Visit **[https://openrouter.ai/keys](https://openrouter.ai/keys)**
2. Sign in with GitHub or Google (free, no credit card required)
3. Click **Create Key** and copy your `sk-or-v1-...` key
4. Add it to your `.env` file or export it in your shell:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

> [!TIP]
> **Highly Recommended First Step for CLI**: Run `azero config` immediately after installation! The interactive wizard will set up your AI provider API keys (Groq, OpenRouter, OpenAI, OpenCode, Ollama) and automatically enable smart multi-key failover.

---

## CLI Usage (`azero`)

> [!IMPORTANT]
> **First Run**: Highly recommended to execute `azero config` first to configure API keys and active AI provider.

```bash
# 🔑 Recommended First Step: Interactively configure API keys & AI providers
azero config

# Interactive analysis (prompts for idea details & provider selection)
azero analyze

# Analyze an idea from a structured JSON file
azero analyze --file examples/sample-idea.json

# Analyze from a freeform text prompt
azero prompt "A privacy-first AI meeting summarizer for law firms"

# Pin the same live research providers used by the web pipeline (repeat -r)
azero analyze --prompt "AI scheduling for dentists" -r "Web Search" -r GitHub

# Run the same real example available from the web home page
azero demo

# Re-run the web report's adjustable unit-economics stress test
azero simulate 1 --cac 120 --variable-cost 8 --fixed-costs 900 --churn 4

# Check an AI-provider configuration before starting an analysis
azero verify-provider openrouter --api-key sk-or-v1-your-key

# View step-by-step idea formulation guide
azero guide

# List all saved analyses
azero list

# Display full report for an analysis ID (or latest)
azero show 1

# Export report as Markdown or JSON
azero export 1 --format markdown --output report.md

# Display system configuration and version info
azero version
```

The CLI and web interface use the same analysis engine and the same root
`azero_data` history. Analyses started from either interface appear in both
`azero list` and the web **History** view.

---

## Web Interface

### 1. Launch FastAPI Backend API (Port 8000)
```bash
cd backend
.venv\Scripts\uvicorn assumption_zero.main:app --reload --port 8000
```

### 2. Launch Vite/React Web Frontend (Port 5173)
```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.

### Publishing safely

Before exposing Assumption Zero on a public domain:

- Serve it only over HTTPS because users may supply their own AI-provider keys.
- Set `SSRF_PROTECTION_ENABLED=true` so custom provider URLs cannot target services on the host's private network.
- Set `CORS_ORIGINS` to a JSON array containing only your real frontend origin.
- Put rate limiting at the reverse proxy or hosting layer; live research and AI calls can be expensive.
- Persist `azero_data` on a protected volume and decide how long user analyses should be retained.
- Never commit `.env`; the repository ignores it and `.env.example` contains placeholders only.

---

## Architecture & Project Structure

```
assumption-zero/
├── backend/
│   ├── assumption_zero/
│   │   ├── analysis/        # Core scoring engine, citation validator & orchestrator
│   │   ├── api/             # FastAPI REST endpoints
│   │   ├── llm/             # OpenRouter, Gemini, Ollama & Mock adapters
│   │   ├── research/        # Web Search, Arxiv, GitHub, HN, Reddit, Wiki providers
│   │   ├── cli.py           # Formal Typer CLI (azero command)
│   │   ├── main.py          # FastAPI application entry point
│   │   └── schemas.py       # Pydantic data models
│   └── tests/               # Backend Pytest suite
├── frontend/
│   ├── src/                 # React components, hooks, design tokens & pages
│   └── vite.config.ts       # Vite build configuration
├── examples/                # Sample input JSONs
├── README.md
└── LICENSE
```

---

## Testing

Run the automated backend test suite:

```bash
cd backend
.venv\Scripts\python -m pytest -q
```

Run the complete frontend quality gate:

```bash
cd frontend
npm run check
```

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.  
GitHub Repository: **[https://github.com/ramizz1/assumption-zero](https://github.com/ramizz1/assumption-zero)**
