import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import AnalysisRunProgress, {
  ANALYSIS_REQUEST_TIMEOUT_MS,
  estimateAnalysisRun,
  formatElapsedTime,
} from '../src/components/AnalysisRunProgress'

describe('analysis run progress', () => {
  it('formats elapsed seconds without hiding long waits', () => {
    expect(formatElapsedTime(0)).toBe('0s')
    expect(formatElapsedTime(125)).toBe('2m 05s')
  })

  it('moves through expected phases and never claims completion early', () => {
    const early = estimateAnalysisRun(5, 'exhaustive')
    const research = estimateAnalysisRun(75, 'exhaustive')
    const perspectives = estimateAnalysisRun(145, 'exhaustive')
    const delayed = estimateAnalysisRun(260, 'exhaustive')

    expect(early.phase).toContain('Connecting')
    expect(research.phase).toContain('market evidence')
    expect(perspectives.phase).toContain('AI perspectives')
    expect(delayed.delayed).toBe(true)
    expect(delayed.percent).toBeLessThan(100)
    expect([early.percent, research.percent, perspectives.percent, delayed.percent])
      .toEqual([...new Set([early.percent, research.percent, perspectives.percent, delayed.percent])].sort((a, b) => a - b))
  })

  it('stops the browser request before the five-minute host limit', () => {
    expect(ANALYSIS_REQUEST_TIMEOUT_MS).toBeLessThan(300_000)
    expect(ANALYSIS_REQUEST_TIMEOUT_MS).toBeGreaterThanOrEqual(240_000)
  })

  it('renders accessible progress, elapsed time, and cancellation', () => {
    const onCancel = vi.fn()
    render(<AnalysisRunProgress depth="deep" elapsedSeconds={125} onCancel={onCancel} />)

    expect(screen.getByRole('progressbar', { name: 'Estimated analysis progress' }))
      .toHaveAttribute('aria-valuenow')
    expect(screen.getByText('2m 05s')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).toHaveBeenCalledOnce()
  })
})
