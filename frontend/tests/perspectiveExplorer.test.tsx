import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import PerspectiveExplorer from '../src/components/PerspectiveExplorer'
import type { AnalysisPerspective } from '../src/types'

const perspective = (overrides: Partial<AnalysisPerspective>): AnalysisPerspective => ({
  perspective_name: 'market_analyst',
  perspective_display: 'Market Analyst',
  model_id: 'test-model',
  summary: 'Market summary',
  key_findings: ['§MARKET SIZING§', 'A useful market finding'],
  risks: ['Market risk'],
  opportunities: ['Market opportunity'],
  recommendation: 'Test First',
  cited_evidence_ids: [],
  invalid_citations: [],
  dimension_scores: {},
  most_dangerous_assumption: 'Market assumption',
  ...overrides,
})

describe('AI perspective explorer', () => {
  it('shows one perspective at a time and cleans legacy section markers', () => {
    render(
      <PerspectiveExplorer
        evidence={[]}
        perspectives={[
          perspective({}),
          perspective({
            perspective_name: 'regional_strategist',
            perspective_display: 'Regional Strategist',
            summary: 'Regional summary',
            key_findings: ['В§REGULATION & LOCALIZATIONВ§', 'A regional finding'],
          }),
        ]}
      />,
    )

    expect(screen.getByText('Market summary')).toBeInTheDocument()
    expect(screen.queryByText('Regional summary')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /Regional Strategist/i }))

    expect(screen.queryByText('Market summary')).not.toBeInTheDocument()
    expect(screen.getByText('Regional summary')).toBeInTheDocument()
    expect(screen.getByText('REGULATION & LOCALIZATION')).toBeInTheDocument()
    expect(screen.queryByText('В§REGULATION & LOCALIZATIONВ§')).not.toBeInTheDocument()
  })
})
