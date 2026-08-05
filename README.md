# Assumption Zero

**The open-source MVP validation engine.**  
Stress-test your idea before you build it.

> ⚠ **Disclaimer:** Assumption Zero provides decision support, not a prediction or substitute for real customer validation. Every claim is backed by evidence. Configure an AI provider for qualitative reasoning.

---

## What It Does

Assumption Zero analyzes a startup or MVP idea using real open-source information and multiple independent AI perspectives. For each idea it:

1. **Generates 25+ targeted research queries** across 13 evidence categories
2. **Collects evidence from 5 real sources** — GitHub, Hacker News, Reddit, Wikipedia, SearXNG
3. **Runs 3 independent AI perspectives** — Market Analyst, Skeptical Investor, Practical Builder
4. **Validates all AI citations** against collected evidence — hallucinated citations are flagged
5. **Calculates an Opportunity Score** (0–100) deterministically from weighted dimension scores
6. **Detects disagreements** between the three perspectives
7. **Generates 5 cheap validation experiments** ordered by cost and information value
8. **Exports a full report** as Markdown or JSON

---

## Quick Start

### Requirements

- **Python 3.12+**
- **Node.js 20+** (for the web interface)
- Internet access (for research providers — GitHub, HN, Reddit, Wikipedia are free)

### 1. Backend

```bash
cd backend
python -m venv .venv

# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -e "."
```

### 2. Configure (optional but recommended)

```bash
cp .env.example .env
# Edit .env to add your AI provider key
```

```env
# Choose your AI provider (default: beta — no config needed)
AI_PROVIDER=beta

# Beta AI uses OpenRouter free models under the hood.
# No key needed. Optionally add your own for higher limits:
# OPENROUTER_API_KEY=sk-or-v1-your-key
# OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# OR: Ollama (free, local, fully private)
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Optional: SearXNG for web search
SEARXNG_BASE_URL=http://localhost:8888
```

Without any AI configuration, Assumption Zero defaults to **Beta AI** — a built-in provider backed by free open-weight models (no sign-up, no key). Use **Template Analysis** (`mock`) for a fully offline, deterministic fallback.

### 3. Run the CLI

```bash
# Analyze an idea interactively
azero analyze

# Analyze from a JSON file
azero analyze --file examples/sample-idea.json

# Run the built-in example (LegalMind Local) through the real pipeline
azero demo

# List past analyses
azero list

# Show a full report
azero show ANALYSIS_ID

# Export as Markdown
azero export ANALYSIS_ID --format markdown --output report.md

# Export as JSON
azero export ANALYSIS_ID --format json --output report.json
```

### 4. Run the API

```bash
uvicorn assumption_zero.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Run the Web Interface

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## Architecture

```
assumption-zero/
├── backend/
│   └── assumption_zero/
│       ├── main.py            # FastAPI app factory
│       ├── cli.py             # Typer CLI
│       ├── config.py          # Settings (pydantic-settings)
│       ├── schemas.py         # All Pydantic types
│       ├── models.py          # SQLAlchemy DB models
│       ├── research/          # Evidence collection providers
│       │   ├── base.py        # ResearchProvider ABC
│       │   ├── github_provider.py
│       │   ├── hackernews_provider.py
│       │   ├── reddit_provider.py
│       │   ├── wikipedia_provider.py
│       │   └── searxng_provider.py
│       ├── llm/               # AI model adapters
│       │   ├── base.py        # LLMAdapter ABC + prompt templates
│       │   ├── mock_adapter.py      # Heuristic scoring (no key needed)
│       │   ├── gemini_adapter.py
│       │   ├── ollama_adapter.py
│       │   └── openai_compat_adapter.py
│       ├── analysis/          # Core analysis pipeline
│       │   ├── engine.py         # 9-stage orchestrator
│       │   ├── query_generator.py
│       │   ├── scoring.py        # Pure Python math
│       │   ├── confidence.py
│       │   ├── citation_validator.py
│       │   ├── competitor_merger.py
│       │   ├── disagreement.py
│       │   └── experiment_generator.py
│       ├── services/
│       │   └── analysis_service.py  # Bridge between API/CLI and engine
│       └── api/
│           └── routes.py       # FastAPI endpoints
└── frontend/
    └── src/
        ├── pages/              # HomePage, AnalysisPage, ProgressView, ReportView
        ├── components/         # Gauge, ScoreBreakdown, CompetitorCard, etc.
        ├── hooks/              # useAnalysis (polling)
        ├── lib/                # api.ts, utils.ts
        └── types/              # TypeScript types matching backend schemas
