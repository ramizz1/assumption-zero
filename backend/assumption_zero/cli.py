"""
╔═══════════════════════════════════════════╗
║   A Z E R O  —  A S S U M P T I O N  0   ║
║   The open-source MVP validation engine   ║
╚═══════════════════════════════════════════╝
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
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

# ── Theme ─────────────────────────────────────────────────────────────────────
THEME = Theme(
    {
        "a0.accent":  "bold #F5A623",       # amber — primary brand
        "a0.muted":   "#C8C8C8",            # light — for secondary text
        "a0.good":    "bold #4CAF50",       # green
        "a0.warn":    "bold #FFC107",       # yellow/amber
        "a0.bad":     "bold #F44336",       # red
        "a0.info":    "bold #64B5F6",       # blue
        "a0.label":   "bold white",         # primary labels
        "a0.section": "bold #F5A623",       # section headers — amber
        "a0.market":  "bold #64B5F6",       # market analyst — blue
        "a0.skeptic": "bold #EF9A9A",       # skeptic — salmon
        "a0.builder": "bold #A5D6A7",       # builder — green
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


# ── Helpers ───────────────────────────────────────────────────────────────────


def _score_color(score: float) -> str:
    if score >= 65:
        return "a0.good"
    if score >= 45:
        return "a0.warn"
    return "a0.bad"


def _score_bar(score: float, width: int = 30) -> str:
    filled = int(score / 100 * width)
    col = _score_color(score)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{col}]{bar}[/] [{col}]{score:.0f}/100[/]"


def _rec_color(rec: str) -> str:
    return {
        "Build": "a0.good",
        "Test First": "a0.warn",
        "Pivot": "bold #FF8C00",
        "Avoid": "a0.bad",
    }.get(rec, "white")


def _conf_color(conf: str) -> str:
    return {"high": "a0.good", "medium": "a0.warn", "low": "a0.bad"}.get(conf.lower(), "white")


def _perspective_color(name: str) -> str:
    return {
        "market_analyst": "a0.market",
        "skeptical_investor": "a0.skeptic",
        "practical_builder": "a0.builder",
    }.get(name, "white")


def _perspective_icon(name: str) -> str:
    return {
        "market_analyst": "📊",
        "skeptical_investor": "🔍",
        "practical_builder": "🔨",
    }.get(name, "◆")


# ── Layout helpers ────────────────────────────────────────────────────────────


def _print_splash() -> None:
    console.print()
    console.print(
        Panel(
            Align.center(
                Text.from_markup(
                    f"[a0.accent]ASSUMPTION ZERO[/]  [a0.muted]v{__version__}[/]\n"
                    f"[a0.muted]{TAGLINE}[/]\n\n"
                    f"[a0.muted]Open-source  ·  Beta AI built-in  ·  No signup required[/]"
                ),
            ),
            border_style="#F5A623",
            padding=(1, 4),
            subtitle="[a0.muted]github.com/ramizz1/assumption-zero[/]",
        )
    )
    console.print()


def _print_section(title: str, icon: str = "◆") -> None:
    console.print()
    console.print(Rule(f"[a0.section] {icon}  {title} [/]", style="#F5A623"))
    console.print()


def _print_disclaimer() -> None:
    console.print()
    console.print(
        Panel(
            f"[a0.muted]{DISCLAIMER}[/]",
            border_style="#F5A623",
            padding=(0, 2),
        )
    )
    console.print()


# ── Engine runner ─────────────────────────────────────────────────────────────


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
    "clarifying_idea":              ("Clarifying idea", "🧠"),
    "generating_queries":           ("Building research plan", "📋"),
    "collecting_evidence":          ("Collecting evidence from real sources", "🔎"),
    "running_market_analyst":       ("Market analyst perspective", "📊"),
    "running_skeptical_investor":   ("Skeptical investor perspective", "🔍"),
    "running_practical_builder":    ("Practical builder perspective", "🔨"),
    "calculating_score":            ("Calculating opportunity score", "⚡"),
    "generating_experiments":       ("Designing validation experiments", "🧪"),
    "complete":                     ("Analysis complete", "✓"),
}


def _run_analysis_sync(idea, is_demo: bool = False):
    import uuid
    engine = _build_engine_sync()
    analysis_id = str(uuid.uuid4())
    current_label = ["⏳  Starting…"]

    async def _run():
        async def on_progress(stage, desc):
            label, icon = STAGE_LABELS.get(stage.value, (desc, "•"))
            current_label[0] = f"{icon}  {label}…"

        with Progress(
            SpinnerColumn(spinner_name="dots", style="a0.accent"),
            TextColumn("[a0.accent]{task.description}"),
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


# ── Report renderer ───────────────────────────────────────────────────────────


def _print_report(result) -> None:
    from assumption_zero.schemas import AnalysisStatus

    if result.status == AnalysisStatus.FAILED:
        err_console.print(f"Analysis failed: {result.error_message}")
        return

    score = result.opportunity_score
    conf = result.evidence_confidence
    rec = result.recommendation

    score_val = score.total if score else 0.0
    score_col = _score_color(score_val)
    rec_str = rec.value if rec else "Unknown"
    conf_str = conf.value.upper() if conf else "UNKNOWN"
    conf_col = _conf_color(conf.value if conf else "low")

    # ── 1. Executive Verdict ──────────────────────────────────────
    _print_section("Executive Verdict", "◈")

    body = Text()
    body.append(f"  {_score_bar(score_val)}\n\n")
    body.append("  Recommendation     ", style="a0.label")
    body.append(f"{rec_str}\n", style=_rec_color(rec_str))
    body.append("  Evidence Confidence  ", style="a0.label")
    body.append(f"{conf_str}\n", style=conf_col)

    if result.most_dangerous_assumption:
        body.append("\n  ⚠  Most Dangerous Assumption\n", style="a0.warn")
        body.append(f"  {result.most_dangerous_assumption}\n", style="white")

    console.print(
        Panel(
            body,
            title=f"[{score_col}]● {result.idea_input.name}[/]",
            border_style="yellow",
            padding=(0, 1),
        )
    )

    # ── 2. Score Breakdown ────────────────────────────────────────
    if score and score.dimensions:
        _print_section("Opportunity Score Breakdown", "◈")

        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="a0.section",
            padding=(0, 1),
            show_edge=False,
        )
        table.add_column("Dimension", min_width=30, style="white")
        table.add_column("Score", justify="right", width=8)
        table.add_column("Bar", width=22)
        table.add_column("Weight", justify="right", width=7, style="a0.muted")
        table.add_column("Conf", width=8)

        for dim in score.dimensions:
            col = _score_color(dim.raw_score)
            bar_filled = int(dim.raw_score / 100 * 16)
            mini_bar = "█" * bar_filled + "░" * (16 - bar_filled)
            table.add_row(
                dim.display_name,
                f"[{col}]{dim.raw_score:.0f}[/]",
                f"[{col}]{mini_bar}[/]",
                f"{dim.weight}%",
                f"[{_conf_color(dim.confidence.value)}]{dim.confidence.value[0].upper()}[/]",
            )

        table.add_section()
        table.add_row(
            "[a0.label]Total[/]",
            f"[{score_col} bold]{score_val:.0f}[/]",
            f"[{score_col}]{_score_bar(score_val, 16)}[/]",
            "[a0.muted]100%[/]",
            "",
        )
        console.print(table)

    # ── 3. Evidence ───────────────────────────────────────────────
    _print_section("Evidence Collected", "◈")

    ev_count = len(result.evidence)
    sources = sorted(set(e.source_name for e in result.evidence))
    console.print(
        f"  [a0.label]{ev_count} evidence items[/]  [white]from[/]  "
        f"[a0.info]{', '.join(sources)}[/]"
    )

    if result.provider_errors:
        console.print(f"\n  [a0.warn]⚠ {len(result.provider_errors)} provider issue(s):[/]")
        for err in result.provider_errors[:3]:
            console.print(f"  [white]  · {err[:110]}[/]")

    if result.strongest_supporting:
        console.print()
        console.print(
            Panel(
                f"[white]{result.strongest_supporting[:280]}[/]",
                title="[a0.good]✔  Strongest Supporting Evidence[/]",
                border_style="green",
                padding=(0, 2),
            )
        )
    if result.strongest_contradicting:
        console.print(
            Panel(
                f"[white]{result.strongest_contradicting[:280]}[/]",
                title="[a0.bad]✘  Strongest Contradicting Evidence[/]",
                border_style="red",
                padding=(0, 2),
            )
        )

    # ── 4. Competitors ────────────────────────────────────────────
    if result.competitors:
        _print_section(f"Competitors  ({len(result.competitors)} found)", "◈")

        comp_table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="a0.section",
            show_edge=False,
            padding=(0, 1),
        )
        comp_table.add_column("Name", min_width=20)
        comp_table.add_column("Type", width=12, style="a0.muted")
        comp_table.add_column("Description")

        for comp in result.competitors[:10]:
            desc = comp.description[:70] + "…" if len(comp.description) > 70 else comp.description
            comp_table.add_row(
                f"[a0.accent]{comp.name[:28]}[/]",
                comp.competitor_type.value,
                f"[white]{desc}[/]",
            )
        console.print(comp_table)

    # ── 5. AI Perspectives ────────────────────────────────────────
    _print_section("AI Perspectives", "◈")

    for p in result.perspectives:
        pcol = _perspective_color(p.perspective_name.value)
        icon = _perspective_icon(p.perspective_name.value)
        rec_c = _rec_color(p.recommendation.value)

        findings_text = ""
        if p.key_findings:
            findings_text = "\n[a0.label]Key Findings[/]\n" + "\n".join(
                f"  [a0.accent]→[/] [white]{f}[/]" for f in p.key_findings[:4]
            )
        risks_text = ""
        if p.risks:
            risks_text = "\n\n[a0.label]Risks[/]\n" + "\n".join(
                f"  [a0.bad]✗[/] [white]{r}[/]" for r in p.risks[:4]
            )
        opps_text = ""
        if p.opportunities:
            opps_text = "\n\n[a0.label]Opportunities[/]\n" + "\n".join(
                f"  [a0.good]✓[/] [white]{o}[/]" for o in p.opportunities[:3]
            )

        body = (
            f"[{rec_c}]▶  {p.recommendation.value}[/]  "
            f"[a0.muted]via {p.model_id}[/]\n\n"
            f"[white]{p.summary}[/]"
            f"{findings_text}{risks_text}{opps_text}"
        )

        border_color = "blue"
        if "skeptic" in p.perspective_name.value:
            border_color = "red"
        elif "builder" in p.perspective_name.value:
            border_color = "green"

        console.print(
            Panel(
                body,
                title=f"[{pcol}]{icon}  {p.perspective_display}[/]",
                border_style=border_color,
                padding=(1, 2),
            )
        )

    # ── 6. Disagreements ─────────────────────────────────────────
    if result.disagreements:
        _print_section(f"Model Disagreements  ({len(result.disagreements)})", "◈")
        for d in result.disagreements:
            console.print(f"  [a0.warn]↔[/] [a0.label]{d.topic}[/]")
            for pos in d.positions:
                console.print(f"    [a0.muted]{pos.perspective}:[/]  [white]{pos.position}[/]")
            console.print()

    # ── 7. Validation Experiments ─────────────────────────────────
    if result.experiments:
        _print_section(f"Validation Experiments  ({len(result.experiments)})", "◈")

        for i, exp in enumerate(result.experiments, 1):
            meta = (
                f"[a0.muted]Cost:[/] [a0.warn]{exp.estimated_cost_range}[/]   "
                f"[a0.muted]Time:[/] [a0.info]{exp.estimated_time}[/]"
            )
            body = (
                f"{meta}\n\n"
                f"[a0.label]Assumption tested[/]\n[white]{exp.assumption_tested}[/]\n\n"
                f"[a0.label]Why it matters[/]\n[white]{exp.why_it_matters}[/]\n\n"
                f"[a0.label]Procedure[/]\n[white]{exp.procedure}[/]\n\n"
                f"[a0.good]✓ Success if:[/] [white]{exp.success_threshold}[/]\n"
                f"[a0.bad]✗ Failure if:[/] [white]{exp.failure_threshold}[/]\n\n"
                f"[a0.muted]Ethics: {exp.legal_ethical}[/]"
            )
            console.print(
                Panel(
                    body,
                    title=f"[a0.info]Experiment {i} — {exp.title}[/]",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

    # ── 8. Missing Information ────────────────────────────────────
    if result.missing_information:
        _print_section("Missing Information", "◈")
        for m in result.missing_information:
            console.print(f"  [a0.warn]•[/]  [white]{m}[/]")

    # ── 9. Sources ────────────────────────────────────────────────
    if result.evidence:
        _print_section(f"Sources  ({len(result.evidence)})", "◈")
        for e in result.evidence[:12]:
            console.print(
                f"  [a0.muted][{e.evidence_id}][/]  "
                f"[a0.info]{e.title[:65]}[/]\n"
                f"           [white]{e.url[:80]}[/]"
            )
        if len(result.evidence) > 12:
            console.print(f"  [a0.muted]  … and {len(result.evidence) - 12} more[/]")

    _print_disclaimer()


# ── Export ────────────────────────────────────────────────────────────────────


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


# ── Interactive idea form ─────────────────────────────────────────────────────


def _ask_idea():
    from assumption_zero.schemas import IdeaInput

    console.print()
    console.print(
        Panel(
            "[a0.accent]💡 How to get 100% accurate validation results:[/]\n\n"
            "1. [bold white]Be Specific:[/] Mention your target audience (e.g. 'solo law firms in Azerbaijan').\n"
            "2. [bold white]Explain the Pain:[/] Describe why customers struggle without your solution.\n"
            "3. [bold white]List Competitors:[/] Name existing local or global tools (e.g. 'tap.az, lalafo').\n"
            "4. [bold white]Specify Budget & Model:[/] State pricing model and available capital.\n\n"
            "[a0.muted]Press Enter to skip optional fields.[/]",
            border_style="#F5A623",
            padding=(1, 2),
            title="[bold #F5A623]Step-by-Step Idea Definition Guide[/]",
        )
    )
    console.print()

    def ask(label: str, hint: str = "", required: bool = False) -> str:
        suffix = " [a0.bad](required)[/]" if required else " [a0.muted](optional)[/]"
        hint_str = f" [a0.muted]e.g. {hint}[/]" if hint else ""
        while True:
            val = Prompt.ask(
                f"  [a0.accent]›[/] [a0.label]{label}[/]{suffix}{hint_str}",
                default="",
                console=console,
            ).strip()
            if required and not val:
                console.print("  [a0.bad]  ✗ This field is required.[/]")
                continue
            return val

    name = ask("Idea / product name", "LegalMind Local", required=True)
    description = ask("Short description", "On-device AI legal meeting summarizer for small law firms", required=True)

    _print_section("The Problem", "🔎")
    problem = ask("Problem being solved", "Attorneys lose 10+ hours/week summarizing client meetings due to cloud data privacy compliance", required=True)
    customer = ask("Target customer", "Solo practitioners and small law firms (1-20 attorneys)", required=True)
    geography = ask("Target geography", "United States", required=True)

    import os
    if os.getenv("OPENROUTER_API_KEY"):
        console.print("  [a0.good]✓ Using OpenRouter API key from environment[/]\n")
    else:
        _print_section("AI Key Setup", "🔑")
        console.print(
            "  [a0.muted]Get a free OpenRouter key at:[/] [a0.info]https://openrouter.ai/keys[/]\n"
            "  [a0.muted]Press Enter to use built-in Assumption Zero Beta key.[/]\n"
        )
        user_key = ask("OpenRouter API Key", "sk-or-v1-...")
        if user_key:
            os.environ["OPENROUTER_API_KEY"] = user_key
            console.print("  [a0.good]✓ Using custom OpenRouter API key[/]\n")

    _print_section("Business Details", "📋")
    model = ask("Business model", "SaaS subscription per seat")
    price = ask("Expected price", "$49/month per attorney seat")
    skills = ask("Founder skills", "Full-stack developer (Python + React)")
    budget = ask("Available budget / runway", "$15,000 for 6 months")
    competitors = ask("Known competitors", "Otter.ai, Fireflies.ai")

    _print_section("Strategic Insights", "⚡")
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
    """Show the comprehensive guide for formulating startup ideas."""
    _print_splash()
    _print_section("Step-by-Step Idea Formulation Guide", "💡")

    guide_text = (
        "[a0.accent]To get 100% accurate scores and actionable insights from Assumption Zero:[/\n\n"
        "[bold white]1. Precise Problem Definition[/]\n"
        "   State exactly who suffers, what fails today, and the financial/time cost of inaction.\n"
        "   [a0.muted]Good:[/] 'Solo law firms lose 10+ hours/week manually summarizing client meetings due to cloud privacy compliance.'\n"
        "   [a0.muted]Bad:[/] 'Making it easier for buyers and sellers.'\n\n"
        "[bold white]2. Specific Target Customer & Location[/]\n"
        "   Identify exact demographics, region, and segment.\n"
        "   [a0.muted]Good:[/] 'Solo law practice attorneys in the US with 1-20 employees.'\n\n"
        "[bold white]3. Real Competitors & Existing Alternatives[/]\n"
        "   List direct competitors (e.g. Otter.ai, Fireflies.ai) and indirect alternatives (Excel, WhatsApp).\n\n"
        "[bold white]4. Realistic Budget & Founder Skills[/]\n"
        "   State your technical skills and runway so the AI can evaluate Founder/Project Fit accurately.\n"
    )
    console.print(Panel(guide_text, border_style="#F5A623", padding=(1, 2)))


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

    Interactive mode (default): answer the prompts.
    1-Prompt mode: pass --prompt "your freeform idea text"
    File mode: pass --file path/to/idea.json
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
                f"[a0.muted]Loaded from[/] [a0.info]{file}[/]\n"
                f"[a0.label]  Idea:[/] [a0.accent]{idea.name}[/]"
            )
        except Exception as exc:
            err_console.print(f"Invalid idea file: {exc}")
            raise typer.Exit(1)
    elif prompt:
        console.print("[a0.muted]Parsing freeform 1-prompt using AI...[/]")
        from assumption_zero.services.analysis_service import build_llm_adapter
        llm = build_llm_adapter()
        idea = asyncio.run(llm.parse_raw_prompt(prompt))
        console.print(f"[a0.good]✓ Extracted Idea:[/] [a0.accent]{idea.name}[/]")
    else:
        _print_section("Tell me about your idea", "💡")
        idea = _ask_idea()

    console.print()
    console.print(
        Panel(
            f"[a0.label]Idea:[/]  [a0.accent]{idea.name}[/]\n"
            f"[white]{idea.description}[/]\n\n"
            f"[a0.muted]Running research across GitHub, Hacker News, Wikipedia, Reddit…[/]\n"
            f"[a0.muted]This usually takes 30–90 seconds.[/]",
            border_style="#F5A623",
            padding=(0, 2),
        )
    )
    console.print()
    result = _run_analysis_sync(idea)
    _print_report(result)


@app.command()
def prompt(
    text: Optional[str] = typer.Argument(None, help="Single natural language text prompt describing your startup idea")
) -> None:
    """Analyze a startup idea from a single freeform text prompt."""
    if not text:
        _print_splash()
        _print_section("1-Prompt Quick Mode", "⚡")
        console.print(
            "  [a0.muted]Describe your startup idea in plain English (product name, problem, customer, pricing, budget, etc.):[/]\n"
        )
        text = Prompt.ask("  [a0.accent]›[/] [a0.label]Startup Idea Prompt[/]", console=console).strip()
        if not text:
            console.print("  [a0.bad]✗ Prompt cannot be empty.[/]")
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
                "Run [a0.accent]azero analyze[/] to analyse your first idea,\n"
                "or [a0.accent]azero guide[/] to view idea formatting tips.",
                border_style="#F5A623",
                padding=(0, 2),
            )
        )
        return

    table = Table(
        title="[a0.section]Saved Analyses[/]",
        box=box.SIMPLE,
        show_header=True,
        header_style="a0.section",
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("#", width=4, style="a0.accent")
    table.add_column("ID", width=10, style="a0.muted")
    table.add_column("Idea", min_width=24)
    table.add_column("Status", width=10)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Verdict", width=13)
    table.add_column("Created", width=17, style="a0.muted")

    for i, item in enumerate(items, 1):
        status_col = "a0.good" if item.status.value == "complete" else "a0.warn"
        score_str = (
            f"[{_score_color(item.opportunity_score)}]{item.opportunity_score:.0f}[/]"
            if item.opportunity_score is not None
            else "[a0.muted]—[/]"
        )
        rec_str = (
            f"[{_rec_color(item.recommendation.value)}]{item.recommendation.value}[/]"
            if item.recommendation
            else "[a0.muted]—[/]"
        )
        created = item.created_at.strftime("%b %d %H:%M") if item.created_at else "—"
        table.add_row(
            f"#{i}",
            item.analysis_id[:8],
            f"[a0.accent]{item.idea_name[:26]}[/]",
            f"[{status_col}]{item.status.value}[/]",
            score_str,
            rec_str,
            created,
        )

    console.print(table)
    console.print(
        f"\n[a0.muted]  Use [/][a0.accent]azero show 1[/][a0.muted] or [/][a0.accent]azero show {items[0].analysis_id[:8]}[/][a0.muted] to view report.[/]"
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
        console.print(f"[a0.muted]Run [/][a0.accent]azero list[/][a0.muted] to see all saved analyses.[/]")
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
                f"[a0.good]✓[/] Exported to [a0.info]{output}[/]",
                border_style="green",
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
    table.add_column(style="a0.muted", width=24)
    table.add_column(style="a0.info")

    table.add_row("Version", f"[a0.accent]{__version__}[/]")
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
