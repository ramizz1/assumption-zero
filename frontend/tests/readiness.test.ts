import { describe, expect, it } from 'vitest'
import { assessFormReadiness, assessPromptReadiness } from '../src/lib/readiness'

describe('idea readiness', () => {
  it('scores a detailed prompt higher than a vague prompt', () => {
    const vague = assessPromptReadiness('An app for people')
    const detailed = assessPromptReadiness(
      'A subscription app for small law firms in the US that need to replace slow manual meeting notes. Price is $49 per user and Otter is the main competitor.',
    )
    expect(detailed.score).toBeGreaterThan(vague.score)
    expect(detailed.score).toBe(100)
  })

  it('requires useful commercial context in the form', () => {
    const result = assessFormReadiness({
      name: 'LegalMind',
      description: 'Private meeting notes for legal teams',
      problem: 'Law firms cannot safely send confidential audio to cloud transcription tools.',
      target_customer: 'Small law firms',
      geography: 'United States',
    })
    expect(result.score).toBe(80)
    expect(result.checks.find((check) => check.id === 'commercial')?.complete).toBe(false)
  })
})