```

### Design Principles

- **One shared engine**: `AnalysisEngine` is used identically by both the API and the CLI
- **No fake data**: All evidence comes from real APIs. The "demo" runs the real pipeline on a sample idea
- **No predictions**: Results are decision support, not success probabilities
- **Deterministic scoring**: The Opportunity Score is pure Python math applied to AI output — no AI in the calculation itself
- **Transparent citations**: Every AI claim must cite a real evidence ID; invalid citations are flagged
- **Graceful degradation**: Provider failures never crash the analysis; they are reported in `provider_errors`

---

## Opportunity Score

The score (0–100) is calculated from 7 dimensions with fixed weights that sum to exactly 100:

| Dimension | Weight |
|---|---|
| Problem Evidence | 20% |
| Demand Signals | 20% |
| Competitive Gap | 15% |
| Distribution Feasibility | 15% |
| Unit Economics | 15% |
| Founder / Project Fit | 10% |
| Legal & Operational Risk | 5% |

Each AI perspective contributes raw scores (0–100) per dimension. The engine averages across perspectives and applies the weights. No AI is involved in the final calculation.

**Evidence Confidence** (Low / Medium / High) is calculated separately from the score, based on source count, diversity, reliability, recency, and citation validity.

---

## AI Providers

| Provider | Key Required | Cost | Notes |
|---|---|---|---|
| `beta` (default) | None | Free | Assumption Zero Beta AI — built-in, ready to use |
| `mock` | None | Free | Heuristic template scoring, fully offline |
| `ollama` | None | Free | Runs locally; requires [Ollama](https://ollama.ai) |

The **Beta AI** uses [OpenRouter](https://openrouter.ai) free-tier open-weight models (Llama 3.3 70B by default).
To bring your own key, set `OPENROUTER_API_KEY` in `.env`.

---

## Research Providers

| Provider | Key Required | What It Searches |
|---|---|---|
| GitHub | Optional (GITHUB_TOKEN) | OSS alternatives, repos |
| Hacker News | None | Startup discussions, complaints |
| Reddit | None | Communities, demand signals |
| Wikipedia | None | Market background, definitions |
| SearXNG | SEARXNG_BASE_URL | General web (self-hosted) |

---

## Docker

```bash
docker compose up
```

This starts:
- `backend` on port 8000
- `frontend` on port 5173

---

## Running Tests

**Backend:**
```bash
cd backend
pip install -e ".[dev]"
pytest
# 37 tests, ~0.5s
```

**Frontend:**
```bash
cd frontend
npm install
npm test
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `beta` | `beta`, `mock`, `ollama` |
| `OPENROUTER_API_KEY` | built-in | Override the shared Beta AI key |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.3-70b-instruct:free` | Model for Beta AI / OpenRouter |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `SEARXNG_BASE_URL` | — | Self-hosted SearXNG instance URL |
| `GITHUB_TOKEN` | — | GitHub PAT for higher rate limits |
| `DATABASE_URL` | `sqlite:///./az.db` | SQLAlchemy database URL |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `DEBUG` | `false` | Enable debug mode |

---

## Ethical Design

- **Never collects payment** from users in validation experiments without disclosure
- **No deceptive practices** in experiment templates
- **API keys stay server-side** — never exposed to the browser
- **Results are never published** — stored locally in SQLite
- **Hallucinated citations are detected** and flagged, not silently accepted

---

## License

MIT — see [LICENSE](LICENSE)

---

## Roadmap

- [ ] PDF export
- [ ] Competitor pricing tracker
- [ ] Slack/Discord notifications when analysis completes
- [ ] Team sharing (optional hosted mode)
- [ ] Perplexity AI provider adapter
- [ ] Rate-limiting and API key management UI

---

*Assumption Zero is open-source. Contributions welcome.*  
*This tool provides decision support, not a prediction or substitute for real customer validation.*
