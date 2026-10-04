import { describe, expect, it } from 'vitest'
import type { AISettings } from '../src/components/SettingsModal'
import { shouldOfferEvidenceOnly } from '../src/pages/HomePage'

const settings = (overrides: Partial<AISettings> = {}): AISettings => ({
  provider: 'auto',
  groqKey: '',
  openrouterKey: '',
  opencodeKey: '',
  openaiKey: '',
  ollamaUrl: 'http://localhost:11434',
  customKey: '',
  customUrl: 'http://localhost:8000/v1',
  ...overrides,
})

describe('evidence-only analysis choice', () => {
  it('asks before an automatic run when the browser has no API key', () => {
    expect(shouldOfferEvidenceOnly(settings())).toBe(true)
  })

  it('does not ask when Auto has a usable browser key', () => {
    expect(shouldOfferEvidenceOnly(settings({ groqKey: 'test-groq-key' }))).toBe(false)
  })

  it('asks when the selected remote provider has no matching key', () => {
    expect(shouldOfferEvidenceOnly(settings({
      provider: 'openrouter',
      groqKey: 'test-groq-key',
    }))).toBe(true)
  })

  it('does not require a key for a local Ollama run', () => {
    expect(shouldOfferEvidenceOnly(settings({ provider: 'ollama' }))).toBe(false)
  })
})
