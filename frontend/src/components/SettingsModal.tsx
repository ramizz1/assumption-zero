import React, { useState, useEffect } from 'react'
import ProviderIcon from './ProviderIcon'
import { api } from '../lib/api'

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
  provider: 'auto' | 'beta' | 'groq' | 'openrouter' | 'hybrid' | 'openai_compat' | 'ollama' | 'opencode' | 'custom'
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
  const defaults: AISettings = {
    provider: 'auto',
    groqKey: '',
    openrouterKey: '',
    opencodeKey: '',
    openaiKey: '',
    ollamaUrl: 'http://localhost:11434',
    customKey: '',
    customUrl: 'http://localhost:8000/v1',
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const stored = JSON.parse(raw) as Partial<AISettings>
      return {
        ...defaults,
        ...stored,
        provider: stored.provider === 'beta' ? 'auto' : (stored.provider || defaults.provider),
      }
    }
  } catch {
    // fallback
  }
  return defaults
}

export const SettingsModal: React.FC<Props> = ({ isOpen, onClose, onSave }) => {
  const [settings, setSettings] = useState<AISettings>(getStoredAISettings())
  const [savedStatus, setSavedStatus] = useState(false)
  const [showKeys, setShowKeys] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ status: 'ok' | 'error'; message: string } | null>(null)

  useEffect(() => {
    if (isOpen) {
      setSettings(getStoredAISettings())
      setSavedStatus(false)
      setTestResult(null)
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

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await api.verifyKeys({
        provider: settings.provider,
        groqKey: settings.groqKey,
        openrouterKey: settings.openrouterKey,
        opencodeKey: settings.opencodeKey,
        openaiKey: settings.openaiKey,
        ollamaUrl: settings.ollamaUrl,
        customUrl: settings.customUrl,
      })
      setTestResult({ status: 'ok', message: res.message || `Successfully connected to ${settings.provider}!` })
    } catch (err: any) {
      setTestResult({ status: 'error', message: err.message || `Failed to connect to ${settings.provider}.` })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/40 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl flex flex-col bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden verseo-card">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-200 bg-amber-50/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-900 font-bold text-lg shadow-xs">
              🔑
            </div>
            <div>
              <h2 className="text-lg font-display font-bold text-gray-900 tracking-tight">
                AI Provider API Keys & Settings
              </h2>
              <p className="text-xs text-gray-500 font-mono">
                Browser-only keys for analysis requests; this does not edit the server .env
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg border border-gray-200 bg-white hover:bg-gray-100 text-gray-500 hover:text-gray-900 flex items-center justify-center transition-colors shadow-xs"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-5 overflow-y-auto max-h-[75vh]">
          {/* Key Visibility & Test Controls */}
          <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-200">
            <label className="flex items-center gap-2 text-xs font-mono font-medium text-gray-700 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showKeys}
                onChange={(e) => setShowKeys(e.target.checked)}
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
              />
              <span>{showKeys ? '🙈 Hide API Keys' : '👁️ Show API Keys'}</span>
            </label>

            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing}
              className="px-3 py-1.5 rounded-lg border border-gray-300 bg-white hover:bg-gray-100 text-xs font-mono font-bold text-gray-800 transition-all flex items-center gap-1.5 shadow-xs"
            >
              {testing ? '⚡ Validating...' : '⚡ Validate Setup'}
            </button>
          </div>

          {testResult && (
            <div
              className={`p-3.5 rounded-xl border text-xs font-mono flex items-center gap-2 animate-in fade-in ${
                testResult.status === 'ok'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              <span>{testResult.status === 'ok' ? '✓' : '⚠️'}</span>
              <span className="flex-1 font-medium">{testResult.message}</span>
            </div>
          )}

          {/* Provider Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-gray-700">
              Active AI Provider
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
              {[
                { id: 'auto', label: 'Auto' },
                { id: 'ollama', label: 'Ollama' },
                { id: 'opencode', label: 'OpenCode' },
                { id: 'openai_compat', label: 'OpenAI' },
                { id: 'groq', label: 'Groq (L3)' },
                { id: 'openrouter', label: 'OpenRouter' },
                { id: 'custom', label: 'Custom' },
              ].map((p) => {
                const isActive = settings.provider === p.id
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setSettings((s) => ({ ...s, provider: p.id as AISettings['provider'] }))}
                    className={`p-3 rounded-xl border font-medium flex items-center gap-2 transition-all ${
                      isActive
                        ? 'bg-gray-900 text-white border-gray-900 shadow-md ring-1 ring-gray-900'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:text-gray-900 shadow-sm'
                    }`}
                  >
                    <ProviderIcon id={p.id} isActive={isActive} size="sm" />
                    {p.label}
                  </button>
                )
              })}
            </div>
            {settings.provider === 'auto' && (
              <p className="text-[11px] text-gray-500 leading-relaxed">
                Uses your first browser key (Groq first), then configured server providers. Without a working AI, Assumption Zero runs a clearly labelled evidence baseline.
              </p>
            )}
          </div>

          {/* Conditional Input Fields */}
          {settings.provider === 'ollama' && (
            <div className="space-y-2 p-4 rounded-xl bg-blue-50/80 border border-blue-200 animate-in fade-in">
              <label className="flex items-center gap-2 text-xs font-bold text-blue-900">
                <ProviderIcon id="ollama" isActive={false} size="sm" /> Ollama Base URL
              </label>
              <input
                type="text"
                placeholder="http://localhost:11434"
                value={settings.ollamaUrl}
                onChange={(e) => setSettings((s) => ({ ...s, ollamaUrl: e.target.value }))}
                className="w-full bg-white border border-blue-300 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:border-blue-500 font-mono shadow-inner"
              />
              <p className="text-[11px] text-blue-700 font-medium">
                Connects to your local Ollama server. Make sure Ollama is running (`ollama serve`).
              </p>
            </div>
          )}

          {settings.provider === 'opencode' && (
            <div className="space-y-2 p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 animate-in fade-in">
              <label className="flex items-center justify-between text-xs font-bold text-emerald-900">
                <span className="flex items-center gap-2">
                  <ProviderIcon id="opencode" isActive={false} size="sm" /> OpenCode AI API Key
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  {settings.opencodeKey ? '✓ Key Entered' : '🔑 Key Required'}
                </span>
              </label>
              <input
                type={showKeys ? 'text' : 'password'}
                placeholder="opencode-api-key..."
                value={settings.opencodeKey}
                onChange={(e) => setSettings((s) => ({ ...s, opencodeKey: e.target.value }))}
                className="w-full bg-white border border-emerald-300 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:border-emerald-500 font-mono shadow-inner"
              />
              <p className="text-[11px] text-emerald-700 font-medium">
                Get your key at <a href="https://opencode.ai" target="_blank" rel="noreferrer" className="text-emerald-800 underline font-bold">opencode.ai</a>
              </p>
            </div>
          )}

          {settings.provider === 'openai_compat' && (
            <div className="space-y-2 p-4 rounded-xl bg-orange-50/80 border border-orange-200 animate-in fade-in">
              <label className="flex items-center justify-between text-xs font-bold text-orange-900">
                <span className="flex items-center gap-2">
                  <ProviderIcon id="openai_compat" isActive={false} size="sm" /> OpenAI / ChatGPT API Key
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-orange-100 text-orange-800">
                  {settings.openaiKey ? '✓ Key Entered' : '🔑 Key Required'}
                </span>
              </label>
              <input
                type={showKeys ? 'text' : 'password'}
                placeholder="sk-..."
                value={settings.openaiKey}
                onChange={(e) => setSettings((s) => ({ ...s, openaiKey: e.target.value }))}
                className="w-full bg-white border border-orange-300 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:border-orange-500 font-mono shadow-inner"
              />
              <p className="text-[11px] text-orange-700 font-medium">
                Uses OpenAI ChatGPT models (gpt-4o-mini, gpt-4o).
              </p>
            </div>
          )}

          {settings.provider === 'groq' && (
            <div className="space-y-2 p-4 rounded-xl bg-red-50/80 border border-red-200 animate-in fade-in">
              <label className="flex items-center justify-between text-xs font-bold text-red-900">
                <span className="flex items-center gap-2">
                  <ProviderIcon id="groq" isActive={false} size="sm" /> Groq API Key
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-100 text-red-800">
                  {settings.groqKey ? '✓ Key Entered' : '🔑 Key Required'}
                </span>
              </label>
              <input
                type={showKeys ? 'text' : 'password'}
                placeholder="gsk_..."
                value={settings.groqKey}
                onChange={(e) => setSettings((s) => ({ ...s, groqKey: e.target.value }))}
                className="w-full bg-white border border-red-300 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:border-red-500 font-mono shadow-inner"
              />
              <p className="text-[11px] text-red-700 font-medium">
                Free key at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" className="text-red-800 underline font-bold">console.groq.com</a>
              </p>
            </div>
          )}

          {settings.provider === 'openrouter' && (
            <div className="space-y-2 p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 animate-in fade-in">
              <label className="flex items-center justify-between text-xs font-bold text-indigo-900">
                <span className="flex items-center gap-2">
                  <ProviderIcon id="openrouter" isActive={false} size="sm" /> OpenRouter API Key
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                  {settings.openrouterKey ? '✓ Key Entered' : '🔑 Key Required'}
                </span>
              </label>
              <input
                type={showKeys ? 'text' : 'password'}
                placeholder="sk-or-v1-..."
                value={settings.openrouterKey}
                onChange={(e) => setSettings((s) => ({ ...s, openrouterKey: e.target.value }))}
                className="w-full bg-white border border-indigo-300 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:border-indigo-500 font-mono shadow-inner"
              />
              <p className="text-[11px] text-indigo-700 font-medium">
                Access 200+ open models at <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer" className="text-indigo-800 underline font-bold">openrouter.ai</a>
              </p>
            </div>
          )}

          {settings.provider === 'custom' && (
            <div className="space-y-3 p-4 rounded-xl bg-gray-50 border border-gray-200 animate-in fade-in">
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-bold text-gray-800">
                  <LucideBot /> Custom Base URL
                </label>
                <input
                  type="text"
                  placeholder="http://localhost:8000/v1"
                  value={settings.customUrl}
                  onChange={(e) => setSettings((s) => ({ ...s, customUrl: e.target.value }))}
                  className="w-full bg-white border border-gray-300 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-gray-500 font-mono shadow-inner"
                />
              </div>
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-bold text-gray-800">
                  <LucideCode /> Custom API Key (Optional)
                </label>
                <input
                  type={showKeys ? 'text' : 'password'}
                  placeholder="api-key..."
                  value={settings.customKey}
                  onChange={(e) => setSettings((s) => ({ ...s, customKey: e.target.value }))}
                  className="w-full bg-white border border-gray-300 rounded-xl px-3.5 py-2 text-sm text-gray-900 focus:outline-none focus:border-gray-500 font-mono shadow-inner"
                />
              </div>
              <p className="text-[11px] text-gray-600 font-medium">
                Connects to any OpenAI-compatible API endpoint.
              </p>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-4 border-t border-gray-200 flex items-center justify-between">
            <span className="text-xs text-gray-500 font-mono flex items-center gap-1.5">
              {savedStatus ? (
                <span className="text-emerald-600 font-bold">✓ Settings Saved!</span>
              ) : (
                'Keys saved in local storage'
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
                className="btn-primary text-xs px-5 py-2 font-bold"
              >
                Save API Keys
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SettingsModal
