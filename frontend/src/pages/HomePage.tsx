import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import SavedAnalysesModal from '../components/SavedAnalysesModal'
import SettingsModal, { getStoredAISettings, AISettings } from '../components/SettingsModal'

const SAMPLE_IDEA = {
  name: "LegalMind Local",
  description: "A privacy-first AI meeting summarizer that runs entirely on-device for small legal firms",
  problem: "Legal professionals have confidential client meetings that cannot be recorded or transcribed using cloud-based AI tools due to attorney-client privilege and data sovereignty concerns. Existing tools like Otter.ai and Fireflies.ai send audio to remote servers, creating compliance risks.",
  target_customer: "Solo practitioners and small law firms (1–20 attorneys) who have weekly client meetings and hearings they need documented but cannot use cloud AI tools due to ethical obligations",
  geography: "United States",
  business_model: "SaaS subscription per seat, installed locally, no data leaves the device",
  price: "$49/month per attorney seat",
  founder_skills: "Full-stack developer with 5 years experience, no legal industry background, some ML experience running local models",
  budget: "$15,000 runway for 6 months",
  known_competitors: "Otter.ai, Fireflies.ai, Whisper (open source), Tactiq",
  unfair_advantage: "Proprietary lightweight local model quantization pipeline running 4x faster on Apple Silicon and Windows NPU chips",
  key_assumptions: "Attorneys will pay $49/mo for 100% on-device data privacy rather than risk cloud security compliance violations",
  additional_context: "Planning to use OpenAI Whisper for transcription and a local Llama model for summarization. Initial target is solo practitioners in the US who already use case management software."
}

