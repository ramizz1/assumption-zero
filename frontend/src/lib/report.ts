import type { AnalysisResult } from '../types'

const list = (items: string[]) => items.length ? items.map((item) => `- ${item}`).join('\n') : '- None recorded'

export function generateMarkdownReport(result: AnalysisResult): string {
  const score = result.opportunity_score
  const lines: string[] = [
    `# ${result.idea_input.name} — Validation Report`,
    '',
    `Generated: ${new Date(result.completed_at || result.created_at).toLocaleString()}`,
    `Analysis ID: ${result.analysis_id}`,
    '',
    '## Executive verdict',
    '',
    `- Opportunity score: ${score ? `${score.total.toFixed(1)}/100` : 'Not available'}`,
    `- Recommendation: ${result.recommendation || 'Not available'}`,
    `- Evidence confidence: ${result.evidence_confidence || 'Not available'}`,
    `- Analysis mode: ${result.models_used.join(', ') || 'Evidence baseline'}`,
    '',
    result.idea_input.description,
    '',
  ]

  if (result.most_dangerous_assumption) {
    lines.push('### Most dangerous assumption', '', result.most_dangerous_assumption, '')
  }

  if (score) {
    lines.push('## Score breakdown', '', '| Dimension | Score | Weight | Confidence |', '|---|---:|---:|---|')
    score.dimensions.forEach((dimension) => {
      lines.push(`| ${dimension.display_name} | ${dimension.raw_score.toFixed(0)} | ${dimension.weight}% | ${dimension.confidence} |`)
    })
    lines.push('')
  }

  if (result.regional_analysis) {
    const regional = result.regional_analysis
    const signalList = (items: typeof regional.demand_signals) => items.length
      ? items.map((item) => `- [${item.evidence_id}] ${item.title} — ${item.source_name}`).join('\n')
      : '- No region-specific evidence collected'
    lines.push(
      `## Regional market reality: ${regional.geography}`, '',
      `- Regional evidence score: ${regional.demand_score.toFixed(0)}/100`,
      `- Confidence: ${regional.confidence}`,
      `- Regional evidence: ${regional.evidence_count} items across ${regional.source_count} sources`,
      result.research_coverage ? `- Research depth: ${result.research_coverage.depth}; ${result.research_coverage.queries_executed} balanced queries executed` : '',
      '', regional.summary, '',
      '### Regional demand signals', '', signalList(regional.demand_signals), '',
      '### Regional pricing signals', '', signalList(regional.pricing_signals), '',
      '### Regional regulatory signals', '', signalList(regional.regulatory_signals), '',
      '### Regional distribution signals', '', signalList(regional.distribution_signals), '',
      '### Localization requirements', '', list(regional.localization_requirements), '',
      '### Regional research gaps', '', list(regional.research_gaps), '',
    )
  }

  if (result.founder_toolkit) {
    const toolkit = result.founder_toolkit
    lines.push(
      '## Founder toolkit', '',
      `**Positioning:** ${toolkit.one_sentence_pitch}`, '',
      `**Ideal customer:** ${toolkit.ideal_customer_profile}`, '',
      `**Beachhead:** ${toolkit.beachhead_market}`, '',
      '### Recommended channels', '', list(toolkit.recommended_channels), '',
      '### Key metrics', '', list(toolkit.key_metrics), '',
      '### 30-day roadmap', '',
    )
    toolkit.roadmap.forEach((action) => {
      lines.push(
        `#### ${action.phase}: ${action.objective}`, '',
        list(action.actions), '',
        `- Success metric: ${action.success_metric}`,
        `- Stop condition: ${action.stop_condition}`,
        `- Budget: ${action.budget_hint}`, '',
      )
    })
    lines.push(
      '### Customer interview questions', '', list(toolkit.interview_questions), '',
      '### Decision rules', '', list(toolkit.decision_rules), '',
    )
  }

  lines.push(
    '## Evidence balance', '',
    `**Strongest support:** ${result.strongest_supporting || 'Insufficient evidence'}`, '',
    `**Strongest contradiction:** ${result.strongest_contradicting || 'Insufficient evidence'}`, '',
    '### Information gaps', '', list(result.missing_information), '',
    '## Independent perspectives', '',
  )

  result.perspectives.forEach((perspective) => {
    lines.push(
      `### ${perspective.perspective_display}`,
      '',
      `Recommendation: **${perspective.recommendation}**`,
      '',
      perspective.summary,
      '',
      '**Key findings**',
      '',
      list(perspective.key_findings),
      '',
      '**Risks**',
      '',
      list(perspective.risks),
      '',
    )
  })

  lines.push('## Evidence-grounded competitors', '')
  if (result.competitors.length === 0) {
    lines.push('- None verified in this research run', '')
  } else {
    result.competitors.forEach((competitor) => {
      const citations = competitor.evidence_ids.length
        ? competitor.evidence_ids.map((id) => `[${id}]`).join(', ')
        : 'Unverified user input'
      lines.push(
        `### ${competitor.name}`,
        '',
        `- Type: ${competitor.competitor_type}`,
        `- Confidence: ${competitor.confidence}`,
        `- Evidence: ${citations}`,
        `- Description: ${competitor.description}`,
        `- Strengths: ${competitor.strengths.join('; ') || 'Not established'}`,
        `- Weaknesses: ${competitor.weaknesses.join('; ') || 'Not established'}`,
        `- Complaints: ${competitor.complaints.join('; ') || 'Not established'}`,
        `- Differentiation hypotheses: ${competitor.differentiation.join('; ') || 'None recorded'}`,
        '',
      )
    })
  }

  lines.push('## Validation experiments', '')
  result.experiments.forEach((experiment, index) => {
    lines.push(
      `### ${index + 1}. ${experiment.title}`,
      '',
      `- Assumption: ${experiment.assumption_tested}`,
      `- Time: ${experiment.estimated_time}`,
      `- Cost: ${experiment.estimated_cost_range}`,
      `- Success threshold: ${experiment.success_threshold}`,
      `- Failure threshold: ${experiment.failure_threshold}`,
      `- Decision: ${experiment.decision_after}`,
      '',
      experiment.procedure,
      '',
    )
  })

  lines.push('## Sources', '')
  result.evidence.forEach((evidence) => {
    const link = evidence.url && !evidence.url.startsWith('demo://') ? ` — ${evidence.url}` : ''
    lines.push(`- [${evidence.evidence_id}] ${evidence.title}${link}`)
  })

  lines.push(
    '',
    '---',
    'Assumption Zero provides decision support, not a prediction or a substitute for direct customer validation.',
    '',
  )
  return lines.join('\n')
}
