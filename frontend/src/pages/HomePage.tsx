import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import SavedAnalysesModal from '../components/SavedAnalysesModal'
import SettingsModal, { getStoredAISettings, AISettings } from '../components/SettingsModal'
import ProviderIcon from '../components/ProviderIcon'
import { assessFormReadiness, assessPromptReadiness, type ReadinessResult } from '../lib/readiness'

// SVG Icons
const LucideGlobe = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
const LucideBrain = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>
const LucideTarget = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
const LucideFlask = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 2v7.31"/><path d="M14 9.3V11.99"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/><path d="M5.52 16h12.96"/></svg>
const LucideSparkles = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M3 5h4"/></svg>
const LucideCode = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
const LucideZap = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
const LucideBot = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="14" x="3" y="7" rx="2" ry="2"/><path d="M12 3v4"/><path d="M8 3h8"/><path d="M15 12v.01"/><path d="M9 12v.01"/></svg>
const LucideCloud = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>

const ReadinessPanel = ({ readiness }: { readiness: ReadinessResult }) => {
  const missing = readiness.checks.filter((check) => !check.complete)
  const tone = readiness.score >= 80 ? 'emerald' : readiness.score >= 60 ? 'amber' : 'zinc'
  const colors = {
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-900',
    amber: 'bg-amber-50 border-amber-200 text-amber-900',
    zinc: 'bg-zinc-50 border-zinc-200 text-zinc-800',
  }[tone]

  return (
    <div className={`rounded-2xl border p-4 ${colors}`} aria-live="polite">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div>
          <p className="text-xs font-mono font-bold uppercase tracking-wider">Idea brief strength</p>
          <p className="text-[11px] opacity-70 mt-0.5">Better context produces more useful research and experiments.</p>
        </div>
        <span className="text-lg font-black tabular-nums">{readiness.score}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/80 overflow-hidden border border-black/5 mb-3">
        <div className="h-full bg-current transition-all duration-300" style={{ width: `${readiness.score}%` }} />
      </div>
      <div className="flex flex-wrap gap-2">
        {readiness.checks.map((check) => (
          <span
            key={check.id}
            title={check.complete ? `${check.label} included` : check.hint}
            className={`text-[10px] font-mono font-bold px-2 py-1 rounded-lg border ${
              check.complete ? 'bg-white/80 border-current/10' : 'bg-white border-dashed border-current/30 opacity-70'
            }`}
          >
            {check.complete ? '✓' : '+'} {check.label}
          </span>
        ))}
      </div>
      {missing.length > 0 && (
        <p className="text-[11px] mt-3 leading-relaxed"><strong>Best next improvement:</strong> {missing[0].hint}</p>
      )}
    </div>
  )
}

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
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')

  const [aiSettings, setAiSettings] = useState<AISettings>(getStoredAISettings())
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
    let active = true
    const checkBackend = () => {
      api.health()
        .then(() => active && setBackendStatus('online'))
        .catch(() => active && setBackendStatus('offline'))
    }
    checkBackend()
    const healthInterval = window.setInterval(checkBackend, 15_000)
    return () => {
      active = false
      window.clearInterval(healthInterval)
    }
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
      const provider = aiSettings.provider === 'custom' ? 'openai_compat' : aiSettings.provider
      const result = await api.createAnalysisFromPrompt({
        prompt: rawPromptText,
        ai_provider: provider,
        groq_api_key: aiSettings.groqKey || undefined,
        openrouter_api_key: aiSettings.openrouterKey || undefined,
        opencode_api_key: aiSettings.opencodeKey || undefined,
        openai_api_key: (provider === 'openai_compat') ? (aiSettings.customKey || aiSettings.openaiKey || undefined) : (aiSettings.openaiKey || undefined),
        custom_base_url: (provider === 'openai_compat') ? (aiSettings.customUrl || undefined) : undefined,
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
      const provider = aiSettings.provider === 'custom' ? 'openai_compat' : aiSettings.provider
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
        ai_provider: provider,
        groq_api_key: aiSettings.groqKey || undefined,
        openrouter_api_key: aiSettings.openrouterKey || undefined,
        opencode_api_key: aiSettings.opencodeKey || undefined,
        openai_api_key: (provider === 'openai_compat') ? (aiSettings.customKey || aiSettings.openaiKey || undefined) : (aiSettings.openaiKey || undefined),
        custom_base_url: (provider === 'openai_compat') ? (aiSettings.customUrl || undefined) : undefined,
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

  const readiness = inputMode === 'prompt'
    ? assessPromptReadiness(rawPromptText)
    : assessFormReadiness(idea)

  return (
    <div className="min-h-screen flex flex-col verseo-grid text-zinc-900 selection:bg-zinc-200" style={{backgroundColor: '#ffffff'}}>
      {/* Header */}
      <header className="relative z-20 border-b px-6 py-4" style={{borderColor: '#e4e4e7', backgroundColor: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(20px)'}}>
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl border overflow-hidden flex items-center justify-center" style={{borderColor: '#e4e4e7', backgroundColor: '#f4f4f5'}}>
              <img src="/logo.png" alt="Assumption Zero Logo" className="w-full h-full object-cover" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold tracking-tight text-base" style={{color: '#18181b'}}>Assumption Zero</span>
                <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-full" style={{color: '#52525b', backgroundColor: '#f4f4f5', border: '1px solid #e4e4e7'}}>
                  v0.1.0
                </span>
              </div>
              <p className="text-[11px] font-mono hidden sm:block" style={{color: '#a1a1aa'}}>
                [ OPEN-SOURCE MVP VALIDATION ENGINE ]
              </p>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center gap-3">
            <span
              className={`hidden md:inline-flex items-center gap-1.5 text-[10px] font-mono font-bold px-2 py-1 rounded-full border ${
                backendStatus === 'online'
                  ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                  : backendStatus === 'offline'
                  ? 'text-red-700 bg-red-50 border-red-200'
                  : 'text-zinc-500 bg-zinc-50 border-zinc-200'
              }`}
              title={backendStatus === 'offline' ? 'The API is unreachable. Start the backend before analyzing.' : 'Backend status'}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === 'online' ? 'bg-emerald-500' : backendStatus === 'offline' ? 'bg-red-500' : 'bg-zinc-400 animate-pulse'}`} />
              API {backendStatus}
            </span>
            <button
              onClick={() => setIsHistoryOpen(true)}
              className="px-3.5 py-1.5 rounded-xl border text-xs font-mono font-medium transition-all flex items-center gap-2 shadow-sm hover:bg-zinc-50"
              style={{borderColor: '#e4e4e7', backgroundColor: '#fafafa', color: '#52525b'}}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
              <span>History</span>
              {historyCount !== null && (
                <span className="px-1.5 py-0.5 rounded-md text-[10px] font-bold" style={{backgroundColor: '#f4f4f5', color: '#52525b', border: '1px solid #e4e4e7'}}>
                  {historyCount}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              className="px-3.5 py-1.5 rounded-xl border text-xs font-mono font-medium transition-all flex items-center gap-1.5 shadow-sm hover:bg-zinc-50"
              style={{borderColor: '#e4e4e7', backgroundColor: '#fafafa', color: '#52525b'}}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <span>AI Setup</span>
            </button>

            <div className="flex items-center gap-2 ml-2" title="Creator Profile">
              <img src="/avatar.jpg" alt="Avatar" className="w-8 h-8 rounded-full border object-cover" style={{borderColor: '#e4e4e7'}} />
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 text-center px-6 pt-16 pb-12 border-b" style={{borderColor: '#e4e4e7'}}>
        <div className="max-w-4xl mx-auto space-y-5">
          <div className="inline-flex items-center gap-2 verseo-badge shadow-sm">
            <span className="w-2 h-2 rounded-full animate-pulse" style={{backgroundColor: '#18181b'}} />
            <span>[ ✦ MULTI-SOURCE LIVE RESEARCH · 3 AI PERSPECTIVES · DETERMINISTIC SCORING ]</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-black tracking-tight leading-[1.1]" style={{color: '#09090b'}}>
            Stress-test your MVP idea <br />
            <span style={{color: '#52525b'}}>
              before you build it.
            </span>
          </h1>

          <p className="text-base sm:text-lg max-w-2xl mx-auto font-normal leading-relaxed" style={{color: '#71717a'}}>
            Assumption Zero evaluates startup ideas against primary web research, identifies competitor complaints, challenges moat assumptions, and crafts 7-day validation experiments.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <main className="relative z-10 flex-1 px-4 sm:px-6 py-10 max-w-5xl mx-auto w-full space-y-12">
        {error && (
          <div className="p-5 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-start gap-3 shadow-sm backdrop-blur-md">
            <span className="text-xl">⚠️</span>
            <div className="flex-1 space-y-1">
              <h4 className="font-bold text-red-800 text-sm">
                {error.includes('gibberish')
                  ? 'Invalid Startup Idea Prompt'
                  : error.includes('402') || error.includes('429') || error.includes('quota')
                  ? 'No AI Tokens Available (Quota Exceeded)'
                  : 'Analysis Request Failed'}
              </h4>
              <p className="text-xs text-red-600 leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {/* Verseo Input Card Container */}
        <div className="verseo-card p-6 sm:p-8 backdrop-blur-xl shadow-md">
          {/* Corner Crosshairs */}
          <span className="verseo-corner-tl">+</span>
          <span className="verseo-corner-tr">+</span>
          <span className="verseo-corner-bl">+</span>
          <span className="verseo-corner-br">+</span>

          {/* Mode Switcher Tabs */}
          <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-6 flex-wrap gap-4">
            <div className="flex bg-gray-100 p-1.5 rounded-2xl border border-gray-200 gap-1">
              <button
                type="button"
                onClick={() => setInputMode('prompt')}
                className={`py-2 px-4 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-2 ${
                  inputMode === 'prompt'
                    ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-white/50'
                }`}
              >
                <LucideZap /> 1-Prompt Mode
              </button>

              <button
                type="button"
                onClick={() => setInputMode('form')}
                className={`py-2 px-4 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-2 ${
                  inputMode === 'form'
                    ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-white/50'
                }`}
              >
                <LucideCode /> Form Wizard
              </button>
            </div>

            {/* Quick Sample Action */}
            <button
              type="button"
              onClick={handleLoadSample}
              className="text-xs font-mono text-gray-600 hover:text-gray-900 font-semibold px-3 py-1.5 rounded-xl border border-gray-200 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center gap-1.5"
            >
              <LucideSparkles /> [ Load Sample Idea ]
            </button>
          </div>

          {/* AI Provider Selector Pills */}
          <div className="mb-6 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono" style={{color: '#71717a'}}>
              <span className="font-semibold">[ AI PROVIDER ]</span>
              <button
                type="button"
                onClick={() => setIsSettingsOpen(true)}
                className="hover:underline flex items-center gap-1"
                style={{color: '#52525b'}}
              >
                Configure Keys
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              </button>
            </div>
            <div className="flex flex-wrap gap-2 text-xs font-mono">
              {[
                { id: 'auto', label: 'Auto' },
                { id: 'ollama', label: 'Ollama' },
                { id: 'opencode', label: 'OpenCode' },
                { id: 'openai_compat', label: 'OpenAI' },
                { id: 'groq', label: 'Groq (L3)' },
                { id: 'openrouter', label: 'OpenRouter' },
                { id: 'custom', label: 'Custom' },
              ].map((p) => {
                const isActive = aiSettings.provider === p.id
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setAiSettings({ ...aiSettings, provider: p.id as AISettings['provider'] })}
                    className="px-3 py-1.5 rounded-xl border font-medium flex items-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
                    style={{
                      background: isActive ? '#18181b' : '#fafafa',
                      borderColor: isActive ? '#18181b' : '#e4e4e7',
                      color: isActive ? '#ffffff' : '#71717a',
                      boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.15)' : 'none',
                    }}
                  >
                    <ProviderIcon id={p.id} isActive={isActive} size="sm" />
                    {p.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Mode 1: Natural Language Prompt */}
          {inputMode === 'prompt' ? (
            <form onSubmit={handleAnalyzePrompt} className="space-y-6">
              <div className="space-y-2">
                <label className="label">
                  Describe Your Startup or Product Idea
                </label>
                <p className="text-xs text-gray-500">
                  Describe what you're building, target audience, problem solved, pricing, or competitors in plain natural text.
                </p>

                <textarea
                  rows={6}
                  value={rawPromptText}
                  onChange={(e) => setRawPromptText(e.target.value)}
                  placeholder="e.g. LegalMind Local — A privacy-first AI meeting summarizer for small law firms that processes audio entirely on-device. Pricing: $49/mo per seat. Target: Solo practitioners and small firms in the US..."
                  className="w-full bg-gray-50 border border-gray-200 rounded-2xl p-4 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-gray-400 focus:ring-1 focus:ring-gray-200 transition-all resize-y shadow-inner"
                  required
                  minLength={20}
                  maxLength={5000}
                />
              </div>

              {/* Upload file helper */}
              <div className="flex items-center justify-between text-xs font-mono text-gray-500 flex-wrap gap-2">
                <label className="cursor-pointer hover:text-gray-900 transition-colors flex items-center gap-1.5 bg-white border border-gray-200 px-3 py-1.5 rounded-xl shadow-sm">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                  Upload .txt or .json
                  <input type="file" accept=".txt,.json,.md" onChange={handleFileUpload} className="hidden" />
                </label>

                <span className="text-gray-500">{rawPromptText.length.toLocaleString()} / 5,000 chars</span>
              </div>

              <ReadinessPanel readiness={readiness} />

              <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                <button
                  type="submit"
                  disabled={loading || rawPromptText.trim().length < 20 || backendStatus === 'offline'}
                  className="btn-primary w-full py-4 text-base flex justify-center items-center gap-2"
                >
                  {loading ? 'Running AI Engine & Live Research...' : <><LucideSparkles /> Analyze MVP Idea Now</>}
                </button>
                <button type="button" onClick={handleDemo} disabled={loading || backendStatus === 'offline'} className="btn-ghost px-5 py-4">
                  Run example
                </button>
              </div>
            </form>
          ) : (
            /* Mode 2: Detailed Form */
            <form onSubmit={handleAnalyzeForm} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="label">Idea Name *</label>
                  <input
                    type="text"
                    value={idea.name}
                    onChange={update('name')}
                    placeholder="e.g. LegalMind Local"
                    className="input-field shadow-inner"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="label">Target Customer *</label>
                  <input
                    type="text"
                    value={idea.target_customer}
                    onChange={update('target_customer')}
                    placeholder="e.g. Solo law firms (1-20 attorneys)"
                    className="input-field shadow-inner"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="label">Short Description *</label>
                <input
                  type="text"
                  value={idea.description}
                  onChange={update('description')}
                  placeholder="e.g. On-device AI meeting summarizer for law practices"
                  className="input-field shadow-inner"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="label">Problem Solved *</label>
                <textarea
                  rows={3}
                  value={idea.problem}
                  onChange={update('problem')}
                  placeholder="What problem does this solve? Why is current alternative broken?"
                  className="textarea-field shadow-inner"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="label">Target Geography *</label>
                  <input
                    type="text"
                    value={idea.geography}
                    onChange={update('geography')}
                    placeholder="e.g. United States"
                    className="input-field shadow-inner"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="label">Expected Pricing</label>
                  <input
                    type="text"
                    value={idea.price}
                    onChange={update('price')}
                    placeholder="e.g. $49/mo per seat"
                    className="input-field shadow-inner"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="label">Budget / Runway</label>
                  <input
                    type="text"
                    value={idea.budget}
                    onChange={update('budget')}
                    placeholder="e.g. $15,000 for 6 months"
                    className="input-field shadow-inner"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="label">Known Competitors</label>
                  <input
                    type="text"
                    value={idea.known_competitors}
                    onChange={update('known_competitors')}
                    placeholder="e.g. Otter.ai, Fireflies.ai"
                    className="input-field shadow-inner"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="label">Unfair Advantage / Moat</label>
                  <input
                    type="text"
                    value={idea.unfair_advantage}
                    onChange={update('unfair_advantage')}
                    placeholder="e.g. Local NPU acceleration engine"
                    className="input-field shadow-inner"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="label">Business Model</label>
                  <input
                    type="text"
                    value={idea.business_model}
                    onChange={update('business_model')}
                    placeholder="e.g. Per-seat SaaS subscription"
                    className="input-field shadow-inner"
                    maxLength={500}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="label">Founder / Team Fit</label>
                  <input
                    type="text"
                    value={idea.founder_skills}
                    onChange={update('founder_skills')}
                    placeholder="e.g. Full-stack engineer, 5 years in legal tech"
                    className="input-field shadow-inner"
                    maxLength={1000}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="label">Critical Assumptions</label>
                <textarea
                  rows={2}
                  value={idea.key_assumptions}
                  onChange={update('key_assumptions')}
                  placeholder="What must be true for this idea to work?"
                  className="textarea-field shadow-inner"
                  maxLength={1000}
                />
              </div>

              <div className="space-y-1.5">
                <label className="label">Additional Context</label>
                <textarea
                  rows={3}
                  value={idea.additional_context}
                  onChange={update('additional_context')}
                  placeholder="Existing traction, planned channels, constraints, research, or customer conversations"
                  className="textarea-field shadow-inner"
                  maxLength={3000}
                />
              </div>

              <ReadinessPanel readiness={readiness} />

              <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                <button
                  type="submit"
                  disabled={loading || backendStatus === 'offline'}
                  className="btn-primary w-full py-4 text-base flex justify-center items-center gap-2"
                >
                  {loading ? 'Running AI Engine & Live Research...' : <><LucideSparkles /> Analyze MVP Idea Now</>}
                </button>
                <button type="button" onClick={handleDemo} disabled={loading || backendStatus === 'offline'} className="btn-ghost px-5 py-4">
                  Run example
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Verseo Bento Grid — 4 Core Feature Cards */}
        <section className="space-y-6 pt-4">
          <div className="text-center space-y-2">
            <span className="verseo-badge">[ ✦ HOW IT WORKS ]</span>
            <h2 className="text-3xl font-display font-black text-gray-900 tracking-tight">
              Source-backed MVP evaluation pipeline.
            </h2>
            <p className="text-sm text-gray-500 max-w-lg mx-auto">
              Automated research and multi-perspectives designed to eliminate founder bias.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Bento Card 1: Live Market & Web Research */}
            <div className="verseo-card-hover p-6 flex flex-col justify-between group">
              <span className="verseo-corner-tl">+</span>
              <span className="verseo-corner-tr">+</span>
              <span className="verseo-corner-bl">+</span>
              <span className="verseo-corner-br">+</span>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 group-hover:bg-gray-900 group-hover:text-white transition-colors duration-300">
                  <LucideGlobe />
                </div>
                <h3 className="text-lg font-display font-bold text-gray-900">Live Multi-Source Research</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Queries primary web sources across GitHub, HackerNews, Wikipedia, Reddit, and SearXNG to gather live competitor complaints, pricing models, and market demand.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2 font-mono text-[11px] text-gray-400">
                <span>[ GitHub · HN · Reddit · SearXNG ]</span>
              </div>
            </div>

            {/* Bento Card 2: 3 Independent AI Perspectives */}
            <div className="verseo-card-hover p-6 flex flex-col justify-between group">
              <span className="verseo-corner-tl">+</span>
              <span className="verseo-corner-tr">+</span>
              <span className="verseo-corner-bl">+</span>
              <span className="verseo-corner-br">+</span>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 group-hover:bg-gray-900 group-hover:text-white transition-colors duration-300">
                  <LucideBrain />
                </div>
                <h3 className="text-lg font-display font-bold text-gray-900">3 AI Agent Perspectives</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Evaluates your idea simultaneously through three distinct lenses: <strong>Market Analyst</strong> (sizing), <strong>Skeptical VC Investor</strong> (moat risks), and <strong>Practical Builder</strong> (90-day roadmap).
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2 font-mono text-[11px] text-gray-400">
                <span>[ Analyst · VC Skeptic · Builder ]</span>
              </div>
            </div>

            {/* Bento Card 3: Deterministic Opportunity Gauge */}
            <div className="verseo-card-hover p-6 flex flex-col justify-between group">
              <span className="verseo-corner-tl">+</span>
              <span className="verseo-corner-tr">+</span>
              <span className="verseo-corner-bl">+</span>
              <span className="verseo-corner-br">+</span>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 group-hover:bg-gray-900 group-hover:text-white transition-colors duration-300">
                  <LucideTarget />
                </div>
                <h3 className="text-lg font-display font-bold text-gray-900">Deterministic Scoring Engine</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Computes an objective 0–100 opportunity score weighing execution difficulty, competitor saturation, founder skills, pricing sustainability, and evidence confidence.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2 font-mono text-[11px] text-gray-400">
                <span>[ Build · Test First · Pivot · Avoid ]</span>
              </div>
            </div>

            {/* Bento Card 4: 7-Day Validation Experiments */}
            <div className="verseo-card-hover p-6 flex flex-col justify-between group">
              <span className="verseo-corner-tl">+</span>
              <span className="verseo-corner-tr">+</span>
              <span className="verseo-corner-bl">+</span>
              <span className="verseo-corner-br">+</span>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 group-hover:bg-gray-900 group-hover:text-white transition-colors duration-300">
                  <LucideFlask />
                </div>
                <h3 className="text-lg font-display font-bold text-gray-900">7-Day Validation Experiments</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Generates low-cost, high-velocity micro-experiments with clear success metrics so you can validate customer demand before writing code.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2 font-mono text-[11px] text-gray-400">
                <span>[ Actionable Test Plans ]</span>
              </div>
            </div>
          </div>
        </section>
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