export const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Modals
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [historyCount, setHistoryCount] = useState<number | null>(null)

  // AI settings
  const [aiSettings, setAiSettings] = useState<AISettings>(getStoredAISettings())
  const [selectedProvider, setSelectedProvider] = useState<string>('beta')
  const [groqApiKey, setGroqApiKey] = useState('')
  const [openrouterApiKey, setOpenrouterApiKey] = useState('')
  const [opencodeApiKey, setOpencodeApiKey] = useState('')
  const [showJsonExample, setShowJsonExample] = useState(false)
  const [inputMode, setInputMode] = useState<'prompt' | 'form'>('prompt')

  const [rawPromptText, setRawPromptText] = useState('')

  const [idea, setIdea] = useState({
    name: '',
    description: '',
    problem: '',
    target_customer: '',
    geography: '',
    business_model: '',
    price: '',
    founder_skills: '',
    budget: '',
    known_competitors: '',
    unfair_advantage: '',
    key_assumptions: '',
    additional_context: '',
  })

  // Load history count on mount
  useEffect(() => {
    api.listAnalyses().then((items) => {
      setHistoryCount(items.length)
    }).catch(() => {})
  }, [])

  const update = (field: keyof typeof idea) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setIdea((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const handleLoadSample = () => {
    if (inputMode === 'prompt') {
      setRawPromptText(
        'LegalMind Local — A privacy-first AI meeting summarizer for small law firms that processes client audio entirely on-device. Business model: $49/month per seat subscription. Target customer: Solo law practices and firms with 1-20 attorneys. Founder has full-stack developer skills with $15,000 budget for 6 months.'
      )
    } else {
      setIdea(SAMPLE_IDEA)
    }
  }

  const handleAnalyzePrompt = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rawPromptText.trim()) return
    setLoading(true)
    setError(null)

    try {
      const activeProvider = selectedProvider || aiSettings.provider
      const result = await api.createAnalysisFromPrompt({
        prompt: rawPromptText,
        ai_provider: activeProvider,
        groq_api_key: groqApiKey || aiSettings.groqKey || undefined,
        openrouter_api_key: openrouterApiKey || aiSettings.openrouterKey || undefined,
        opencode_api_key: opencodeApiKey || aiSettings.opencodeKey || undefined,
        openai_api_key: aiSettings.openaiKey || undefined,
        ollama_base_url: aiSettings.ollamaUrl || undefined,
      })
      navigate(`/analysis/${result.analysis_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start prompt analysis')
      setLoading(false)
    }
  }

  const handleAnalyzeForm = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const activeProvider = selectedProvider || aiSettings.provider
      const payload = {
        name: idea.name,
        description: idea.description,
        problem: idea.problem,
        target_customer: idea.target_customer,
        geography: idea.geography,
        business_model: idea.business_model || undefined,
        price: idea.price || undefined,
        founder_skills: idea.founder_skills || undefined,
        budget: idea.budget || undefined,
        known_competitors: idea.known_competitors || undefined,
        unfair_advantage: idea.unfair_advantage || undefined,
        key_assumptions: idea.key_assumptions || undefined,
        additional_context: idea.additional_context || undefined,
      }

      const result = await api.createAnalysis({
        idea: payload,
        ai_provider_override: activeProvider,
        groq_api_key: groqApiKey || aiSettings.groqKey || undefined,
        openrouter_api_key: openrouterApiKey || aiSettings.openrouterKey || undefined,
        opencode_api_key: opencodeApiKey || aiSettings.opencodeKey || undefined,
        openai_api_key: aiSettings.openaiKey || undefined,
        ollama_base_url: aiSettings.ollamaUrl || undefined,
      })
      navigate(`/analysis/${result.analysis_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis')
      setLoading(false)
    }
  }

  const handleDemo = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.runDemo()
      navigate(`/analysis/${result.analysis_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start demo')
      setLoading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      const content = event.target?.result as string
      if (content) {
        setRawPromptText(content)
      }
    }
    reader.readAsText(file)
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#090a0f] text-gray-100 selection:bg-amber-500/30 selection:text-amber-200">
      {/* Framer-style background glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[20%] left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-amber-500/10 via-amber-600/5 to-transparent blur-[120px] rounded-full opacity-70" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-white/10 px-6 py-4 bg-[#0d0e15]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-amber-400 p-0.5 shadow-lg shadow-amber-500/20">
              <div className="w-full h-full bg-[#0d0e15] rounded-[6px] flex items-center justify-center font-black text-amber-400 text-sm">
                A0
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white tracking-tight">Assumption Zero</span>
                <span className="text-[10px] font-bold text-amber-300 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded-full">
                  v0.1.0
                </span>
              </div>
              <p className="text-[11px] text-gray-400 hidden sm:block">
                Open-source MVP Validation Engine · Live Market Research
              </p>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center gap-3">
            {/* History Drawer Trigger */}
            <button
              type="button"
              onClick={() => setIsHistoryOpen(true)}
              className="px-3 py-1.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-amber-500/30 text-xs font-semibold text-gray-200 transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span>📜 History</span>
              {historyCount !== null && (
                <span className="px-1.5 py-0.5 rounded-md bg-amber-500/20 text-amber-300 text-[10px] font-bold">
                  {historyCount}
                </span>
              )}
            </button>

            {/* AI Engine Settings Trigger */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              className="px-3 py-1.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-xs font-semibold text-gray-200 transition-all flex items-center gap-1.5"
            >
              <span>⚙️ AI Setup</span>
            </button>

            {/* Demo Button */}
            <button
              type="button"
              onClick={handleDemo}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-bold transition-all hidden md:flex items-center gap-1"
            >
              <span>✦ Run Demo</span>
            </button>

            <a
              href="https://github.com/ramizz1/assumption-zero"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-400 hover:text-white transition-colors ml-1 hidden sm:inline"
            >
              GitHub →
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 text-center px-6 pt-14 pb-10 border-b border-white/5">
        <div className="max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 bg-amber-400/10 border border-amber-400/20 rounded-full px-4 py-1.5 text-xs text-amber-300 shadow-sm backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>Multi-Source Live Research • 3 AI Perspectives • Deterministic Scoring</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-tight">
            Stress-test your idea <br />
            <span className="bg-gradient-to-r from-amber-400 via-amber-300 to-orange-400 bg-clip-text text-transparent">
              before you build it.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-gray-400 max-w-2xl mx-auto font-normal">
            Assumption Zero evaluates startup ideas against primary market data, challenge moats, identify competitor complaints, and design 7-day validation experiments.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <main className="relative z-10 flex-1 px-4 sm:px-6 py-10 max-w-5xl mx-auto w-full">
        {error && (
          <div className="mb-8 p-5 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-300 flex items-start gap-3 shadow-xl backdrop-blur-md">
            <span className="text-xl">⚠️</span>
            <div className="flex-1 space-y-1">
              <h4 className="font-bold text-red-400 text-sm">
                {error.includes('gibberish')
                  ? 'Invalid Startup Idea Prompt'
                  : error.includes('402') || error.includes('429') || error.includes('quota')
                  ? 'No AI Tokens Available (Quota Exceeded)'
                  : 'Analysis Request Failed'}
              </h4>
              <p className="text-xs text-red-300/90 leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {/* Card Container */}
        <div className="bg-[#12131b]/90 border border-white/10 rounded-3xl shadow-2xl p-6 sm:p-8 backdrop-blur-xl">
          {/* Mode Switcher Tabs */}
          <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-6 flex-wrap gap-4">
            <div className="flex bg-[#0b0c12] p-1.5 rounded-2xl border border-white/5 gap-1">
              <button
                type="button"
                onClick={() => setInputMode('prompt')}
                className={`py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  inputMode === 'prompt'
                    ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>⚡</span> 1-Prompt Natural Language
              </button>

              <button
                type="button"
                onClick={() => setInputMode('form')}
                className={`py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  inputMode === 'form'
                    ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>📋</span> Structured Form Wizard
              </button>
            </div>

            {/* Quick Sample Action */}
            <button
              type="button"
              onClick={handleLoadSample}
              className="text-xs text-amber-400/90 hover:text-amber-300 font-semibold px-3 py-1.5 rounded-xl border border-amber-500/20 bg-amber-500/10 hover:bg-amber-500/20 transition-colors flex items-center gap-1.5"
            >
              <span>💡</span> Load Example Idea
            </button>
          </div>

          {/* AI Provider selector pills */}
          <div className="mb-6 space-y-2">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="font-semibold text-gray-300">Select AI Provider:</span>
              <button
                type="button"
                onClick={() => setIsSettingsOpen(true)}
                className="text-amber-400 hover:underline"
              >
                Configure Keys ⚙️
              </button>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              {[
                { id: 'beta', label: '✦ Beta AI (Built-in)' },
                { id: 'ollama', label: '🦙 Ollama Local' },
                { id: 'opencode', label: '⚡ OpenCode AI' },
                { id: 'openai_compat', label: '🤖 OpenAI ChatGPT' },
                { id: 'groq', label: '⚡ Groq Llama 3.3' },
                { id: 'openrouter', label: '🌐 OpenRouter' },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setSelectedProvider(p.id)}
                  className={`px-3 py-1.5 rounded-xl border transition-all font-medium ${
                    selectedProvider === p.id
                      ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-md ring-1 ring-amber-500/30'
                      : 'bg-[#161824] border-white/5 text-gray-400 hover:border-white/20 hover:text-white'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Mode 1: Natural Language Prompt */}
          {inputMode === 'prompt' ? (
            <form onSubmit={handleAnalyzePrompt} className="space-y-6">
              <div className="space-y-2">
                <label className="block text-sm font-bold text-white">
                  Describe Your Startup or MVP Idea
                </label>
                <p className="text-xs text-gray-400">
                  Describe what you're building, target audience, problem solved, pricing, or competitors in plain natural text.
                </p>

                <textarea
                  rows={6}
                  value={rawPromptText}
                  onChange={(e) => setRawPromptText(e.target.value)}
                  placeholder="e.g. LegalMind Local — A privacy-first AI meeting summarizer for small law firms that processes audio entirely on-device. Pricing: $49/mo per seat. Target: Solo practitioners and small firms in the US..."
                  className="w-full bg-[#0b0c12] border border-white/10 rounded-2xl p-4 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-amber-500/60 focus:ring-1 focus:ring-amber-500/30 transition-all resize-y"
                  required
                />
              </div>

              {/* Upload file helper */}
              <div className="flex items-center justify-between text-xs text-gray-400 flex-wrap gap-2">
                <label className="cursor-pointer hover:text-amber-400 transition-colors flex items-center gap-1.5 bg-white/5 border border-white/10 px-3 py-1.5 rounded-xl">
                  <span>📁</span> Upload .txt or .json File
                  <input type="file" accept=".txt,.json,.md" onChange={handleFileUpload} className="hidden" />
                </label>

                <span className="text-gray-500">{rawPromptText.length} characters</span>
              </div>

              <button
                type="submit"
                disabled={loading || !rawPromptText.trim()}
                className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-black font-extrabold rounded-2xl hover:from-amber-400 hover:to-amber-300 transition-all duration-200 shadow-xl shadow-amber-500/20 active:scale-[0.99] disabled:opacity-50 text-base"
              >
                {loading ? 'Running AI Engine & Research Pipeline...' : '✦ Analyze MVP Idea Now'}
              </button>
            </form>
          ) : (
            /* Mode 2: Detailed Form */
            <form onSubmit={handleAnalyzeForm} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Idea Name *</label>
                  <input
                    type="text"
                    value={idea.name}
                    onChange={update('name')}
                    placeholder="e.g. LegalMind Local"
                    className="input-field"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Target Customer *</label>
                  <input
                    type="text"
                    value={idea.target_customer}
                    onChange={update('target_customer')}
                    placeholder="e.g. Solo law firms (1-20 attorneys)"
                    className="input-field"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-gray-200">Short Description *</label>
                <input
                  type="text"
                  value={idea.description}
                  onChange={update('description')}
                  placeholder="e.g. On-device AI meeting summarizer for law practices"
                  className="input-field"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-gray-200">Problem Solved *</label>
                <textarea
                  rows={3}
                  value={idea.problem}
                  onChange={update('problem')}
                  placeholder="What problem does this solve? Why is current alternative broken?"
                  className="textarea-field"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Target Geography *</label>
                  <input
                    type="text"
                    value={idea.geography}
                    onChange={update('geography')}
                    placeholder="e.g. United States"
                    className="input-field"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Expected Pricing</label>
                  <input
                    type="text"
                    value={idea.price}
                    onChange={update('price')}
                    placeholder="e.g. $49/mo per seat"
                    className="input-field"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Budget / Runway</label>
                  <input
                    type="text"
                    value={idea.budget}
                    onChange={update('budget')}
                    placeholder="e.g. $15,000 for 6 months"
                    className="input-field"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Known Competitors</label>
                  <input
                    type="text"
                    value={idea.known_competitors}
                    onChange={update('known_competitors')}
                    placeholder="e.g. Otter.ai, Fireflies.ai"
                    className="input-field"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-gray-200">Unfair Advantage / Moat</label>
                  <input
                    type="text"
                    value={idea.unfair_advantage}
                    onChange={update('unfair_advantage')}
                    placeholder="e.g. Local NPU acceleration engine"
                    className="input-field"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-amber-500 to-amber-400 text-black font-extrabold rounded-2xl hover:from-amber-400 hover:to-amber-300 transition-all duration-200 shadow-xl shadow-amber-500/20 active:scale-[0.99] disabled:opacity-50 text-base"
              >
                {loading ? 'Running AI Engine & Research Pipeline...' : '✦ Analyze MVP Idea Now'}
              </button>
            </form>
          )}
        </div>
      </main>

      {/* Modals */}
      <SavedAnalysesModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onCountUpdate={(cnt) => setHistoryCount(cnt)}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSave={(newSettings) => setAiSettings(newSettings)}
      />
    </div>
  )
}

export default HomePage
