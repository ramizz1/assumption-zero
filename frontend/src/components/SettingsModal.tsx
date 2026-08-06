import React, { useState, useEffect } from 'react'

// Provider Icons
const LucideSparkles = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M3 5h4"/></svg>
const LlamaIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v10m0 0-4-4m4 4 4-4"/><path d="M4 14c0-2.2 1.8-4 4-4s4 1.8 4 4v7H4v-7Z"/><path d="M20 14c0-2.2-1.8-4-4-4s-4 1.8-4 4v7h8v-7Z"/></svg>
const LucideCode = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
const LucideBot = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="14" x="3" y="7" rx="2" ry="2"/><path d="M12 3v4"/><path d="M8 3h8"/><path d="M15 12v.01"/><path d="M9 12v.01"/></svg>
const LucideZap = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
const LucideCloud = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>

interface Props {
  isOpen: boolean
  onClose: () => void
  onSave?: (settings: AISettings) => void
}

export interface AISettings {
  provider: 'beta' | 'groq' | 'openrouter' | 'hybrid' | 'openai_compat' | 'ollama' | 'opencode' | 'custom'
  groqKey: string
  openrouterKey: string
  opencodeKey: string
  openaiKey: string
  ollamaUrl: string
  customKey: string
  customUrl: string
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
    customKey: '',
    customUrl: 'http://localhost:8000/v1',
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/40 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl flex flex-col bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden verseo-card">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 font-bold text-lg shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            </div>
            <div>
              <h2 className="text-xl font-display font-bold text-gray-900 tracking-tight">AI Engine Configuration</h2>
              <p className="text-xs text-gray-500">Configure LLM provider keys and local Ollama server</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-gray-500 hover:text-gray-900 flex items-center justify-center transition-colors shadow-sm"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-5 overflow-y-auto max-h-[70vh]">
          {/* Provider Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-gray-700">
              Active AI Provider
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
              {[
                { id: 'ollama', label: 'Ollama', icon: <img src="/ollama.png" alt="Ollama" className="w-4 h-4 object-contain" /> },
                { id: 'opencode', label: 'OpenCode', icon: <img src="/opencode.png" alt="OpenCode" className="w-4 h-4 object-contain" /> },
                { id: 'openai_compat', label: 'OpenAI', icon: <img src="/openai.png" alt="OpenAI" className="w-4 h-4 object-contain" /> },
                { id: 'groq', label: 'Groq (L3)', icon: <img src="/groq.png" alt="Groq" className="w-4 h-4 object-contain" /> },
                { id: 'openrouter', label: 'OpenRouter', icon: <img src="/openrouter.png" alt="OpenRouter" className="w-4 h-4 object-contain" /> },
                { id: 'custom', label: 'Custom', icon: <LucideBot /> },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setSettings((s) => ({ ...s, provider: p.id as AISettings['provider'] }))}
                  className={`p-3 rounded-xl border font-medium flex items-center gap-2 transition-all ${
                    settings.provider === p.id
                      ? 'bg-gray-100 text-gray-900 border-gray-900 shadow-sm ring-1 ring-gray-900'
                      : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300 hover:text-gray-900 shadow-sm'
                  }`}
                >
                  {p.icon}
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Conditional Input Fields */}
          {settings.provider === 'ollama' && (
            <div className="space-y-2 p-4 rounded-xl bg-blue-50 border border-blue-200 animate-in fade-in">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-blue-800">
                <img src="/ollama.png" alt="Ollama" className="w-4 h-4 object-contain" /> Ollama Base URL
              </label>
              <input
                type="text"
                placeholder="http://localhost:11434"
                value={settings.ollamaUrl}
                onChange={(e) => setSettings((s) => ({ ...s, ollamaUrl: e.target.value }))}
                className="w-full bg-white border border-blue-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-blue-400 shadow-inner"
              />
              <p className="text-[11px] text-blue-600">
                Connects to your local Ollama server. Make sure Ollama is running (`ollama serve`).
              </p>
            </div>
          )}

