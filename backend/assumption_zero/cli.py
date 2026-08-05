"""
Assumption Zero CLI — MVP Validation Engine
Clean, formal, and structured terminal interface.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from assumption_zero import __version__

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Formal Professional Theme ──────────────────────────────────────────────────
THEME = Theme(
    {
        "a0.accent":  "bold white",         # primary text accent
        "a0.muted":   "dim",                # secondary / metadata
        "a0.good":    "bold green",         # high scores / positive status
        "a0.warn":    "bold yellow",        # medium scores / warning status
        "a0.bad":     "bold red",           # low scores / danger status
        "a0.info":    "cyan",               # informational text
        "a0.label":   "bold white",         # labels
        "a0.section": "bold cyan",          # section headers
        "a0.market":  "cyan",               # market analyst perspective
        "a0.skeptic": "magenta",            # skeptic perspective
        "a0.builder": "green",              # builder perspective
    }
)

console = Console(theme=THEME, highlight=False, legacy_windows=False)
err_console = Console(stderr=True, style="bold red", legacy_windows=False)

DISCLAIMER = (
    "Assumption Zero provides decision support, not a prediction "
    "or substitute for real customer validation. Results are for "
    "informational purposes only."
)

TAGLINE = "Stress-test your idea before you build it."

app = typer.Typer(
    name="azero",
    help="Assumption Zero — The open-source MVP validation engine",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ── Formatting Helpers ────────────────────────────────────────────────────────


def _score_color(score: float) -> str:
    if score >= 65:
        return "green"
    if score >= 45:
        return "yellow"
    return "red"


def _score_bar(score: float, width: int = 24) -> str:
    filled = max(0, min(width, int(score / 100 * width)))
    col = _score_color(score)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{col}][{bar}][/] [{col}]{score:.0f}/100[/]"


def _rec_color(rec: str) -> str:
    return {
        "Build": "bold green",
        "Test First": "bold yellow",
        "Pivot": "bold yellow",
        "Avoid": "bold red",
    }.get(rec, "white")


def _conf_color(conf: str) -> str:
    return {"high": "green", "medium": "yellow", "low": "red"}.get(conf.lower(), "white")


def _perspective_color(name: str) -> str:
    return {
        "market_analyst": "cyan",
        "skeptical_investor": "magenta",
        "practical_builder": "green",
    }.get(name, "white")


# ── Layout Helpers ────────────────────────────────────────────────────────────


def _print_splash() -> None:
    console.print()
    console.print(f"[bold cyan]ASSUMPTION ZERO[/]  [dim]v{__version__}[/]  |  [dim]{TAGLINE}[/]")
    console.print(Rule(style="dim cyan"))
    console.print()


def _print_section(title: str, icon: str = "") -> None:
    console.print()
    console.print(Rule(f"[bold cyan]{title.upper()}[/]", style="dim cyan"))
    console.print()


def _print_disclaimer() -> None:
    console.print()
    console.print(
        Panel(
            f"[dim]{DISCLAIMER}[/]",
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )
    console.print()


# ── Engine Runner ─────────────────────────────────────────────────────────────


def _build_engine_sync():
    from assumption_zero.analysis.engine import AnalysisEngine
    from assumption_zero.services.analysis_service import (
        build_llm_adapter,
        build_research_providers,
    )
    llm = build_llm_adapter()
    providers = build_research_providers()
    return AnalysisEngine(providers=providers, llm_adapter=llm)


STAGE_LABELS = {
    "clarifying_idea":              ("Clarifying project scope", "1/6"),
    "generating_queries":           ("Building research query set", "2/6"),
    "collecting_evidence":          ("Collecting evidence from primary sources", "3/6"),
    "running_market_analyst":       ("Analyzing market dynamics & sizing", "4/6"),
    "running_skeptical_investor":   ("Analyzing moat & risk factors", "4/6"),
    "running_practical_builder":    ("Analyzing execution & roadmap", "4/6"),
    "calculating_score":            ("Calculating opportunity score", "5/6"),
    "generating_experiments":       ("Designing validation experiments", "6/6"),
    "complete":                     ("Analysis complete", "DONE"),
}


def _run_analysis_sync(idea, is_demo: bool = False):
    import uuid
    engine = _build_engine_sync()
    analysis_id = str(uuid.uuid4())
    current_label = ["Starting engine..."]

    async def _run():
        async def on_progress(stage, desc):
            label, step = STAGE_LABELS.get(stage.value, (desc, "•"))
            current_label[0] = f"[{step}] {label}..."

        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn("[cyan]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(current_label[0], total=None)

            async def _watch():
                while True:
                    await asyncio.sleep(0.15)
                    progress.update(task, description=current_label[0])

            watcher = asyncio.create_task(_watch())
            try:
                result = await engine.run(
                    idea=idea,
                    analysis_id=analysis_id,
                    progress_callback=on_progress,
                    is_demo=is_demo,
                )
            finally:
                watcher.cancel()
                try:
                    await watcher
                except asyncio.CancelledError:
                    pass
        return result

    return asyncio.run(_run())


# ── Report Renderer ───────────────────────────────────────────────────────────


def _print_report(result) -> None:
    from assumption_zero.schemas import AnalysisStatus

    if result.status == AnalysisStatus.FAILED:
        err_console.print(f"Analysis failed: {result.error_message}")
        return

    score = result.opportunity_score
    conf = result.evidence_confidence
    rec = result.recommendation

    score_val = score.total if score else 0.0
    rec_str = rec.value if rec else "Unknown"
    conf_str = conf.value.upper() if conf else "UNKNOWN"
    conf_col = _conf_color(conf.value if conf else "low")

    # ── 1. Executive Verdict ──────────────────────────────────────
    _print_section("Executive Verdict")

    verdict_text = (
        f"  [bold white]Opportunity Score:[/]    {_score_bar(score_val)}\n"
        f"  [bold white]Recommendation:[/]       [{_rec_color(rec_str)}]{rec_str}[/]\n"
        f"  [bold white]Evidence Confidence:[/]  [{conf_col}]{conf_str}[/]\n"
    )
    if result.most_dangerous_assumption:
        verdict_text += (
            f"\n  [bold red]CRITICAL RISK / MOST DANGEROUS ASSUMPTION[/]\n"
            f"  [white]{result.most_dangerous_assumption}[/]\n"
        )

    console.print(
        Panel(
            Text.from_markup(verdict_text),
            title=f"[bold cyan]{result.idea_input.name}[/]",
            border_style="dim cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    # ── 2. Score Breakdown ────────────────────────────────────────
    if score and score.dimensions:
        _print_section("Opportunity Score Breakdown")

        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            padding=(0, 1),
            show_edge=False,
        )
        table.add_column("Dimension", min_width=30, style="white")
        table.add_column("Score", justify="right", width=8)
        table.add_column("Bar", width=22)
        table.add_column("Weight", justify="right", width=7, style="dim")
        table.add_column("Conf", width=8)

        for dim in score.dimensions:
            col = _score_color(dim.raw_score)
            table.add_row(
                dim.display_name,
                f"[{col}]{dim.raw_score:.0f}[/]",
                _score_bar(dim.raw_score, 14),
                f"{dim.weight}%",
                f"[{_conf_color(dim.confidence.value)}]{dim.confidence.value[0].upper()}[/]",
            )

        table.add_section()
        table.add_row(
            "[bold white]Total Score[/]",
            f"[{_score_color(score_val)} bold]{score_val:.0f}[/]",
            _score_bar(score_val, 14),
            "[dim]100%[/]",
            "",
        )
        console.print(table)

    # ── 3. Evidence ───────────────────────────────────────────────
    _print_section("Evidence Collected")

    ev_count = len(result.evidence)
    sources = sorted(set(e.source_name for e in result.evidence))
    console.print(
        f"  [bold white]{ev_count} evidence items[/]  [dim]collected from[/]  "
        f"[cyan]{', '.join(sources)}[/]"
    )

    if result.provider_errors:
        console.print(f"\n  [yellow][WARNING] {len(result.provider_errors)} provider issue(s):[/]")
        for err in result.provider_errors[:3]:
            console.print(f"    - [dim]{err[:110]}[/]")

    if result.strongest_supporting:
        console.print()
        console.print(
            Panel(
                f"[white]{result.strongest_supporting[:280]}[/]",
                title="[bold green]Strongest Supporting Evidence[/]",
                border_style="dim green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
    if result.strongest_contradicting:
        console.print(
            Panel(
                f"[white]{result.strongest_contradicting[:280]}[/]",
                title="[bold red]Strongest Contradicting Evidence[/]",
                border_style="dim red",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    # ── 4. Competitors ────────────────────────────────────────────
    if result.competitors:
        _print_section(f"Competitors ({len(result.competitors)} Identified)")

        comp_table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            show_edge=False,
            padding=(0, 1),
        )
        comp_table.add_column("Name", min_width=20, style="bold white")
        comp_table.add_column("Type", width=14, style="dim")
        comp_table.add_column("Description")

        for comp in result.competitors[:10]:
            desc = comp.description[:75] + "..." if len(comp.description) > 75 else comp.description
            comp_table.add_row(
                comp.name[:28],
                comp.competitor_type.value,
                f"[white]{desc}[/]",
            )
        console.print(comp_table)

    # ── 5. AI Perspectives ────────────────────────────────────────
    _print_section("AI Strategic Perspectives")

    for p in result.perspectives:
        pcol = _perspective_color(p.perspective_name.value)
        rec_c = _rec_color(p.recommendation.value)

        # Parse key findings section titles
        findings_lines = []
        current_section = ""
        for f in p.key_findings:
            if f.startswith("§") and f.endswith("§"):
                current_section = f.strip("§").upper()
                findings_lines.append(f"\n  [bold cyan][ {current_section} ][/]")
            else:
                findings_lines.append(f"  - [white]{f}[/]")

        findings_text = "\n".join(findings_lines) if findings_lines else ""

        risks_text = ""
        if p.risks:
            risks_text = "\n\n  [bold red][ RISKS IDENTIFIED ][/]\n" + "\n".join(
                f"  - [white]{r}[/]" for r in p.risks
            )
        opps_text = ""
        if p.opportunities:
            opps_text = "\n\n  [bold green][ OPPORTUNITIES ][/]\n" + "\n".join(
                f"  - [white]{o}[/]" for o in p.opportunities
            )

        body_text = (
            f"  [bold white]Verdict:[/] [{rec_c}]{p.recommendation.value}[/]   [dim](Model: {p.model_id})[/]\n\n"
            f"  [white]{p.summary}[/]"
            f"{findings_text}"
            f"{risks_text}"
            f"{opps_text}"
        )

        console.print(
            Panel(
                body_text,
                title=f"[bold {pcol}]{p.perspective_display.upper()}[/]",
                border_style="dim cyan",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

    # ── 6. Disagreements ─────────────────────────────────────────
    if result.disagreements:
        _print_section(f"Model Disagreements ({len(result.disagreements)})")
        for d in result.disagreements:
            console.print(f"  [bold yellow][!][/] [bold white]{d.topic}[/]")
            for pos in d.positions:
                console.print(f"    - [dim]{pos.perspective}:[/] [white]{pos.position}[/]")
            console.print()

    # ── 7. Decision Intelligence ──────────────────────────────────
    _print_section("Decision Intelligence")

    if result.perspectives:
        console.print("  [bold white]Critical Assumptions per Perspective:[/]")
        for p in result.perspectives:
            pcol = _perspective_color(p.perspective_name.value)
            console.print(
                f"    - [{pcol}]{p.perspective_display}:[/] "
                f"[white]{p.most_dangerous_assumption}[/]"
            )
        console.print()

    if result.evidence:
        from assumption_zero.schemas import ReliabilityLevel

        high_rel = sum(1 for e in result.evidence if e.reliability == ReliabilityLevel.HIGH)
        n = len(result.evidence)
        quality_pct = int(high_rel / n * 100) if n else 0

        console.print(f"  [bold white]Evidence Quality ({n} items):[/]")
        console.print(f"    High-reliability proportion: {_score_bar(float(quality_pct), 16)}")
        console.print()

    # ── 8. Next Steps ─────────────────────────────────────────────
    console.print("  [bold white]Recommended Next Steps:[/]")
    next_steps = [
        "Conduct 5 discovery interviews with target segment customers before writing code.",
        "Create a lean landing page to measure conversion interest and sign-up intent.",
        "Manually deliver core value to 3 early users to validate willingness to pay.",
        "Allocate a 1-week budget ($0-$200) to test riskiest distribution channel.",
        "Define primary success metric (retention, revenue, NPS) and measure from Day 1.",
    ]
    if result.perspectives:
        for p in result.perspectives:
            if "builder" in p.perspective_name.value:
                next_steps.insert(0, f"Scope check: {p.most_dangerous_assumption}")
                break
    for i, step in enumerate(next_steps[:5], 1):
        console.print(f"    {i}. [white]{step}[/]")
    console.print()

    # ── 9. Validation Experiments ─────────────────────────────────
    if result.experiments:
        _print_section(f"Validation Experiments ({len(result.experiments)})")

        for i, exp in enumerate(result.experiments, 1):
            meta = f"[dim]Est. Cost:[/] [yellow]{exp.estimated_cost_range}[/]   |   [dim]Est. Time:[/] [cyan]{exp.estimated_time}[/]"
            body = (
                f"{meta}\n\n"
                f"  [bold white]Assumption Tested:[/]  [white]{exp.assumption_tested}[/]\n"
                f"  [bold white]Why It Matters:[/]     [white]{exp.why_it_matters}[/]\n"
                f"  [bold white]Procedure:[/]         [white]{exp.procedure}[/]\n\n"
                f"  [bold green]Success Criteria:[/]  [white]{exp.success_threshold}[/]\n"
                f"  [bold red]Failure Criteria:[/]  [white]{exp.failure_threshold}[/]\n\n"
                f"  [dim]Ethics / Compliance: {exp.legal_ethical}[/]"
            )
            console.print(
                Panel(
                    body,
                    title=f"[bold cyan]Experiment {i} — {exp.title}[/]",
                    border_style="dim cyan",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )

    # ── 10. Missing Information ───────────────────────────────────
    if result.missing_information:
        _print_section("Missing Information")
        for m in result.missing_information:
            console.print(f"  - [white]{m}[/]")

    _print_disclaimer()


# ── Export Markdown ───────────────────────────────────────────────────────────


def _export_markdown(result) -> str:
    lines = [
        f"# Assumption Zero — {result.idea_input.name}",
        "",
        f"> ⚠ {DISCLAIMER}",
        "",
        "## Executive Verdict",
        "",
    ]
    if result.opportunity_score:
        lines.append(f"**Opportunity Score:** {result.opportunity_score.total:.0f}/100")
    if result.evidence_confidence:
        lines.append(f"**Evidence Confidence:** {result.evidence_confidence.value.upper()}")
    if result.recommendation:
        lines.append(f"**Recommendation:** {result.recommendation.value}")
    if result.most_dangerous_assumption:
        lines.append(f"**Most Dangerous Assumption:** {result.most_dangerous_assumption}")

    lines += ["", "## Score Breakdown", ""]
    if result.opportunity_score:
        lines.append("| Dimension | Score | Weight | Confidence |")
        lines.append("|---|---|---|---|")
        for d in result.opportunity_score.dimensions:
            lines.append(
                f"| {d.display_name} | {d.raw_score:.0f} | {d.weight}% | {d.confidence.value.upper()} |"
            )
        lines.append(f"| **Total** | **{result.opportunity_score.total:.0f}** | 100% | |")

    lines += ["", "## Evidence", ""]
    for e in result.evidence:
        lines.append(f"- **[{e.evidence_id}]** [{e.title}]({e.url}) — *{e.source_name}*")

    lines += ["", "## Competitors", ""]
    for comp in result.competitors:
        lines.append(f"- **{comp.name}** ({comp.competitor_type.value}) — {comp.description[:120]}")

    lines += ["", "## AI Perspectives", ""]
    for p in result.perspectives:
        lines += [
            f"### {p.perspective_display}",
            f"*Model: {p.model_id} · Recommendation: {p.recommendation.value}*",
            "",
            p.summary,
        ]
        if p.key_findings:
            lines += ["", "**Key Findings:**"] + [f"- {f}" for f in p.key_findings]
        if p.risks:
            lines += ["", "**Risks:**"] + [f"- {r}" for r in p.risks]
        if p.opportunities:
            lines += ["", "**Opportunities:**"] + [f"- {o}" for o in p.opportunities]
        lines.append("")

    lines += ["", "## Validation Experiments", ""]
    for i, exp in enumerate(result.experiments, 1):
        lines += [
            f"### Experiment {i}: {exp.title}",
            f"**Cost:** {exp.estimated_cost_range} | **Time:** {exp.estimated_time}",
            f"**Assumption:** {exp.assumption_tested}",
            f"**Why it matters:** {exp.why_it_matters}",
            f"**Procedure:** {exp.procedure}",
            f"**Success if:** {exp.success_threshold}",
            f"**Failure if:** {exp.failure_threshold}",
            f"**Ethics:** {exp.legal_ethical}",
            "",
        ]

    if result.missing_information:
        lines += ["## Missing Information", ""]
        for m in result.missing_information:
            lines.append(f"- {m}")

    lines += [
        "",
        "---",
        "",
        f"*Generated by Assumption Zero v{__version__}*",
        f"*{DISCLAIMER}*",
    ]
    return "\n".join(lines)


# ── Interactive Form ──────────────────────────────────────────────────────────


def _ask_idea():
    from assumption_zero.schemas import IdeaInput

    console.print()
    console.print("[bold cyan]Step-by-Step Idea Definition[/]\n")

    def ask(label: str, hint: str = "", required: bool = False) -> str:
        suffix = " [red](required)[/]" if required else " [dim](optional)[/]"
        hint_str = f" [dim]e.g. {hint}[/]" if hint else ""
        while True:
            val = Prompt.ask(
                f"  [cyan]›[/] [bold white]{label}[/]{suffix}{hint_str}",
                default="",
                console=console,
            ).strip()
            if required and not val:
                console.print("    [red]Error: This field is required.[/]")
                continue
            return val

    name = ask("Idea / product name", "LegalMind Local", required=True)
    description = ask("Short description", "On-device AI legal meeting summarizer for small law firms", required=True)

    _print_section("The Problem")
    problem = ask("Problem being solved", "Attorneys lose 10+ hours/week summarizing client meetings due to cloud data privacy compliance", required=True)
    customer = ask("Target customer", "Solo practitioners and small law firms (1-20 attorneys)", required=True)
    geography = ask("Target geography", "United States", required=True)

    import os
    if os.getenv("OPENROUTER_API_KEY"):
        console.print("  [green]Using OpenRouter API key from environment[/]\n")
    else:
        _print_section("AI Key Setup")
        console.print(
            "  [dim]Get a free OpenRouter key at:[/] [cyan]https://openrouter.ai/keys[/]\n"
            "  [dim]Press Enter to use built-in Assumption Zero Beta key.[/]\n"
        )
        user_key = ask("OpenRouter API Key", "sk-or-v1-...")
        if user_key:
            os.environ["OPENROUTER_API_KEY"] = user_key
            console.print("  [green]Using custom OpenRouter API key[/]\n")

    _print_section("Business Details")
    model = ask("Business model", "SaaS subscription per seat")
    price = ask("Expected price", "$49/month per attorney seat")
    skills = ask("Founder skills", "Full-stack developer (Python + React)")
    budget = ask("Available budget / runway", "$15,000 for 6 months")
    competitors = ask("Known competitors", "Otter.ai, Fireflies.ai")

    _print_section("Strategic Insights")
    advantage = ask("Unfair advantage / Moat", "Proprietary algorithm, direct distribution channel with industry partners")
    assumptions = ask("Core assumption to test", "Target customers will pay for on-device privacy over cloud alternatives")
    context = ask("Additional context", "Web app + Mobile client backed by REST API")

    return IdeaInput(
        name=name,
        description=description,
        problem=problem,
        target_customer=customer,
        geography=geography,
        business_model=model or None,
        price=price or None,
        founder_skills=skills or None,
        budget=budget or None,
        known_competitors=competitors or None,
        unfair_advantage=advantage or None,
        key_assumptions=assumptions or None,
        additional_context=context or None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def guide() -> None:
    """Show the guide for formulating startup ideas."""
    _print_splash()
    _print_section("Idea Formulation Guide")

    guide_text = (
        "[bold white]To get actionable insights and realistic scores from Assumption Zero:[/]\n\n"
        "[bold cyan]1. Precise Problem Definition[/]\n"
        "   State who suffers, current broken alternatives, and financial or time cost.\n"
        "   [dim]Example: 'Solo law firms lose 10+ hours/week summarizing meetings due to privacy compliance.'[/]\n\n"
        "[bold cyan]2. Target Customer & Geography[/]\n"
        "   Define specific demographics, size, and location.\n"
        "   [dim]Example: 'Solo law practice attorneys in the US with 1-20 employees.'[/]\n\n"
        "[bold cyan]3. Competitors & Alternatives[/]\n"
        "   Include direct software tools (e.g. Otter.ai) and indirect solutions (Excel, WhatsApp).\n\n"
        "[bold cyan]4. Budget & Founder Fit[/]\n"
        "   Specify developer skills and runway to evaluate technical & execution risk.\n"
    )
    console.print(Panel(guide_text, border_style="dim cyan", box=box.ROUNDED, padding=(1, 2)))


@app.command()
def analyze(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to a JSON file with IdeaInput fields"
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p", help="Analyze from a single freeform text prompt"
    ),
) -> None:
    """
    Analyse an MVP idea interactively, from a 1-prompt text, or from a JSON file.
    """
    _print_splash()

    if file:
        if not file.exists():
            err_console.print(f"File not found: {file}")
            raise typer.Exit(1)
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            from assumption_zero.schemas import IdeaInput
            idea = IdeaInput(**data)
            console.print(
                f"[dim]Loaded from[/] [cyan]{file}[/]\n"
                f"  [bold white]Idea:[/] [bold cyan]{idea.name}[/]"
            )
        except Exception as exc:
            err_console.print(f"Invalid idea file: {exc}")
            raise typer.Exit(1)
    elif prompt:
        console.print("[dim]Parsing freeform prompt using AI...[/]")
        from assumption_zero.services.analysis_service import build_llm_adapter
        llm = build_llm_adapter()
        idea = asyncio.run(llm.parse_raw_prompt(prompt))
        console.print(f"[green]Extracted Idea:[/] [bold cyan]{idea.name}[/]")
    else:
        _print_section("Idea Definition")
        idea = _ask_idea()

    console.print()
    console.print(
        Panel(
            f"  [bold white]Idea:[/]  [bold cyan]{idea.name}[/]\n"
            f"  [white]{idea.description}[/]\n\n"
            f"  [dim]Running analysis engine...[/]",
            border_style="dim cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()
    result = _run_analysis_sync(idea)
    _print_report(result)


@app.command()
def prompt(
    text: Optional[str] = typer.Argument(None, help="Single natural language text prompt describing your startup idea"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to a text or markdown file containing your idea prompt"),
) -> None:
    """Analyze a startup idea from a freeform text prompt or text/markdown file."""
    if file:
        if not file.exists():
            err_console.print(f"File not found: {file}")
            raise typer.Exit(1)
        text = file.read_text(encoding="utf-8")
        console.print(f"[dim]Loaded prompt from[/] [cyan]{file}[/]")

    if not text:
        _print_splash()
        _print_section("Freeform Input Mode")
        console.print(
            "  [dim]Paste your startup idea prompt below.[/]\n"
            "  [dim]Type 'END' on a new line when finished, or pass a file: azero prompt -f my_idea.txt[/]\n"
        )
        lines = []
        try:
            while True:
                line = input("  › ")
                if line.strip().upper() == "END":
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        text = "\n".join(lines).strip()

        if not text:
            console.print("  [red]Error: Prompt cannot be empty.[/]")
            raise typer.Exit(1)

    analyze(file=None, prompt=text)


@app.command(name="list")
def list_cmd() -> None:
    """List all saved analyses ordered by most recent."""
    _print_splash()

    async def _list():
        from assumption_zero.services.analysis_service import list_analyses
        return await list_analyses()

    items = asyncio.run(_list())

    if not items:
        console.print(
            Panel(
                "[white]No analyses yet.[/]\n"
                "Run [bold cyan]azero analyze[/] to analyse your first idea,\n"
                "or [bold cyan]azero guide[/] to view idea formatting tips.",
                border_style="dim cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
        return

    table = Table(
        title="Saved Analyses",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("#", width=4, style="cyan")
    table.add_column("ID", width=10, style="dim")
    table.add_column("Idea", min_width=24, style="bold white")
    table.add_column("Status", width=10)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Verdict", width=13)
    table.add_column("Created", width=17, style="dim")

    for i, item in enumerate(items, 1):
        status_col = "green" if item.status.value == "complete" else "yellow"
        score_str = (
            f"[{_score_color(item.opportunity_score)}]{item.opportunity_score:.0f}[/]"
            if item.opportunity_score is not None
            else "[dim]—[/]"
        )
        rec_str = (
            f"[{_rec_color(item.recommendation.value)}]{item.recommendation.value}[/]"
            if item.recommendation
            else "[dim]—[/]"
        )
        created = item.created_at.strftime("%b %d %H:%M") if item.created_at else "—"
        table.add_row(
            f"#{i}",
            item.analysis_id[:8],
            item.idea_name[:26],
            f"[{status_col}]{item.status.value}[/]",
            score_str,
            rec_str,
            created,
        )

    console.print(table)
    console.print(
        f"\n[dim]  Use [/][bold cyan]azero show 1[/][dim] or [/][bold cyan]azero show {items[0].analysis_id[:8]}[/][dim] to view report.[/]"
    )


@app.command()
def show(
    analysis_id: Optional[str] = typer.Argument(
        None, help="Analysis ID, 8-char short ID (e.g. b28a73fb), or index (1, 2, ...). Omit for latest."
    ),
) -> None:
    """Show the full report for a saved analysis. Omit ID to show the latest analysis."""
    _print_splash()

    target_id = analysis_id or "1"

    async def _get():
        from assumption_zero.services.analysis_service import get_analysis
        return await get_analysis(target_id)

    result = asyncio.run(_get())
    if not result:
        err_console.print(f"Analysis '{target_id}' not found.")
        console.print(f"[dim]Run [/][bold cyan]azero list[/][dim] to see all saved analyses.[/]")
        raise typer.Exit(1)

    _print_report(result)


@app.command()
def export(
    analysis_id: Optional[str] = typer.Argument(
        None, help="Analysis ID, short ID, or index (1, 2, ...). Omit for latest."
    ),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export an analysis as Markdown or JSON."""
    target_id = analysis_id or "1"

    async def _get():
        from assumption_zero.services.analysis_service import get_analysis
        return await get_analysis(target_id)

    result = asyncio.run(_get())
    if not result:
        err_console.print(f"Analysis '{target_id}' not found.")
        raise typer.Exit(1)

    fmt = format.lower()
    if fmt == "json":
        content = result.model_dump_json(indent=2)
    else:
        content = _export_markdown(result)

    if output:
        output.write_text(content, encoding="utf-8")
        console.print(
            Panel(
                f"[green]Exported to [cyan]{output}[/]",
                border_style="dim green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
    else:
        console.print(content)


@app.command()
def version() -> None:
    """Show version and configuration info."""
    _print_splash()

    from assumption_zero.services.analysis_service import build_llm_adapter, build_research_providers

    adapter = build_llm_adapter()
    providers = build_research_providers()

    table = Table(box=box.SIMPLE, show_header=False, show_edge=False, padding=(0, 2))
    table.add_column(style="dim", width=24)
    table.add_column(style="cyan")

    table.add_row("Version", f"[bold white]{__version__}[/]")
    table.add_row("AI Provider", adapter.model_id)
    table.add_row(
        "Research Providers",
        ", ".join(p.name for p in providers) or "none configured",
    )
    table.add_row("Repository", "github.com/ramizz1/assumption-zero")
    table.add_row("License", "MIT")

    console.print(table)


if __name__ == "__main__":
    app()
