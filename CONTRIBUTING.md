# Contributing to Assumption Zero

Thanks for helping founders make better decisions before they build.

## Good contributions

- Improve research-source coverage or evidence normalization.
- Make competitor discovery more precise and easier to audit.
- Add or improve AI-provider adapters.
- Strengthen deterministic scoring tests.
- Improve accessibility, responsiveness, or report readability.
- Add realistic fixtures for failure cases and ambiguous evidence.

For large behavioral changes, open a feature request before implementation so the direction and test strategy can be agreed on first.

## Local setup

```bash
git clone https://github.com/ramizz1/assumption-zero.git
cd assumption-zero/backend
python -m venv .venv
```

Install backend development dependencies:

```bash
pip install -e ".[dev]"
```

Install frontend dependencies:

```bash
cd ../frontend
npm ci
```

## Quality checks

Before opening a pull request, run:

```bash
cd backend
.venv/Scripts/python -m pytest -q

cd ../frontend
npm run check
```

Use `.venv/bin/python` instead on macOS or Linux.

## Pull requests

- Keep the change focused and explain the user-facing outcome.
- Add tests for new behavior and regressions.
- Do not commit API keys, `.env`, saved analyses, or private reports.
- Document new CLI options, environment variables, or provider behavior.
- Include screenshots for visible UI changes.

By contributing, you agree that your contribution may be distributed under the project's MIT License.
