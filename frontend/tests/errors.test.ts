import { describe, expect, it } from 'vitest'

import {
  AI_CAPACITY_MESSAGE,
  AI_GENERIC_MESSAGE,
  analysisErrorTitle,
  safeAnalysisMessage,
  safeRequestMessage,
} from '../src/lib/errors'

describe('safe AI errors', () => {
  it('never renders adapter, model, or perspective details from a legacy record', () => {
    const legacy = 'Perspective skeptical_investor failed: Openrouter/Google/Gemma-4-26B-A4B-It:Free could not complete the request.'
    const message = safeAnalysisMessage(legacy)

    expect(message).toBe(AI_GENERIC_MESSAGE)
    expect(message).not.toMatch(/skeptical|openrouter|gemma/i)
  })

  it('gives an accurate capacity message for quota and rate-limit failures', () => {
    expect(safeAnalysisMessage('HTTP 429 quota exceeded')).toBe(AI_CAPACITY_MESSAGE)
    expect(analysisErrorTitle('rate limit reached')).toBe('No AI Capacity Available')
  })

  it('keeps useful validation text but rejects internal upstream details', () => {
    expect(safeRequestMessage('Add the customer and problem before continuing.')).toBe(
      'Add the customer and problem before continuing.',
    )
    expect(safeRequestMessage('fallback-chain(openrouter/secret-model) failed')).toBe(
      AI_GENERIC_MESSAGE,
    )
  })
})
