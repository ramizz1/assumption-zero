# Assumption Zero

**The open-source MVP validation engine.**  
Stress-test your idea before you build it.

> ⚠ **Disclaimer:** Assumption Zero provides decision support, not a prediction or substitute for real customer validation. Every claim is backed by evidence.

---

## What It Does

Assumption Zero analyzes a startup or MVP idea using real live web search information and multiple independent AI perspectives. For each idea it:

1. **Generates 25+ targeted research queries** across 13 evidence categories
2. **Collects evidence from 7 real sources** — Live Web Search, Live News & Media, Arxiv Papers, GitHub, Hacker News, Reddit, Wikipedia
3. **Runs 3 independent AI perspectives** — Market Analyst, Skeptical Investor, Practical Builder
4. **Validates all AI citations** against collected evidence — hallucinated citations are flagged
5. **Calculates an Opportunity Score** (0–100) deterministically from weighted dimension scores
6. **Detects strategic risks & disagreements** between perspectives
7. **Generates actionable validation experiments** ordered by cost and information value
8. **Exports full reports** as Markdown or CSV/JSON

---

## Quick Start

### Requirements

- **Python 3.12+**
- **Node.js 20+** (for web interface)
- Internet access for live web research

### 1. Installation & Environment

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows (.venv/bin/activate on Linux/macOS)
pip install -e "."
```

### 2. OpenRouter API Key Tutorial

Assumption Zero includes built-in Beta AI access out-of-the-box. For higher rate limits and custom models, use your own **OpenRouter API Key**:

1. Visit **[https://openrouter.ai/keys](https://openrouter.ai/keys)**
2. Sign in with GitHub or Google (free, no credit card required)
3. Click **Create Key** and copy your `sk-or-v1-...` key
4. Set it in `.env` or pass it in the CLI/Web UI:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

---

## CLI Usage

```bash
# Analyze an idea interactively (prompts for OpenRouter key or uses built-in Beta key)
azero analyze

# Analyze from a JSON file
azero analyze --file examples/gotur-az.json

# View step-by-step idea guide
azero guide

# List saved reports
azero list

# Show full report for latest run (#1) or short ID
azero show 1

# Export as Markdown or CSV
azero export 1 --format markdown --output report.md
```

---

## Web Interface

### 1. Start Backend API (Port 8000)
```bash
cd backend
.venv\Scripts\uvicorn assumption_zero.main:app --reload --port 8000
```

### 2. Start Web Frontend (Port 5173)
```bash
cd frontend
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

## Opportunity Score Dimensions

| Dimension | Weight | Description |
|---|---|---|
| **Problem Evidence** | 20% | Real customer pain, existing workarounds |
| **Demand Signals** | 20% | Active search volume, market growth, purchase intent |
| **Competitive Gap** | 15% | Differentiation vs existing competitors |
| **Distribution Feasibility** | 15% | Go-to-market channels & CAC efficiency |
| **Unit Economics** | 15% | Margins, willingness to pay, pricing viability |
| **Founder / Project Fit** | 10% | Founder skills & runway vs requirements |
| **Legal & Operational Risk**| 5% | Regulatory, compliance & data privacy risks |

---

## Open-Source & License

Assumption Zero is open-source under the **MIT License**.  
GitHub Repository: **[https://github.com/ramizz1/assumption-zero](https://github.com/ramizz1/assumption-zero)**