          {settings.provider === 'opencode' && (
            <div className="space-y-2 p-4 rounded-xl bg-emerald-50 border border-emerald-200 animate-in fade-in">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800">
                <img src="/opencode.png" alt="OpenCode" className="w-4 h-4 object-contain" /> OpenCode AI API Key
              </label>
              <input
                type="password"
                placeholder="opencode-api-key..."
                value={settings.opencodeKey}
                onChange={(e) => setSettings((s) => ({ ...s, opencodeKey: e.target.value }))}
                className="w-full bg-white border border-emerald-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-emerald-400 font-mono shadow-inner"
              />
              <p className="text-[11px] text-emerald-600">
                Get your key at <a href="https://opencode.ai" target="_blank" rel="noreferrer" className="text-emerald-700 underline font-semibold">opencode.ai</a>
              </p>
            </div>
          )}

          {settings.provider === 'openai_compat' && (
            <div className="space-y-2 p-4 rounded-xl bg-orange-50 border border-orange-200 animate-in fade-in">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-orange-800">
                <img src="/openai.png" alt="OpenAI" className="w-4 h-4 object-contain" /> OpenAI / ChatGPT API Key
              </label>
              <input
                type="password"
                placeholder="sk-..."
                value={settings.openaiKey}
                onChange={(e) => setSettings((s) => ({ ...s, openaiKey: e.target.value }))}
                className="w-full bg-white border border-orange-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-orange-400 font-mono shadow-inner"
              />
              <p className="text-[11px] text-orange-600">
                Uses OpenAI ChatGPT models (gpt-4o-mini, gpt-4o).
              </p>
            </div>
          )}

          {settings.provider === 'groq' && (
            <div className="space-y-2 p-4 rounded-xl bg-red-50 border border-red-200 animate-in fade-in">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-red-800">
                <img src="/groq.png" alt="Groq" className="w-4 h-4 object-contain" /> Groq API Key
              </label>
              <input
                type="password"
                placeholder="gsk_..."
                value={settings.groqKey}
                onChange={(e) => setSettings((s) => ({ ...s, groqKey: e.target.value }))}
                className="w-full bg-white border border-red-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-red-400 font-mono shadow-inner"
              />
              <p className="text-[11px] text-red-600">
                Free key at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" className="text-red-700 underline font-semibold">console.groq.com</a>
              </p>
            </div>
          )}

          {settings.provider === 'openrouter' && (
            <div className="space-y-2 p-4 rounded-xl bg-indigo-50 border border-indigo-200 animate-in fade-in">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-indigo-800">
                <img src="/openrouter.png" alt="OpenRouter" className="w-4 h-4 object-contain" /> OpenRouter API Key
              </label>
              <input
                type="password"
                placeholder="sk-or-v1-..."
                value={settings.openrouterKey}
                onChange={(e) => setSettings((s) => ({ ...s, openrouterKey: e.target.value }))}
                className="w-full bg-white border border-indigo-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-indigo-400 font-mono shadow-inner"
              />
              <p className="text-[11px] text-indigo-600">
                Access 200+ open models at <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer" className="text-indigo-700 underline font-semibold">openrouter.ai</a>
              </p>
            </div>
          )}

          {settings.provider === 'custom' && (
            <div className="space-y-3 p-4 rounded-xl bg-gray-50 border border-gray-200 animate-in fade-in">
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-800">
                  <LucideBot /> Custom Base URL
                </label>
                <input
                  type="text"
                  placeholder="http://localhost:8000/v1"
                  value={settings.customUrl}
                  onChange={(e) => setSettings((s) => ({ ...s, customUrl: e.target.value }))}
                  className="w-full bg-white border border-gray-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-gray-400 font-mono shadow-inner"
                />
              </div>
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-800">
                  <LucideCode /> Custom API Key (Optional)
                </label>
                <input
                  type="password"
                  placeholder="api-key..."
                  value={settings.customKey}
                  onChange={(e) => setSettings((s) => ({ ...s, customKey: e.target.value }))}
                  className="w-full bg-white border border-gray-200 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-gray-400 font-mono shadow-inner"
                />
              </div>
              <p className="text-[11px] text-gray-600">
                Connects to any OpenAI-compatible API endpoint.
              </p>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-4 border-t border-gray-200 flex items-center justify-between">
            <span className="text-xs text-gray-500 font-mono flex items-center gap-1.5">
              {savedStatus ? (
                <span className="text-emerald-600 font-bold">✓ Saved successfully!</span>
              ) : (
                'Settings stored locally in browser'
              )}
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
                className="btn-primary text-xs px-5 py-2"
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
