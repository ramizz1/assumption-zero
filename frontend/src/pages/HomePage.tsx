import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

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
  const [selectedProvider, setSelectedProvider] = useState<'groq' | 'openrouter'>('groq')
  const [groqApiKey, setGroqApiKey] = useState('')
  const [openrouterApiKey, setOpenrouterApiKey] = useState('')
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
      const result = await api.createAnalysisFromPrompt({
        prompt: rawPromptText,
        ai_provider: selectedProvider,
        groq_api_key: selectedProvider === 'groq' ? (groqApiKey || undefined) : undefined,
        openrouter_api_key: selectedProvider === 'openrouter' ? (openrouterApiKey || undefined) : undefined,
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
        ai_provider_override: selectedProvider,
        groq_api_key: selectedProvider === 'groq' ? (groqApiKey || undefined) : undefined,
        openrouter_api_key: selectedProvider === 'openrouter' ? (openrouterApiKey || undefined) : undefined,
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
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-[#1f1f26] px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">A0</span>
              <span className="font-bold text-white">Assumption Zero</span>
              <span className="text-[10px] font-semibold text-amber-400/80 bg-amber-400/10 border border-amber-400/20 px-1.5 py-0.5 rounded-full">BETA</span>
            </div>
            <p className="text-xs text-gray-600 mt-0.5">Open-source MVP validation · AI built-in</p>
          </div>
          <a
            href="https://github.com/ramizz1/assumption-zero"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            GitHub →
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className="text-center px-6 pt-12 pb-10 border-b border-[#1f1f26]">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-amber-400/5 border border-amber-400/15 rounded-full px-4 py-1.5 text-xs text-amber-400/70 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            Beta AI built-in · OpenRouter · Real Web Research
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            Assumption Zero
          </h1>
          <p className="text-xl text-gray-400 font-medium mb-3">
            The open-source MVP validation engine.
          </p>
          <p className="text-lg text-gray-500 mb-6">
            Stress-test your idea before you build it.
          </p>
        </div>
      </section>

      {/* Main content */}
      <main className="flex-1 px-6 py-10">
        <div className="max-w-4xl mx-auto">
          {error && (
            <div className="mb-6 p-4 sm:p-5 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 flex items-start gap-3">
              <span className="text-xl leading-none mt-0.5">⚠️</span>
              <div className="flex-1">
                <h4 className="font-bold text-red-400 text-sm mb-1">
                  {error.includes('gibberish')
                    ? 'Invalid Startup Idea Prompt'
                    : error.includes('402') || error.includes('429') || error.includes('quota') || error.includes('token') || error.includes('credit')
                    ? 'No AI Tokens Available Today (Quota / Rate Limit Exceeded)'
                    : 'Analysis Error'}
                </h4>
                <p className="text-xs text-red-300/90 leading-relaxed">{error}</p>
                {(error.includes('402') || error.includes('429') || error.includes('quota') || error.includes('token') || error.includes('credit')) && (
                  <p className="text-xs text-amber-300/90 mt-2 bg-amber-400/10 border border-amber-400/20 p-2.5 rounded-lg">
                    💡 <strong>How to fix:</strong> Provide your personal OpenRouter key below under <em>"Custom OpenRouter API Key"</em> or set <code className="bg-black/50 px-1 py-0.5 rounded text-amber-200">OPENROUTER_API_KEY</code> in backend <code className="bg-black/50 px-1 py-0.5 rounded text-amber-200">.env</code>.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Mode Switcher Tabs */}
          <div className="flex border-b border-[#2a2a35] mb-6">
            <button
              type="button"
              onClick={() => setInputMode('prompt')}
              className={`py-3 px-6 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                inputMode === 'prompt'
                  ? 'border-amber-400 text-amber-400 bg-amber-400/5'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>⚡</span> 1-Prompt Quick Mode (AI Analyzes Text First)
            </button>
            <button
              type="button"
              onClick={() => setInputMode('form')}
              className={`py-3 px-6 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                inputMode === 'form'
                  ? 'border-amber-400 text-amber-400 bg-amber-400/5'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>📋</span> Detailed Form Fields
            </button>
          </div>

          {/* Action toolbar */}
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 p-4 bg-[#141419] border border-[#2a2a35] rounded-xl">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className="font-semibold text-white">Quick Actions:</span>
              <span>Need test data?</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleLoadSample}
                className="px-3 py-1.5 bg-amber-400/10 hover:bg-amber-400/20 text-amber-400 border border-amber-400/30 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <span>⚡</span> Load Sample Idea Data
              </button>
              <button
                type="button"
                onClick={() => setShowJsonExample(!showJsonExample)}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <span>📄</span> {showJsonExample ? 'Hide JSON Format' : 'View JSON Format Example'}
              </button>
            </div>
          </div>

          {/* JSON Example Card */}
          {showJsonExample && (
            <div className="mb-6 p-5 bg-[#0f0f14] border border-amber-400/30 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">JSON File Format Example</span>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(SAMPLE_IDEA, null, 2))}
                  className="text-xs text-amber-400 hover:text-amber-300 underline"
                >
                  Copy JSON to Clipboard
                </button>
              </div>
              <pre className="text-xs font-mono text-gray-300 bg-[#0a0a0d] p-4 rounded-lg overflow-x-auto border border-[#1f1f26]">
                {JSON.stringify(SAMPLE_IDEA, null, 2)}
              </pre>
            </div>
          )}

          {/* 1-PROMPT MODE */}
          {inputMode === 'prompt' && (
            <form onSubmit={handleAnalyzePrompt} className="space-y-6">
              <div className="card p-6 border-amber-400/30">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="section-title mb-0">⚡ 1-Prompt Idea Analyzer</h2>
                  <span className="text-xs text-amber-400 font-semibold bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded">
                    AI Auto-Extraction Mode
                  </span>
                </div>
                <p className="text-xs text-gray-400 mb-4">
                  Describe your idea in natural plain English (product name, problem, customer, business model, price, budget, competitors). AI will first extract all structured parameters, then run live web research & business analysis.
                </p>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="label mb-0" htmlFor="raw-prompt">Your Startup / Product Idea Prompt</label>
                    <label className="cursor-pointer text-xs text-amber-400 hover:text-amber-300 font-semibold bg-amber-400/10 border border-amber-400/30 px-3 py-1 rounded-lg flex items-center gap-1.5 transition-colors">
                      <span>📁</span> Upload .txt / .md File
                      <input
                        type="file"
                        accept=".txt,.md,.json"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                    </label>
                  </div>
                  <textarea
                    id="raw-prompt"
                    className="textarea-field font-sans text-sm"
                    rows={8}
                    placeholder="Describe your startup idea in plain English or upload a .txt / .md file... e.g. LegalMind Local: an AI meeting summarizer for law firms that processes audio entirely on-device, $49/mo subscription model, target customers are solo law practices..."
                    value={rawPromptText}
                    onChange={(e) => setRawPromptText(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* AI Provider & API Key Setup */}
              <div className="card p-6 border-amber-400/20 bg-[#141419]/90">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>⚡</span> Select AI Provider & API Key
                  </h3>
                  <span className="text-[11px] text-amber-400/90 font-mono font-semibold">Zero-config built-in key active</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                  <button
                    type="button"
                    onClick={() => setSelectedProvider('groq')}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      selectedProvider === 'groq'
                        ? 'border-amber-400 bg-amber-400/10 text-white shadow-sm'
                        : 'border-[#2a2a35] bg-black/40 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white flex items-center gap-1.5">
                        <span>🚀</span> Groq (Llama 3.3)
                      </span>
                      <span className="text-[10px] font-extrabold bg-amber-400/20 text-amber-300 px-2 py-0.5 rounded-full border border-amber-400/30">RECOMMENDED</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-snug">
                      200,000 free tokens/day (~20 full analyses daily)
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedProvider('openrouter')}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      selectedProvider === 'openrouter'
                        ? 'border-amber-400 bg-amber-400/10 text-white shadow-sm'
                        : 'border-[#2a2a35] bg-black/40 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white flex items-center gap-1.5">
                        <span>🌐</span> OpenRouter
                      </span>
                      <span className="text-[10px] font-bold bg-blue-400/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-400/30">200+ MODELS</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-snug">
                      Access Gemma, Llama & DeepSeek open models
                    </p>
                  </button>
                </div>

                {selectedProvider === 'groq' ? (
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-gray-300">Custom Groq API Key (Optional)</label>
                      <a
                        href="https://console.groq.com/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-amber-400 hover:text-amber-300 underline font-semibold flex items-center gap-1"
                      >
                        <span>🔑 Get Free Groq Key (console.groq.com/keys)</span>
                        <span>→</span>
                      </a>
                    </div>
                    <input
                      type="password"
                      className="input-field font-mono text-xs"
                      placeholder="gsk_... (optional, leave blank for built-in key)"
                      value={groqApiKey}
                      onChange={(e) => setGroqApiKey(e.target.value)}
                    />
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-gray-300">Custom OpenRouter API Key (Optional)</label>
                      <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-amber-400 hover:text-amber-300 underline font-semibold flex items-center gap-1"
                      >
                        <span>🔑 Get Free OpenRouter Key (openrouter.ai/keys)</span>
                        <span>→</span>
                      </a>
                    </div>
                    <input
                      type="password"
                      className="input-field font-mono text-xs"
                      placeholder="sk-or-v1-... (optional, leave blank for built-in key)"
                      value={openrouterApiKey}
                      onChange={(e) => setOpenrouterApiKey(e.target.value)}
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center gap-4 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary flex-1 py-3.5 text-base font-semibold"
                >
                  {loading ? 'AI Parsing & Stress-Testing Idea…' : '⚡ Stress-Test Idea via 1-Prompt →'}
                </button>
                <button
                  type="button"
                  onClick={handleDemo}
                  disabled={loading}
                  className="btn-secondary py-3.5 text-sm"
                >
                  Try Built-in Demo
                </button>
              </div>
            </form>
          )}

          {/* DETAILED FORM MODE */}
          {inputMode === 'form' && (
            <form onSubmit={handleAnalyzeForm} className="space-y-6">
              {/* Basic info */}
              <div className="card p-6">
                <h2 className="section-title">Your Idea</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label" htmlFor="idea-name">Idea / Product Name *</label>
                    <input
                      id="idea-name"
                      className="input-field"
                      placeholder="e.g. LegalMind Local"
                      value={idea.name}
                      onChange={update('name')}
                      required
                      maxLength={200}
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-description">Short Description *</label>
                    <input
                      id="idea-description"
                      className="input-field"
                      placeholder="One sentence description of the product"
                      value={idea.description}
                      onChange={update('description')}
                      required
                      maxLength={2000}
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="label" htmlFor="idea-problem">
                    Problem Being Solved <span className="text-red-400 font-normal">(required)</span>
                  </label>
                  <textarea
                    id="idea-problem"
                    className="textarea-field"
                    rows={3}
                    placeholder="What specific problem does this solve? Who has it and how painfully?"
                    value={idea.problem}
                    onChange={update('problem')}
                    required
                    maxLength={2000}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="label" htmlFor="idea-customer">
                      Target Customer <span className="text-red-400 font-normal">(required)</span>
                    </label>
                    <input
                      id="idea-customer"
                      className="input-field"
                      placeholder="e.g. Solo practitioners & small law firms"
                      value={idea.target_customer}
                      onChange={update('target_customer')}
                      required
                      maxLength={500}
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-geography">
                      Target Geography <span className="text-red-400 font-normal">(required)</span>
                    </label>
                    <input
                      id="idea-geography"
                      className="input-field"
                      placeholder="e.g. United States"
                      value={idea.geography}
                      onChange={update('geography')}
                      required
                      maxLength={200}
                    />
                  </div>
                </div>
              </div>

              {/* Strategic & Business details */}
              <div className="card p-6">
                <h2 className="section-title">Business & Strategic Details <span className="text-gray-600 font-normal text-sm">(optional)</span></h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label" htmlFor="idea-model">Business Model</label>
                    <input id="idea-model" className="input-field" placeholder="e.g. SaaS subscription per seat"
                      value={idea.business_model} onChange={update('business_model')} maxLength={500} />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-price">Expected Price</label>
                    <input id="idea-price" className="input-field" placeholder="e.g. $49/month per attorney seat"
                      value={idea.price} onChange={update('price')} maxLength={200} />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-skills">Founder Skills</label>
                    <input id="idea-skills" className="input-field" placeholder="e.g. Full-stack developer (Python + React)"
                      value={idea.founder_skills} onChange={update('founder_skills')} maxLength={1000} />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-budget">Available Budget / Runway</label>
                    <input id="idea-budget" className="input-field" placeholder="e.g. $15,000 for 6 months"
                      value={idea.budget} onChange={update('budget')} maxLength={200} />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-competitors">Known Competitors</label>
                    <input id="idea-competitors" className="input-field" placeholder="e.g. Otter.ai, Fireflies.ai"
                      value={idea.known_competitors} onChange={update('known_competitors')} maxLength={500} />
                  </div>
                  <div>
                    <label className="label" htmlFor="idea-advantage">Unfair Advantage / Moat</label>
                    <input id="idea-advantage" className="input-field" placeholder="e.g. Proprietary local model quantization"
                      value={idea.unfair_advantage} onChange={update('unfair_advantage')} maxLength={1000} />
                  </div>
                </div>
                <div className="mt-4">
                  <label className="label" htmlFor="idea-assumptions">Core Unvalidated Assumptions</label>
                  <input id="idea-assumptions" className="input-field" placeholder="e.g. Attorneys will pay $49/mo for on-device data privacy"
                    value={idea.key_assumptions} onChange={update('key_assumptions')} maxLength={1000} />
                </div>
              </div>

              {/* AI Provider & API Key Setup */}
              <div className="card p-6 border-amber-400/20 bg-[#141419]/90">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>⚡</span> Select AI Provider & API Key
                  </h3>
                  <span className="text-[11px] text-amber-400/90 font-mono font-semibold">Zero-config built-in key active</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                  <button
                    type="button"
                    onClick={() => setSelectedProvider('groq')}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      selectedProvider === 'groq'
                        ? 'border-amber-400 bg-amber-400/10 text-white shadow-sm'
                        : 'border-[#2a2a35] bg-black/40 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white flex items-center gap-1.5">
                        <span>🚀</span> Groq (Llama 3.3)
                      </span>
                      <span className="text-[10px] font-extrabold bg-amber-400/20 text-amber-300 px-2 py-0.5 rounded-full border border-amber-400/30">RECOMMENDED</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-snug">
                      200,000 free tokens/day (~20 full analyses daily)
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedProvider('openrouter')}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      selectedProvider === 'openrouter'
                        ? 'border-amber-400 bg-amber-400/10 text-white shadow-sm'
                        : 'border-[#2a2a35] bg-black/40 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white flex items-center gap-1.5">
                        <span>🌐</span> OpenRouter
                      </span>
                      <span className="text-[10px] font-bold bg-blue-400/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-400/30">200+ MODELS</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-snug">
                      Access Gemma, Llama & DeepSeek open models
                    </p>
                  </button>
                </div>

                {selectedProvider === 'groq' ? (
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-gray-300">Custom Groq API Key (Optional)</label>
                      <a
                        href="https://console.groq.com/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-amber-400 hover:text-amber-300 underline font-semibold flex items-center gap-1"
                      >
                        <span>🔑 Get Free Groq Key (console.groq.com/keys)</span>
                        <span>→</span>
                      </a>
                    </div>
                    <input
                      type="password"
                      className="input-field font-mono text-xs"
                      placeholder="gsk_... (optional, leave blank for built-in key)"
                      value={groqApiKey}
                      onChange={(e) => setGroqApiKey(e.target.value)}
                    />
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-gray-300">Custom OpenRouter API Key (Optional)</label>
                      <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-amber-400 hover:text-amber-300 underline font-semibold flex items-center gap-1"
                      >
                        <span>🔑 Get Free OpenRouter Key (openrouter.ai/keys)</span>
                        <span>→</span>
                      </a>
                    </div>
                    <input
                      type="password"
                      className="input-field font-mono text-xs"
                      placeholder="sk-or-v1-... (optional, leave blank for built-in key)"
                      value={openrouterApiKey}
                      onChange={(e) => setOpenrouterApiKey(e.target.value)}
                    />
                  </div>
                )}
              </div>

              {/* Submit */}
              <div className="flex items-center gap-4 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary flex-1 py-3.5 text-base font-semibold"
                >
                  {loading ? 'Starting Analysis…' : 'Stress-Test My Idea →'}
                </button>
                <button
                  type="button"
                  onClick={handleDemo}
                  disabled={loading}
                  className="btn-secondary py-3.5 text-sm"
                >
                  Try Built-in Demo
                </button>
              </div>
            </form>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1f1f26] px-6 py-6 text-center text-xs text-gray-600">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>Assumption Zero · Open-source MVP validation engine</p>
          <div className="flex items-center gap-4">
            <a href="https://github.com/ramizz1/assumption-zero" target="_blank" rel="noopener noreferrer" className="hover:text-gray-400">GitHub</a>
            <span>·</span>
            <span>MIT License</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
