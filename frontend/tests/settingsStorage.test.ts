import { beforeEach, describe, expect, it } from 'vitest'

import { getStoredAISettings, saveAISettings, type AISettings } from '../src/components/SettingsModal'

const settings: AISettings = {
  provider: 'groq',
  groqKey: 'secret-groq',
  openrouterKey: 'secret-openrouter',
  opencodeKey: '',
  openaiKey: '',
  ollamaUrl: 'http://localhost:11434',
  customKey: 'secret-custom',
  customUrl: 'https://models.example.com/v1',
}

describe('AI settings storage', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  it('keeps API keys out of persistent local storage', () => {
    saveAISettings(settings)

    expect(localStorage.getItem('azero_ai_preferences')).not.toContain('secret-')
    expect(sessionStorage.getItem('azero_ai_session_secrets')).toContain('secret-groq')
    expect(getStoredAISettings()).toEqual(settings)
  })

  it('migrates legacy persisted secrets into session storage', () => {
    localStorage.setItem('azero_ai_settings', JSON.stringify(settings))

    expect(getStoredAISettings()).toEqual(settings)
    expect(localStorage.getItem('azero_ai_settings')).toBeNull()
    expect(localStorage.getItem('azero_ai_preferences')).not.toContain('secret-')
    expect(sessionStorage.getItem('azero_ai_session_secrets')).toContain('secret-groq')
  })
})
