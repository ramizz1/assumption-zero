"""
Assumption Zero CLI — MVP Validation Engine
Anthropic Claude-inspired warm aesthetic interface with HTML export.
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

# ── Claude Warm & Crisp Theme (Zero Grey Text) ──────────────────────────────
THEME = Theme(
    {
        "a0.accent":  "bold #D97706",       # Claude terracotta / warm amber
        "a0.muted":   "bright_white",       # high-contrast secondary text
        "a0.good":    "bold green",         # high score / positive
        "a0.warn":    "bold #D97706",       # warm amber warning status
        "a0.bad":     "bold red",           # low score / danger
        "a0.info":    "bold cyan",          # primary informational text
        "a0.label":   "bold white",         # primary labels
        "a0.section": "bold #D97706",       # section header accent
        "a0.market":  "bold cyan",          # market perspective
        "a0.skeptic": "bold magenta",       # skeptic perspective
        "a0.builder": "bold green",         # builder perspective
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
        return "bold green"
    if score >= 45:
        return "bold #F5A623"
    return "bold red"


def _score_bar(score: float, width: int = 18, show_ratio: bool = False) -> str:
    filled = max(0, min(width, int(score / 100 * width)))
    col = _score_color(score)
    bar_filled = "█" * filled
    bar_unfilled = "░" * (width - filled)
    ratio_str = f" [{col}]{score:.0f}/100[/]" if show_ratio else ""
    return f"[{col}]{bar_filled}[/][grey50]{bar_unfilled}[/]{ratio_str}"


def _rec_color(rec: str) -> str:
    return {
        "Build": "bold green",
        "Test First": "bold #F5A623",
        "Pivot": "bold #F5A623",
        "Avoid": "bold red",
    }.get(rec, "bold white")


def _status_color(status: str) -> str:
    return {
        "complete": "bold green",
        "running": "bold cyan",
        "pending": "bold #F5A623",
        "failed": "bold red",
    }.get(status.lower(), "bold white")


def _conf_color(conf: str) -> str:
    return {"high": "bold green", "medium": "bold #F5A623", "low": "bold red"}.get(conf.lower(), "bold white")


def _perspective_color(name: str) -> str:
    return {
        "market_analyst": "bold cyan",
        "skeptical_investor": "bold magenta",
        "practical_builder": "bold green",
    }.get(name, "bold white")


# ── Layout Helpers ────────────────────────────────────────────────────────────


def _print_splash() -> None:
    console.print()
    banner_text = (
        f"[bold #F5A623]✦ A S S U M P T I O N   Z E R O[/]   [bold cyan]v{__version__}[/]\n"
        f"[bold white]{TAGLINE}[/]\n\n"
        f"[bold cyan]Multi-Source Live Research[/]  [bright_white]•[/]  [bold green]3 AI Perspectives[/]  [bright_white]•[/]  [bold #F5A623]Deterministic Scoring[/]\n"
        f"[bright_white]GitHub:[/] [bold cyan]https://github.com/ramizz1/assumption-zero[/]"
    )
    console.print(
        Panel(
            banner_text,
            border_style="#F5A623",
            box=box.ROUNDED,
            padding=(1, 3),
        )
    )
    console.print()


def _print_section(title: str, icon: str = "◈") -> None:
    console.print()
    console.print(Rule(f"[bold #F5A623]{icon}  {title}  {icon}[/]", style="#F5A623"))
    console.print()


def _print_disclaimer() -> None:
    console.print()
    console.print(
        Panel(
            f"[bright_white]{DISCLAIMER}[/]",
            border_style="#D97706",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )
    console.print()


# ── Engine Runner ─────────────────────────────────────────────────────────────


def _build_engine_sync(
    provider_override=None, api_key_override=None,
    model_override=None, base_url_override=None,
):
    from assumption_zero.analysis.engine import AnalysisEngine
    from assumption_zero.services.analysis_service import (
        build_llm_adapter,
        build_research_providers,
    )
    llm = build_llm_adapter(
        provider_override=provider_override,
        api_key_override=api_key_override,
        model_override=model_override,
        base_url_override=base_url_override,
    )
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


def _run_analysis_sync(
    idea,
    is_demo: bool = False,
    provider_override=None,
    api_key_override=None,
    model_override=None,
    base_url_override=None,
):
    import uuid
    engine = _build_engine_sync(
        provider_override=provider_override,
        api_key_override=api_key_override,
        model_override=model_override,
        base_url_override=base_url_override,
    )
    analysis_id = str(uuid.uuid4())
    current_label = ["Starting engine..."]

    async def _run():
        async def on_progress(stage, desc):
            label, step = STAGE_LABELS.get(stage.value, (desc, "•"))
            current_label[0] = f"[{step}] {label}..."

        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold #D97706"),
            TextColumn("[bold #D97706]{task.description}"),
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


def _clean_summary(text: str) -> str:
    """Format summary for terminal rendering, cleaning broken markdown tables into clean bullet points."""
    if not text:
        return ""
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and ("---" in stripped or "|-" in stripped):
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if cells:
                clean_lines.append("  • " + " — ".join(cells))
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


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
            title=f"[bold #D97706]{result.idea_input.name}[/]",
            border_style="#D97706",
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
            header_style="bold #F5A623",
            padding=(0, 1),
            show_edge=False,
        )
        table.add_column("Dimension", min_width=30, style="bold white")
        table.add_column("Score", justify="right", width=8)
        table.add_column("Bar", width=24)
        table.add_column("Weight", justify="right", width=7, style="bright_white")
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
            "[bold white]Total[/]",
            f"[{_score_color(score_val)} bold]{score_val:.0f}[/]",
            _score_bar(score_val, 14, show_ratio=True),
            "[bright_white]100%[/]",
            "",
        )
        console.print(table)

    # ── 3. Evidence ───────────────────────────────────────────────
    _print_section("Evidence Collected")

    ev_count = len(result.evidence)
    sources = sorted(set(e.source_name for e in result.evidence))
    console.print(
        f"  [bold white]{ev_count} evidence items[/]  [bright_white]collected from[/]  "
        f"[bold cyan]{', '.join(sources)}[/]"
    )

    if result.provider_errors:
        console.print(f"\n  [bold #D97706][WARNING] {len(result.provider_errors)} provider issue(s):[/]")
        for err in result.provider_errors[:3]:
            console.print(f"    - [bright_white]{err[:110]}[/]")

    if result.strongest_supporting:
        console.print()
        console.print(
            Panel(
                f"[white]{result.strongest_supporting[:280]}[/]",
                title="[bold green]Strongest Supporting Evidence[/]",
                border_style="green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
    if result.strongest_contradicting:
        console.print(
            Panel(
                f"[white]{result.strongest_contradicting[:280]}[/]",
                title="[bold red]Strongest Contradicting Evidence[/]",
                border_style="red",
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
            header_style="bold #D97706",
            show_edge=False,
            padding=(0, 1),
        )
        comp_table.add_column("Name", min_width=20, style="bold white")
        comp_table.add_column("Type", width=14, style="bright_white")
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

        clean_sum = _clean_summary(p.summary)
        body_text = (
            f"  [bold white]Verdict:[/] [{rec_c}]{p.recommendation.value}[/]   [bright_white](Model: {p.model_id})[/]\n\n"
            f"  [white]{clean_sum}[/]"
            f"{findings_text}"
            f"{risks_text}"
            f"{opps_text}"
        )

        console.print(
            Panel(
                body_text,
                title=f"[{pcol}]{p.perspective_display.upper()}[/]",
                border_style="#D97706",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

    # ── 6. Disagreements ─────────────────────────────────────────
    if result.disagreements:
        _print_section(f"Model Disagreements ({len(result.disagreements)})")
        for d in result.disagreements:
            console.print(f"  [bold #D97706][!][/] [bold white]{d.topic}[/]")
            for pos in d.positions:
                console.print(f"    - [bright_white]{pos.perspective}:[/] [white]{pos.position}[/]")
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
            meta = f"[bright_white]Est. Cost:[/] [bold #D97706]{exp.estimated_cost_range}[/]   |   [bright_white]Est. Time:[/] [bold cyan]{exp.estimated_time}[/]"
            body = (
                f"{meta}\n\n"
                f"  [bold white]Assumption Tested:[/]  [white]{exp.assumption_tested}[/]\n"
                f"  [bold white]Why It Matters:[/]     [white]{exp.why_it_matters}[/]\n"
                f"  [bold white]Procedure:[/]         [white]{exp.procedure}[/]\n\n"
                f"  [bold green]Success Criteria:[/]  [white]{exp.success_threshold}[/]\n"
                f"  [bold red]Failure Criteria:[/]  [white]{exp.failure_threshold}[/]\n\n"
                f"  [bright_white]Ethics / Compliance: {exp.legal_ethical}[/]"
            )
            console.print(
                Panel(
                    body,
                    title=f"[bold #D97706]Experiment {i} — {exp.title}[/]",
                    border_style="#D97706",
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

    # Auto-generate report.html in local directory for user
    try:
        html_content = _export_html(result)
        report_path = Path("report.html")
        report_path.write_text(html_content, encoding="utf-8")
        console.print(f"  [bold green]✓ Standalone HTML Report generated:[/] [bold cyan]{report_path.resolve()}[/]\n")
    except Exception:
        pass


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


# ── Export HTML (Claude Anthropic Styled) ──────────────────────────────────────


def _export_html(result) -> str:
    score = result.opportunity_score
    score_val = score.total if score else 0.0
    rec_val = result.recommendation.value if result.recommendation else "Unknown"
    conf_val = result.evidence_confidence.value.upper() if result.evidence_confidence else "UNKNOWN"

    score_color = "#10B981" if score_val >= 65 else "#D97706" if score_val >= 45 else "#EF4444"
    rec_bg = "#10B98122" if rec_val == "Build" else "#D9770622" if rec_val in ("Test First", "Pivot") else "#EF444422"
    rec_color = "#10B981" if rec_val == "Build" else "#D97706" if rec_val in ("Test First", "Pivot") else "#EF4444"

    conf_bg = "#10B98122" if conf_val == "HIGH" else "#D9770622" if conf_val == "MEDIUM" else "#EF444422"
    conf_color = "#10B981" if conf_val == "HIGH" else "#D97706" if conf_val == "MEDIUM" else "#EF4444"

    # Score breakdown rows
    score_rows = ""
    if score and score.dimensions:
        for dim in score.dimensions:
            dim_col = "#10B981" if dim.raw_score >= 65 else "#D97706" if dim.raw_score >= 45 else "#EF4444"
            dim_conf = dim.confidence.value.upper()
            dim_conf_col = "#10B981" if dim_conf == "HIGH" else "#D97706" if dim_conf == "MEDIUM" else "#EF4444"
            score_rows += f"""
            <tr>
                <td><strong>{dim.display_name}</strong></td>
                <td style="text-align: right; color: {dim_col}; font-weight: bold;">{dim.raw_score:.0f} / 100</td>
                <td>
                    <div class="progress-bg">
                        <div class="progress-bar" style="width: {dim.raw_score}%; background: {dim_col};"></div>
                    </div>
                </td>
                <td style="text-align: right;">{dim.weight}%</td>
                <td style="text-align: center;"><span class="badge" style="background: {dim_conf_col}22; color: {dim_conf_col};">{dim_conf}</span></td>
            </tr>
            """

    # Competitors
    comp_html = ""
    if result.competitors:
        for c in result.competitors:
            comp_html += f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">{c.name}</span>
                    <span class="badge" style="background: #3B82F622; color: #60A5FA;">{c.competitor_type.value}</span>
                </div>
                <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 0.5rem;">{c.description}</p>
            </div>
            """

    # AI Perspectives
    persp_html = ""
    for p in result.perspectives:
        p_col = "#38BDF8" if "market" in p.perspective_name.value else "#E879F9" if "skeptick" in p.perspective_name.value or "investor" in p.perspective_name.value else "#4ADE80"
        p_rec_col = "#10B981" if p.recommendation.value == "Build" else "#D97706" if p.recommendation.value in ("Test First", "Pivot") else "#EF4444"

        findings_li = "".join(f"<li>{f.strip('§')}</li>" for f in p.key_findings if not (f.startswith("§") and f.endswith("§")))
        risks_li = "".join(f"<li>{r}</li>" for r in p.risks)
        opps_li = "".join(f"<li>{o}</li>" for o in p.opportunities)

        persp_html += f"""
        <div class="card" style="border-top: 4px solid {p_col};">
            <div class="card-header">
                <span class="card-title" style="color: {p_col};">{p.perspective_display.upper()}</span>
                <div>
                    <span class="badge" style="background: {p_rec_col}22; color: {p_rec_col};">Verdict: {p.recommendation.value}</span>
                    <span class="badge" style="background: #1E293B; color: #94A3B8;">Model: {p.model_id}</span>
                </div>
            </div>
            <p style="margin-top: 1rem; font-size: 1rem; line-height: 1.6;">{p.summary}</p>

            {"<div style='margin-top: 1rem;'><strong style='color: #60A5FA;'>Key Findings:</strong><ul>" + findings_li + "</ul></div>" if findings_li else ""}
            {"<div style='margin-top: 1rem;'><strong style='color: #F87171;'>Identified Risks:</strong><ul>" + risks_li + "</ul></div>" if risks_li else ""}
            {"<div style='margin-top: 1rem;'><strong style='color: #4ADE80;'>Strategic Opportunities:</strong><ul>" + opps_li + "</ul></div>" if opps_li else ""}
        </div>
        """

    # Validation Experiments
    exp_html = ""
    if result.experiments:
        for i, exp in enumerate(result.experiments, 1):
            exp_html += f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title" style="color: #D97706;">Experiment {i}: {exp.title}</span>
                    <div>
                        <span class="badge" style="background: #D9770622; color: #D97706;">Cost: {exp.estimated_cost_range}</span>
                        <span class="badge" style="background: #38BDF822; color: #38BDF8;">Time: {exp.estimated_time}</span>
                    </div>
                </div>
                <div style="margin-top: 1rem; display: grid; gap: 0.75rem;">
                    <div><strong style="color: #F8FAFC;">Assumption Tested:</strong> <span style="color: #CBD5E1;">{exp.assumption_tested}</span></div>
                    <div><strong style="color: #F8FAFC;">Why It Matters:</strong> <span style="color: #CBD5E1;">{exp.why_it_matters}</span></div>
                    <div><strong style="color: #F8FAFC;">Procedure:</strong> <span style="color: #CBD5E1;">{exp.procedure}</span></div>
                    <div style="background: #064E3B44; padding: 0.75rem; border-radius: 6px; border-left: 3px solid #10B981;">
                        <strong style="color: #34D399;">Success Threshold:</strong> {exp.success_threshold}
                    </div>
                    <div style="background: #7F1D1D44; padding: 0.75rem; border-radius: 6px; border-left: 3px solid #EF4444;">
                        <strong style="color: #F87171;">Failure Threshold:</strong> {exp.failure_threshold}
                    </div>
                </div>
            </div>
            """

    # Next steps
    next_steps_html = ""
    next_steps = [
        "Conduct 5 discovery interviews with target segment customers before writing code.",
        "Create a lean landing page to measure conversion interest and sign-up intent.",
        "Manually deliver core value to 3 early users to validate willingness to pay.",
        "Allocate a 1-week budget ($0-$200) to test riskiest distribution channel.",
        "Define primary success metric (retention, revenue, NPS) and measure from Day 1.",
    ]
    for idx, st in enumerate(next_steps, 1):
        next_steps_html += f"""
        <div class="card" style="display: flex; gap: 1rem; align-items: center;">
            <div style="background: #D97706; color: #FFF; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">{idx}</div>
            <div style="color: #F8FAFC; font-size: 1rem;">{st}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assumption Zero — {result.idea_input.name} Validation Report</title>
    <style>
        :root {{
            --bg-color: #0F172A;
            --card-bg: #1E293B;
            --accent-color: #D97706;
            --text-main: #F8FAFC;
            --text-sub: #94A3B8;
            --border-color: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        .logo {{
            color: var(--accent-color);
            font-size: 0.9rem;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        h1 {{
            font-size: 2.2rem;
            margin: 0.5rem 0;
            color: #FFF;
        }}
        .tagline {{
            color: var(--text-sub);
            font-size: 1.05rem;
        }}
        .disclaimer-box {{
            background: #D9770615;
            border-left: 4px solid var(--accent-color);
            padding: 1rem 1.25rem;
            border-radius: 6px;
            margin-bottom: 2rem;
            color: #CBD5E1;
            font-size: 0.95rem;
        }}
        .section-title {{
            font-size: 1.4rem;
            color: var(--accent-color);
            margin: 2.5rem 0 1rem 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .verdict-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        .score-display {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .score-number {{
            font-size: 3.5rem;
            font-weight: 800;
            color: {score_color};
            line-height: 1;
        }}
        .progress-bg {{
            background: #334155;
            height: 14px;
            border-radius: 7px;
            overflow: hidden;
            flex-grow: 1;
        }}
        .progress-bar {{
            height: 100%;
            border-radius: 7px;
            transition: width 0.4s ease;
        }}
        .badge {{
            display: inline-block;
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}
        .card-title {{
            font-size: 1.15rem;
            font-weight: 700;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            background: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 0.9rem 1.25rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: #0F172A;
            color: var(--accent-color);
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}
        ul {{
            margin-left: 1.25rem;
            margin-top: 0.5rem;
            color: #CBD5E1;
        }}
        li {{
            margin-bottom: 0.35rem;
        }}
        footer {{
            margin-top: 4rem;
            text-align: center;
            color: var(--text-sub);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            padding-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">✦ Assumption Zero — MVP Validation Engine</div>
            <h1>{result.idea_input.name}</h1>
            <div class="tagline">{result.idea_input.description}</div>
        </header>

        <div class="disclaimer-box">
            <strong>Decision Support Notice:</strong> {DISCLAIMER}
        </div>

        <div class="section-title">Executive Verdict</div>
        <div class="verdict-card">
            <div class="score-display">
                <div class="score-number">{score_val:.0f}</div>
                <div style="flex-grow: 1;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-weight: bold; color: var(--text-main);">Opportunity Score</span>
                        <span style="color: {score_color}; font-weight: bold;">{score_val:.0f} / 100</span>
                    </div>
                    <div class="progress-bg">
                        <div class="progress-bar" style="width: {score_val}%; background: {score_color};"></div>
                    </div>
                </div>
            </div>
            <div style="margin-bottom: 1rem;">
                <span class="badge" style="background: {rec_bg}; color: {rec_color}; font-size: 1rem;">Recommendation: {rec_val}</span>
                <span class="badge" style="background: {conf_bg}; color: {conf_color}; font-size: 1rem;">Evidence Confidence: {conf_val}</span>
            </div>
            {"<div style='margin-top: 1.25rem; padding: 1rem; background: #7F1D1D33; border-left: 4px solid #EF4444; border-radius: 6px;'><strong style='color: #F87171;'>Critical Assumption Risk:</strong> <span style='color: #F8FAFC;'>" + result.most_dangerous_assumption + "</span></div>" if result.most_dangerous_assumption else ""}
        </div>

        <div class="section-title">Opportunity Score Breakdown</div>
        <table>
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th style="text-align: right;">Score</th>
                    <th>Visual Bar</th>
                    <th style="text-align: right;">Weight</th>
                    <th style="text-align: center;">Confidence</th>
                </tr>
            </thead>
            <tbody>
                {score_rows}
            </tbody>
        </table>

        <div class="section-title">AI Strategic Perspectives</div>
        {persp_html}

        {"<div class='section-title'>Identified Competitors</div><div class='grid'>" + comp_html + "</div>" if comp_html else ""}

        <div class="section-title">Actionable Next Steps</div>
        <div style="display: grid; gap: 0.75rem; margin-bottom: 2rem;">
            {next_steps_html}
        </div>

        {"<div class='section-title'>Validation Experiments</div>" + exp_html if exp_html else ""}

        <footer>
            Generated by Assumption Zero v{__version__} &bull; Open-Source MVP Validation Engine
        </footer>
    </div>
</body>
</html>
"""
    return html


# ── Interactive Form ──────────────────────────────────────────────────────────


def _ask_idea():
    from assumption_zero.schemas import IdeaInput

    console.print()
    console.print("[bold #D97706]Step-by-Step Idea Definition[/]\n")

    def ask(label: str, hint: str = "", required: bool = False) -> str:
        suffix = " [bold red](required)[/]" if required else " [bright_white](optional)[/]"
        hint_str = f" [bright_white]e.g. {hint}[/]" if hint else ""
        while True:
            val = Prompt.ask(
                f"  [bold #D97706]›[/] [bold white]{label}[/]{suffix}{hint_str}",
                default="",
                console=console,
            ).strip()
            if required and not val:
                console.print("    [bold red]Error: This field is required.[/]")
                continue
            return val

    name = ask("Idea / product name", "LegalMind Local", required=True)
    description = ask("Short description", "On-device AI legal meeting summarizer for small law firms", required=True)

    _print_section("The Problem")
    problem = ask("Problem being solved", "Attorneys lose 10+ hours/week summarizing client meetings due to cloud data privacy compliance", required=True)
    customer = ask("Target customer", "Solo practitioners and small law firms (1-20 attorneys)", required=True)
    geography = ask("Target geography", "United States", required=True)

    from assumption_zero.config import get_settings
    _settings = get_settings()
    _has_openrouter = bool(_settings.openrouter_api_key)
    _has_groq = bool(_settings.groq_api_key)

    if _has_openrouter or _has_groq:
        _key_info = []
        if _has_openrouter:
            _key_info.append("[bold cyan]OpenRouter[/]")
        if _has_groq:
            _key_info.append("[bold green]Groq[/]")
        console.print(f"  [bold green]✓ API keys loaded from config:[/] {', '.join(_key_info)}\n")
    else:
        _print_section("AI Key Setup")
        console.print(
            "  [bright_white]Get a free OpenRouter key at:[/] [bold cyan]https://openrouter.ai/keys[/]\n"
            "  [bright_white]Press Enter to skip and use built-in Assumption Zero Beta key.[/]\n"
        )
        user_key = ask("OpenRouter API Key", "sk-or-v1-...")
        if user_key:
            import os
            os.environ["OPENROUTER_API_KEY"] = user_key
            console.print("  [bold green]Using custom OpenRouter API key[/]\n")
        else:
            console.print("  [bright_white]Continuing with built-in Beta key.[/]\n")

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
# AI Provider Selection (interactive)
# ─────────────────────────────────────────────────────────────────────────────

_PROVIDER_PRESETS = {
    "1": ("Built-in Beta AI (free, no key needed)",    "beta",        None,  None,                            None),
    "2": ("OpenAI ChatGPT (your key — gpt-4o-mini)",   "openai_compat", None, "gpt-4o-mini",                 "https://api.openai.com/v1"),
    "3": ("OpenAI ChatGPT (your key — gpt-4o)",        "openai_compat", None, "gpt-4o",                      "https://api.openai.com/v1"),
    "4": ("Groq — llama-3.3-70b (your key)",           "groq",        None,  "llama-3.3-70b-versatile",      None),
    "5": ("OpenRouter — 200+ models (your key)",        "openrouter",  None,  None,                            None),
    "6": ("Together AI (your key)",                     "openai_compat", None, "meta-llama/Llama-3.3-70B-Instruct-Turbo", "https://api.together.xyz/v1"),
    "7": ("DeepSeek (your key)",                        "openai_compat", None, "deepseek-chat",               "https://api.deepseek.com/v1"),
    "8": ("Custom / self-hosted (any OpenAI-spec API)", "openai_compat", None,  None,                          None),
}


def _ask_idea_with_key(
    provider_override=None,
    api_key_override=None,
    model_override=None,
    base_url_override=None,
):
    """Interactive idea wizard with AI provider selection.

    Returns: (IdeaInput, provider, api_key, model, base_url)
    """
    from assumption_zero.config import get_settings
    settings = get_settings()

    # Check what keys are already configured
    _has_openrouter = bool(settings.openrouter_api_key)
    _has_groq = bool(settings.groq_api_key)
    _has_compat = bool(settings.openai_compatible_api_key)
    _any_key = _has_openrouter or _has_groq or _has_compat

    # Collect the idea first
    idea = _ask_idea()

    # ── AI Provider Selection ─────────────────────────────────────────────────
    # If all overrides already supplied, skip
    if provider_override and api_key_override:
        return idea, provider_override, api_key_override, model_override, base_url_override

    _print_section("AI Provider")

    if _any_key and not provider_override:
        # Show detected keys and let user confirm or switch
        detected = []
        if _has_openrouter:
            detected.append("[bold cyan]OpenRouter[/]")
        if _has_groq:
            detected.append("[bold green]Groq[/]")
        if _has_compat:
            detected.append("[bold #F5A623]Custom OpenAI-compat[/]")
        console.print(f"  [bold green]✓ Keys detected in config:[/] {', '.join(detected)}")
        console.print("  [bright_white]Press Enter to use them, or type a number to switch provider.[/]\n")

        choice = Prompt.ask(
            "  [bold #D97706]›[/] [bold white]Use detected keys?[/] [bright_white](Enter = yes, 1-8 = switch)[/]",
            default="",
            console=console,
        ).strip()

        if not choice:
            # Use existing .env config
            return idea, provider_override, api_key_override, model_override, base_url_override
    else:
        if not _any_key:
            console.print("  [bold #D97706]No API keys found in config.[/] Choose an AI provider:\n")
        else:
            console.print("  [bright_white]Override AI provider:[/]\n")
        choice = ""

    # Show provider menu
    console.print("  [bold white]Available providers:[/]")
    for k, (label, *_) in _PROVIDER_PRESETS.items():
        bullet = "[bold cyan]\u25b8[/]" if k == "1" else "[bright_white]\u25b8[/]"
        console.print(f"    {bullet} [bold #D97706]{k}[/]  {label}")
    console.print()

    if not choice:
        choice = Prompt.ask(
            "  [bold #D97706]›[/] [bold white]Provider[/] [bright_white](1-8)[/]",
            default="1",
            console=console,
        ).strip()

    preset = _PROVIDER_PRESETS.get(choice)
    if not preset:
        console.print("  [bright_white]Invalid choice — using built-in Beta AI.[/]")
        preset = _PROVIDER_PRESETS["1"]

    label, prov, _, mdl, burl = preset

    # If preset requires a key (anything except option 1), ask for it
    needs_key = choice != "1"
    entered_key = api_key_override or ""

    if needs_key and not entered_key:
        console.print()
        if choice == "2" or choice == "3":
            console.print("  [bright_white]Get your OpenAI API key at:[/] [bold cyan]https://platform.openai.com/api-keys[/]")
        elif choice == "4":
            console.print("  [bright_white]Get your free Groq key at:[/] [bold cyan]https://console.groq.com/keys[/]")
        elif choice == "5":
            console.print("  [bright_white]Get your free OpenRouter key at:[/] [bold cyan]https://openrouter.ai/keys[/]")
        elif choice == "6":
            console.print("  [bright_white]Get your Together AI key at:[/] [bold cyan]https://api.together.xyz/settings/api-keys[/]")
        elif choice == "7":
            console.print("  [bright_white]Get your DeepSeek key at:[/] [bold cyan]https://platform.deepseek.com/api-keys[/]")
        else:
            console.print("  [bright_white]Enter your API key for this provider.[/]")

        entered_key = Prompt.ask(
            "  [bold #D97706]›[/] [bold white]API Key[/]",
            default="",
            password=True,
            console=console,
        ).strip()

        if not entered_key:
            console.print("  [bright_white]No key entered — falling back to built-in Beta AI.[/]\n")
            return idea, None, None, None, None

    # For custom provider, ask for model and base URL
    final_model = model_override or mdl
    final_base_url = base_url_override or burl

    if choice == "8":
        if not final_base_url:
            final_base_url = Prompt.ask(
                "  [bold #D97706]›[/] [bold white]Base URL[/] [bright_white](e.g. https://api.openai.com/v1)[/]",
                default="https://api.openai.com/v1",
                console=console,
            ).strip()
        if not final_model:
            final_model = Prompt.ask(
                "  [bold #D97706]›[/] [bold white]Model name[/] [bright_white](e.g. gpt-4o-mini, claude-3-haiku)[/]",
                default="gpt-4o-mini",
                console=console,
            ).strip()

    final_key = entered_key or api_key_override or None
    final_prov = prov if (choice != "1") else (provider_override or None)

    console.print(f"\n  [bold green]✓ Provider selected:[/] [bold cyan]{label}[/]")
    if final_model:
        console.print(f"  [bright_white]Model:[/] [bold white]{final_model}[/]")
    console.print()

    return idea, final_prov, final_key, final_model, final_base_url


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────


@app.command()
def guide() -> None:
    """Show the guide for formulating startup ideas."""
    _print_splash()
    _print_section("Idea Formulation Guide")

    guide_text = (
        "[bold white]To get actionable insights and realistic scores from Assumption Zero:[/\n\n"
        "[bold #D97706]1. Precise Problem Definition[/]\n"
        "   State who suffers, current broken alternatives, and financial or time cost.\n"
        "   [bright_white]Example: 'Solo law firms lose 10+ hours/week summarizing meetings due to privacy compliance.'[/]\n\n"
        "[bold #D97706]2. Target Customer & Geography[/]\n"
        "   Define specific demographics, size, and location.\n"
        "   [bright_white]Example: 'Solo law practice attorneys in the US with 1-20 employees.'[/]\n\n"
        "[bold #D97706]3. Competitors & Alternatives[/]\n"
        "   Include direct software tools (e.g. Otter.ai) and indirect solutions (Excel, WhatsApp).\n\n"
        "[bold #D97706]4. Budget & Founder Fit[/]\n"
        "   Specify developer skills and runway to evaluate technical & execution risk.\n"
    )
    console.print(Panel(guide_text, border_style="#D97706", box=box.ROUNDED, padding=(1, 2)))


@app.command()
def analyze(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to a JSON file or text prompt file with IdeaInput fields"
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p", help="Analyze from a single freeform text prompt"
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k",
        help="Custom API key (OpenAI, Groq, OpenRouter, or any OpenAI-compatible provider). Overrides .env.",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m",
        help="Model name to use (e.g. gpt-4o, gpt-4o-mini, claude-3-haiku, llama-3.3-70b-versatile). Overrides .env.",
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider",
        help="AI provider: openai, openrouter, groq, hybrid, or openai_compat. Overrides AI_PROVIDER in .env.",
    ),
    base_url: Optional[str] = typer.Option(
        None, "--base-url",
        help="Custom OpenAI-compatible base URL (e.g. https://api.together.xyz/v1). Used with --api-key.",
    ),
) -> None:
    """
    Analyse an MVP idea interactively, from a 1-prompt text, or from a JSON or text file.

    Examples:

      azero analyze                                          # interactive wizard

      azero analyze --prompt \"AI scheduling app for dentists\"

      azero analyze --api-key sk-... --model gpt-4o         # use your ChatGPT key

      azero analyze --api-key sk-... --model gpt-4o-mini --provider openai
    """
    _print_splash()

    try:
        # ── Build engine with any runtime key/model overrides ──────────────────
        _provider = provider
        _api_key = api_key
        _model = model
        _base_url = base_url

        # If --api-key given but no --provider, auto-detect from model name or default to openai
        if _api_key and not _provider:
            if _model and any(x in (_model or "") for x in ("groq", "llama", "mixtral")):
                _provider = "groq"
            elif _model and any(x in (_model or "") for x in ("gemma", "qwen")):
                _provider = "openrouter"
            else:
                _provider = "openai_compat"

        # If --provider openai and no base_url set, fill in the standard OpenAI URL
        if _provider in ("openai", "openai_compat") and not _base_url:
            _base_url = "https://api.openai.com/v1"

        if file:
            if not file.exists():
                err_console.print(f"File not found: {file}")
                raise typer.Exit(1)
            raw_content = file.read_text(encoding="utf-8").strip()
            try:
                data = json.loads(raw_content)
                from assumption_zero.schemas import IdeaInput
                idea = IdeaInput(**data)
                console.print(
                    f"[bright_white]Loaded from[/] [bold cyan]{file}[/]\n"
                    f"  [bold white]Idea:[/] [bold #D97706]{idea.name}[/]"
                )
            except Exception:
                # Fall back smoothly if the file is text/markdown instead of JSON!
                console.print(f"[bright_white]Loaded text prompt from[/] [bold cyan]{file}[/]")
                console.print("[bright_white]Parsing idea details with AI...[/]")
                from assumption_zero.services.analysis_service import build_llm_adapter
                llm = build_llm_adapter(
                    provider_override=_provider,
                    api_key_override=_api_key,
                    model_override=_model,
                    base_url_override=_base_url,
                )
                idea = asyncio.run(llm.parse_raw_prompt(raw_content))
                console.print(f"[bold green]Extracted Idea:[/] [bold #D97706]{idea.name}[/]")
        elif prompt:
            console.print("[bright_white]Parsing freeform prompt using AI...[/]")
            from assumption_zero.services.analysis_service import build_llm_adapter
            llm = build_llm_adapter(
                provider_override=_provider,
                api_key_override=_api_key,
                model_override=_model,
                base_url_override=_base_url,
            )
            idea = asyncio.run(llm.parse_raw_prompt(prompt))
            console.print(f"[bold green]Extracted Idea:[/] [bold #D97706]{idea.name}[/]")
        else:
            _print_section("Idea Definition")
            # Pass runtime overrides into interactive flow
            idea, _provider, _api_key, _model, _base_url = _ask_idea_with_key(
                provider_override=_provider,
                api_key_override=_api_key,
                model_override=_model,
                base_url_override=_base_url,
            )

        # Show what AI will be used
        if _api_key or _provider:
            _prov_label = _provider or "auto"
            _model_label = _model or "default"
            console.print(f"  [bold green]✓ Using provider:[/] [bold cyan]{_prov_label}[/]  model: [bold white]{_model_label}[/]\n")

        console.print()
        console.print(
            Panel(
                f"  [bold white]Idea:[/]  [bold #D97706]{idea.name}[/]\n"
                f"  [white]{idea.description}[/]\n\n"
                f"  [bright_white]Running analysis engine...[/]",
                border_style="#D97706",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()
        result = _run_analysis_sync(
            idea,
            provider_override=_provider,
            api_key_override=_api_key,
            model_override=_model,
            base_url_override=_base_url,
        )
        _print_report(result)
    except Exception as exc:
        msg = str(exc)
        if "gibberish" in msg.lower():
            err_console.print(f"\n[bold red]Error: The input text appears to be random characters or gibberish. Please enter a valid product or business idea.[/]\n")
        else:
            err_console.print(f"\n[bold red]Error: {msg}[/]\n")
        raise typer.Exit(1)


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
        console.print(f"[bright_white]Loaded prompt from[/] [bold cyan]{file}[/]")

    if not text:
        _print_splash()
        _print_section("Freeform Input Mode")
        console.print(
            "  [bright_white]Paste your startup idea prompt below.[/]\n"
            "  [bright_white]Type 'END' on a new line when finished, or pass a file: azero prompt -f my_idea.txt[/]\n"
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
            console.print("  [bold red]Error: Prompt cannot be empty.[/]")
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
                "Run [bold #D97706]azero analyze[/] to analyse your first idea,\n"
                "or [bold #D97706]azero guide[/] to view idea formatting tips.",
                border_style="#D97706",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
        return

    table = Table(
        title="Saved Analyses",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold #D97706",
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("#", width=4, style="bold cyan")
    table.add_column("ID", width=10, style="bright_white")
    table.add_column("Idea", min_width=24, style="bold white")
    table.add_column("Status", width=10)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Verdict", width=13)
    table.add_column("Created", width=17, style="bright_white")

    for i, item in enumerate(items, 1):
        status_col = "bold green" if item.status.value == "complete" else "bold #D97706"
        score_str = (
            f"[{_score_color(item.opportunity_score)}]{item.opportunity_score:.0f}[/]"
            if item.opportunity_score is not None
            else "[bright_white]—[/]"
        )
        rec_str = (
            f"[{_rec_color(item.recommendation.value)}]{item.recommendation.value}[/]"
            if item.recommendation
            else "[bright_white]—[/]"
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
        f"\n[bright_white]  Use [/][bold #D97706]azero show 1[/][bright_white] or [/][bold #D97706]azero show {items[0].analysis_id[:8]}[/][bright_white] to view report.[/]"
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
        console.print(f"[bright_white]Run [/][bold #D97706]azero list[/][bright_white] to see all saved analyses.[/]")
        raise typer.Exit(1)

    _print_report(result)


@app.command()
def export(
    analysis_id: Optional[str] = typer.Argument(
        None, help="Analysis ID, short ID, or index (1, 2, ...). Omit for latest."
    ),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown, json, or html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export an analysis as Markdown, JSON, or HTML."""
    _print_splash()
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
    elif fmt == "html":
        content = _export_html(result)
    else:
        content = _export_markdown(result)

    if output:
        output.write_text(content, encoding="utf-8")
        console.print(
            Panel(
                f"[bold green]Exported to [bold cyan]{output}[/]",
                border_style="green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
    else:
        console.print(content)


@app.command()
def delete(
    analysis_id: str = typer.Argument(..., help="Analysis ID, short ID, or index (1, 2, ...) to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Delete a saved analysis by ID or index."""
    _print_splash()
    import assumption_zero.storage as store

    full_id = store.resolve_id(analysis_id)
    if not full_id:
        err_console.print(f"Analysis '{analysis_id}' not found.")
        raise typer.Exit(1)

    # Show what we're deleting
    row = store.get_record(full_id)
    idea_name = row.get("idea_name", "Unknown") if row else "Unknown"
    console.print(f"  [bold white]Analysis:[/] [bold #D97706]{idea_name}[/]  [bright_white]({full_id[:8]})[/]")

    if not yes:
        confirm = Prompt.ask(
            "  [bold red]Delete this analysis? This cannot be undone.[/] [bold white](yes/no)[/]",
            console=console,
            default="no",
        )
        if confirm.strip().lower() not in ("yes", "y"):
            console.print("  [bright_white]Cancelled.[/]")
            raise typer.Exit(0)

    deleted = store.delete_record(full_id)
    if deleted:
        console.print(f"  [bold green]✓ Deleted analysis[/] [bold #D97706]{idea_name}[/] [bright_white]({full_id[:8]})[/]")
    else:
        err_console.print(f"Failed to delete '{analysis_id}'.")
        raise typer.Exit(1)


@app.command()
def clean(
    status_filter: str = typer.Option("pending,failed", "--status", "-s", help="Comma-separated statuses to remove (e.g. pending,failed)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Remove all analyses matching the given status (default: pending and failed)."""
    _print_splash()
    import assumption_zero.storage as store

    statuses = {s.strip().lower() for s in status_filter.split(",") if s.strip()}
    rows = store.list_records(limit=9999)
    targets = [r for r in rows if r.get("status", "").lower() in statuses]

    if not targets:
        console.print(f"  [bright_white]No analyses with status {statuses} found.[/]")
        return

    console.print(f"  [bold white]Found[/] [bold #D97706]{len(targets)}[/] [bold white]analyses to remove:[/]")
    for r in targets[:10]:
        console.print(f"    - [bright_white]{r.get('idea_name', '?')[:30]}[/]  [bold cyan]{r['id'][:8]}[/]  [{_status_color(r.get('status',''))}]{r.get('status','')}[/]")
    if len(targets) > 10:
        console.print(f"    ... and {len(targets)-10} more")

    if not yes:
        confirm = Prompt.ask(
            f"  [bold red]Delete all {len(targets)} entries? This cannot be undone.[/] [bold white](yes/no)[/]",
            console=console,
            default="no",
        )
        if confirm.strip().lower() not in ("yes", "y"):
            console.print("  [bright_white]Cancelled.[/]")
            raise typer.Exit(0)

    removed = 0
    for r in targets:
        if store.delete_record(r["id"]):
            removed += 1

    console.print(f"  [bold green]✓ Removed {removed} analyses.[/]")

@app.command()
def version() -> None:
    """Show version and configuration info."""
    _print_splash()

    from assumption_zero.services.analysis_service import build_llm_adapter, build_research_providers

    adapter = build_llm_adapter()
    providers = build_research_providers()

    table = Table(box=box.SIMPLE, show_header=False, show_edge=False, padding=(0, 2))
    table.add_column(style="bright_white", width=24)
    table.add_column(style="bold cyan")

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
