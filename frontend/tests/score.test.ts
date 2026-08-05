/**
 * Frontend utility tests for score and confidence formatting.
 * These test that the UI correctly maps backend values to display values.
 */
import { describe, it, expect } from 'vitest'
import {
  scoreColor,
  recommendationColor,
  confidenceColor,
  reliabilityBadge,
  DISCLAIMER,
} from '../src/lib/utils'
import type { Recommendation } from '../src/types'

describe('scoreColor', () => {
  it('returns green for scores >= 65', () => {
    expect(scoreColor(65)).toBe('text-green-400')
    expect(scoreColor(80)).toBe('text-green-400')
    expect(scoreColor(100)).toBe('text-green-400')
  })

  it('returns amber for scores 45-64', () => {
    expect(scoreColor(45)).toBe('text-amber-400')
    expect(scoreColor(50)).toBe('text-amber-400')
    expect(scoreColor(64)).toBe('text-amber-400')
  })

  it('returns red for scores < 45', () => {
    expect(scoreColor(0)).toBe('text-red-400')
    expect(scoreColor(30)).toBe('text-red-400')
    expect(scoreColor(44)).toBe('text-red-400')
  })
})

describe('recommendationColor', () => {
  const cases: [Recommendation, string][] = [
    ['Build', 'text-green-400'],
    ['Test First', 'text-amber-400'],
    ['Pivot', 'text-orange-400'],
    ['Avoid', 'text-red-400'],
  ]

  it.each(cases)('returns correct color for %s', (rec, expected) => {
    expect(recommendationColor(rec)).toBe(expected)
  })
})

describe('confidenceColor', () => {
  it('returns green for high confidence', () => {
    expect(confidenceColor('high')).toBe('text-green-400')
  })

  it('returns amber for medium confidence', () => {
    expect(confidenceColor('medium')).toBe('text-amber-400')
  })

  it('returns red for low confidence', () => {
    expect(confidenceColor('low')).toBe('text-red-400')
  })
})

describe('reliabilityBadge', () => {
  it('returns green classes for high reliability', () => {
    const cls = reliabilityBadge('high')
    expect(cls).toContain('green')
  })

  it('returns amber classes for medium reliability', () => {
    const cls = reliabilityBadge('medium')
    expect(cls).toContain('amber')
  })

  it('returns red classes for low reliability', () => {
    const cls = reliabilityBadge('low')
    expect(cls).toContain('red')
  })
})

describe('DISCLAIMER', () => {
  it('is a non-empty string', () => {
    expect(typeof DISCLAIMER).toBe('string')
    expect(DISCLAIMER.length).toBeGreaterThan(20)
  })

  it('does not claim success probability', () => {
    expect(DISCLAIMER).not.toMatch(/\d+%/)
    expect(DISCLAIMER.toLowerCase()).not.toContain('success rate')
    expect(DISCLAIMER.toLowerCase()).not.toContain('probability')
  })

  it('mentions decision support', () => {
    expect(DISCLAIMER.toLowerCase()).toContain('decision support')
  })
})
