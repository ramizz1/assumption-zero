import { fireEvent, render, waitFor } from '@testing-library/react'
import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../src/lib/api'
import { clearInMemoryAISettings, getStoredAISettings, saveAISettings, SettingsModal, type AISettings } from '../src/components/SettingsModal'

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
    clearInMemoryAISettings()
  })

  it('keeps API keys out of persistent local storage', () => {
    saveAISettings(settings)

    expect(localStorage.getItem('azero_ai_preferences')).not.toContain('secret-')
    expect(sessionStorage.getItem('azero_ai_session_secrets')).toBeNull()
    expect(getStoredAISettings()).toEqual(settings)
  })

  it('uses the custom provider key when validating a custom endpoint', async () => {
    const verifySpy = vi.spyOn(api, 'verifyKeys').mockResolvedValue({
      status: 'ok',
      provider: 'custom',
      message: 'Connected',
    })
    const view = render(React.createElement(SettingsModal, { isOpen: true, onClose: () => undefined }))

    fireEvent.click(view.getByRole('button', { name: 'Custom' }))
    fireEvent.change(view.getByPlaceholderText('api-key...'), {
      target: { value: 'custom-session-key' },
    })
    fireEvent.click(view.getByRole('button', { name: 'Validate Setup' }))

    await waitFor(() => expect(verifySpy).toHaveBeenCalled())
    expect(verifySpy.mock.calls[0][0]).toMatchObject({
      ai_provider: 'custom',
      openai_api_key: 'custom-session-key',
    })
    verifySpy.mockRestore()
  })

  it('purges legacy persisted secrets instead of loading them', () => {
    localStorage.setItem('azero_ai_settings', JSON.stringify(settings))

    const migrated = getStoredAISettings()
    expect(migrated.provider).toBe('groq')
    expect(migrated.groqKey).toBe('')
    expect(localStorage.getItem('azero_ai_settings')).toBeNull()
    expect(localStorage.getItem('azero_ai_preferences')).not.toContain('secret-')
    expect(sessionStorage.getItem('azero_ai_session_secrets')).toBeNull()
  })
})
