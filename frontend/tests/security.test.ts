import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearInMemoryAISettings,
  getStoredAISettings,
  saveAISettings,
  type AISettings,
} from '../src/components/SettingsModal'
import { getAnalysisOwnerToken } from '../src/lib/api'

describe('browser secret handling', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    clearInMemoryAISettings()
  })

  it('persists only the provider preference, never API keys or endpoint URLs', () => {
    const settings: AISettings = {
      provider: 'groq',
      groqKey: 'gsk_' + 'super_secret_value',
      openrouterKey: 'sk-or-v1-' + 'super-secret',
      opencodeKey: 'opencode-secret',
      openaiKey: 'sk-openai-secret',
      ollamaUrl: 'http://localhost:11434/private',
      customKey: 'custom-secret',
      customUrl: 'https://example.com/v1?token=secret',
    }

    saveAISettings(settings)
    const persisted = localStorage.getItem('azero_ai_preferences') || ''

    expect(JSON.parse(persisted)).toEqual({ provider: 'groq' })
    expect(persisted).not.toContain('secret')
    expect(sessionStorage.getItem('azero_ai_session_secrets')).toBeNull()
    expect(getStoredAISettings().groqKey).toBe(settings.groqKey)
  })

  it('uses a random owner capability without confusing it with a provider key', () => {
    const owner = getAnalysisOwnerToken()
    expect(owner).toMatch(/^[A-Za-z0-9_-]{32,128}$/)
    expect(owner).not.toMatch(/^(sk-|gsk_)/)
  })
})
