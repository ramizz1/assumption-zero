import React, { useState, useEffect } from 'react'

interface Props {
  isOpen: boolean
  onClose: () => void
  onSave?: (settings: AISettings) => void
}

export interface AISettings {
  provider: 'beta' | 'groq' | 'openrouter' | 'hybrid' | 'openai_compat' | 'ollama' | 'opencode'
  groqKey: string
  openrouterKey: string
  opencodeKey: string
  openaiKey: string
  ollamaUrl: string
}

const STORAGE_KEY = 'azero_ai_settings'

export const getStoredAISettings = (): AISettings => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      return JSON.parse(raw)
    }
  } catch {
    // fallback
  }
  return {
    provider: 'beta',
    groqKey: '',
    openrouterKey: '',
    opencodeKey: '',
    openaiKey: '',
    ollamaUrl: 'http://localhost:11434',
  }
}

export const SettingsModal: React.FC<Props> = ({ isOpen, onClose, onSave }) => {
  const [settings, setSettings] = useState<AISettings>(getStoredAISettings())
  const [savedStatus, setSavedStatus] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setSettings(getStoredAISettings())
      setSavedStatus(false)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
      if (onSave) onSave(settings)
      setSavedStatus(true)
      setTimeout(() => {
        setSavedStatus(false)
        onClose()
      }, 600)
    } catch (err) {
      alert('Failed to save settings to localStorage')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl flex flex-col bg-[#10121a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-[#141622]/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 font-bold text-lg">
              ⚙️
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">AI Engine Configuration</h2>
              <p className="text-xs text-gray-400">Configure LLM provider keys and local Ollama server</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-white/10 hover:border-white/20 text-gray-400 hover:text-white flex items-center justify-center transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-5 overflow-y-auto max-h-[70vh]">
          {/* Provider Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-gray-200">
              Active AI Provider
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {[
                { id: 'beta', label: '✦ Built-in Beta' },
                { id: 'ollama', label: '🦙 Ollama Local' },
                { id: 'opencode', label: '⚡ OpenCode AI' },
                { id: 'openai_compat', label: '🤖 OpenAI / ChatGPT' },
                { id: 'groq', label: '⚡ Groq (Llama 3.3)' },
                { id: 'openrouter', label: '🌐 OpenRouter' },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setSettings((s) => ({ ...s, provider: p.id as AISettings['provider'] }))}
                  className={`p-3 rounded-xl border font-medium text-left transition-all ${
                    settings.provider === p.id
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-md ring-1 ring-amber-500/30'
                      : 'bg-[#151724] text-gray-400 border-white/5 hover:border-white/20 hover:text-white'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Conditional Input Fields */}
          {settings.provider === 'ollama' && (
            <div className="space-y-2 p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 animate-in fade-in">
              <label className="block text-xs font-semibold text-blue-300">
                🦙 Ollama Base URL
              </label>
              <input
                type="text"
                placeholder="http://localhost:11434"
                value={settings.ollamaUrl}
                onChange={(e) => setSettings((s) => ({ ...s, ollamaUrl: e.target.value }))}
                className="w-full bg-[#141622] border border-blue-500/30 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-400"
              />
              <p className="text-[11px] text-gray-400">
                Connects to your local Ollama server. Make sure Ollama is running (`ollama serve`).
              </p>
            </div>
          )}

          {settings.provider === 'opencode' && (
            <div className="space-y-2 p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 animate-in fade-in">
              <label className="block text-xs font-semibold text-emerald-300">
                ⚡ OpenCode AI API Key
              </label>
              <input
                type="password"
                placeholder="opencode-api-key..."
                value={settings.opencodeKey}
                onChange={(e) => setSettings((s) => ({ ...s, opencodeKey: e.target.value }))}
                className="w-full bg-[#141622] border border-emerald-500/30 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-emerald-400 font-mono"
              />
              <p className="text-[11px] text-gray-400">
                Get your key at <a href="https://opencode.ai" target="_blank" rel="noreferrer" className="text-emerald-400 underline">opencode.ai</a>
              </p>
            </div>
          )}

          {settings.provider === 'openai_compat' && (
            <div className="space-y-2 p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 animate-in fade-in">
              <label className="block text-xs font-semibold text-amber-300">
                🤖 OpenAI / ChatGPT API Key
              </label>
              <input
                type="password"
                placeholder="sk-..."
                value={settings.openaiKey}
                onChange={(e) => setSettings((s) => ({ ...s, openaiKey: e.target.value }))}
                className="w-full bg-[#141622] border border-amber-500/30 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-amber-400 font-mono"
              />
              <p className="text-[11px] text-gray-400">
                Uses OpenAI ChatGPT models (gpt-4o-mini, gpt-4o).
              </p>
            </div>
          )}

          {settings.provider === 'groq' && (
            <div className="space-y-2 p-4 rounded-xl bg-orange-500/5 border border-orange-500/20 animate-in fade-in">
              <label className="block text-xs font-semibold text-orange-300">
                ⚡ Groq API Key
              </label>
              <input
                type="password"
                placeholder="gsk_..."
                value={settings.groqKey}
                onChange={(e) => setSettings((s) => ({ ...s, groqKey: e.target.value }))}
                className="w-full bg-[#141622] border border-orange-500/30 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-orange-400 font-mono"
              />
              <p className="text-[11px] text-gray-400">
                Free key at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" className="text-orange-400 underline">console.groq.com</a>
              </p>
            </div>
          )}

          {settings.provider === 'openrouter' && (
            <div className="space-y-2 p-4 rounded-xl bg-cyan-500/5 border border-cyan-500/20 animate-in fade-in">
              <label className="block text-xs font-semibold text-cyan-300">
                🌐 OpenRouter API Key
              </label>
              <input
                type="password"
                placeholder="sk-or-v1-..."
                value={settings.openrouterKey}
                onChange={(e) => setSettings((s) => ({ ...s, openrouterKey: e.target.value }))}
                className="w-full bg-[#141622] border border-cyan-500/30 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-cyan-400 font-mono"
              />
              <p className="text-[11px] text-gray-400">
                Access 200+ open models at <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer" className="text-cyan-400 underline">openrouter.ai</a>
              </p>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-4 border-t border-white/10 flex items-center justify-between">
            <span className="text-xs text-gray-400">
              {savedStatus ? '✓ Saved successfully!' : 'Settings stored locally in browser'}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="btn-ghost text-xs px-4 py-2"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary text-xs px-5 py-2 bg-amber-500 hover:bg-amber-400 text-black font-bold"
              >
                Save Settings
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SettingsModal
