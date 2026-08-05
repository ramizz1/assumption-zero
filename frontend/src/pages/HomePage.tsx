import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { IdeaInput } from '../types'
import DisclaimerBanner from '../components/DisclaimerBanner'

const EMPTY_IDEA: IdeaInput = {
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
  additional_context: '',
}

const AI_PROVIDERS = [
  { value: 'beta', label: '✦ Assumption Zero Beta AI', description: 'Built-in AI — ready to use, no key required' },
  { value: 'mock', label: 'Template Analysis', description: 'Heuristic scoring from real research data (offline)' },
  { value: 'ollama', label: 'Ollama (local model)', description: 'Self-hosted, requires Ollama running locally' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const [idea, setIdea] = useState<IdeaInput>(EMPTY_IDEA)
  const [aiProvider, setAiProvider] = useState('beta')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const update = (field: keyof IdeaInput) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => setIdea((prev) => ({ ...prev, [field]: e.target.value }))

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!idea.problem || !idea.target_customer || !idea.geography) {
      setError('Problem, target customer, and geography are required.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const result = await api.createAnalysis({
        idea,
        ai_provider: aiProvider,
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
            href="https://github.com/assumption-zero/assumption-zero"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            GitHub →
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className="text-center px-6 pt-16 pb-12 border-b border-[#1f1f26]">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-amber-400/5 border border-amber-400/15 rounded-full px-4 py-1.5 text-xs text-amber-400/70 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            Beta AI built-in · No signup · Real research
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
          <p className="text-sm text-gray-500 max-w-2xl mx-auto">
            Research competitors, challenge assumptions and design real validation experiments
            using source-backed analysis and multiple AI perspectives.
          </p>
          <p className="text-xs text-amber-500/70 mt-4 font-medium">
            This is not a success predictor. Every claim is backed by evidence.
          </p>
        </div>
      </section>

      {/* Main content */}
      <main className="flex-1 px-6 py-10">
        <div className="max-w-4xl mx-auto">
          {error && (
            <div className="mb-6 p-4 bg-red-400/10 border border-red-500/30 rounded-lg text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Step-by-Step Guidance Banner */}
          <div className="mb-6 p-5 bg-amber-400/5 border border-amber-400/20 rounded-xl text-sm text-gray-300">
            <div className="flex items-center gap-2 text-amber-400 font-bold mb-2 text-base">
              <span>💡</span> Step-by-Step Guide for Best Analysis Results
            </div>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-gray-400">
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">1.</span>
                <span><strong className="text-gray-200">Be Specific:</strong> State your exact target customer (e.g. <em>"Solo law firms in Azerbaijan"</em>).</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">2.</span>
                <span><strong className="text-gray-200">Explain the Pain:</strong> Describe what fails today & how customers solve it manually.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">3.</span>
                <span><strong className="text-gray-200">Name Competitors:</strong> List known competitors or alternatives (e.g. <em>"tap.az, lalafo.az"</em>).</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">4.</span>
                <span><strong className="text-gray-200">State Budget & Skills:</strong> Give your technical skills & budget for accurate fit scoring.</span>
              </li>
            </ul>
          </div>

          <form onSubmit={handleAnalyze} className="space-y-6">
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
                    placeholder="One sentence description"
                    value={idea.description}
                    onChange={update('description')}
                    required
                    maxLength={2000}
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="label" htmlFor="idea-problem">
                  Problem Being Solved{' '}
                  <span className="text-red-400 font-normal">(required)</span>
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
                    Target Customer{' '}
                    <span className="text-red-400 font-normal">(required)</span>
                  </label>
                  <input
                    id="idea-customer"
                    className="input-field"
                    placeholder="e.g. Solo law firm attorneys in the US"
                    value={idea.target_customer}
                    onChange={update('target_customer')}
                    required
                    maxLength={500}
                  />
                </div>
                <div>
                  <label className="label" htmlFor="idea-geography">
                    Target Geography{' '}
                    <span className="text-red-400 font-normal">(required)</span>
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

            {/* Business details */}
            <div className="card p-6">
              <h2 className="section-title">Business Details <span className="text-gray-600 font-normal text-sm">(optional)</span></h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="idea-model">Business Model</label>
                  <input id="idea-model" className="input-field" placeholder="e.g. SaaS, marketplace, consulting"
                    value={idea.business_model} onChange={update('business_model')} maxLength={500} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-price">Expected Price</label>
                  <input id="idea-price" className="input-field" placeholder="e.g. $49/month per seat"
                    value={idea.price} onChange={update('price')} maxLength={200} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-skills">Founder Skills</label>
                  <input id="idea-skills" className="input-field" placeholder="e.g. Full-stack developer, ex-lawyer"
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
              </div>
              <div className="mt-4">
                <label className="label" htmlFor="idea-context">Additional Context</label>
                <textarea id="idea-context" className="textarea-field" rows={2}
                  placeholder="Any other relevant context (tech stack, target market niche, etc.)"
                  value={idea.additional_context} onChange={update('additional_context')} maxLength={3000} />
              </div>
            </div>

            {/* AI Provider */}
            <div className="card p-6">
              <h2 className="section-title">AI Provider</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {AI_PROVIDERS.map((p) => (
                  <label
                    key={p.value}
                    htmlFor={`provider-${p.value}`}
                    className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors ${aiProvider === p.value
                        ? 'border-amber-400/50 bg-amber-400/5'
                        : 'border-[#2a2a35] hover:border-gray-600'
                      }`}
                  >
                    <input
                      type="radio"
                      id={`provider-${p.value}`}
                      name="ai_provider"
                      value={p.value}
                      checked={aiProvider === p.value}
                      onChange={() => setAiProvider(p.value)}
                      className="mt-0.5 accent-amber-400"
                    />
                    <div>
                      <p className="text-sm font-medium text-white">{p.label}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{p.description}</p>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-600 mt-3">
                Beta AI uses a built-in shared key — great for trying the app.
                Self-host with Ollama for full privacy and unlimited use.
              </p>
            </div>

            {/* Privacy note */}
            <p className="text-xs text-gray-600 text-center">
              Your idea is analyzed server-side and stored locally in SQLite.
              No data is sent to third parties except the configured AI provider and research APIs.
              Results are never published.
            </p>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                type="submit"
                id="analyze-btn"
                disabled={loading}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Starting analysis…' : '→ Analyze My Idea'}
              </button>
              <button
                type="button"
                id="demo-btn"
                onClick={handleDemo}
                disabled={loading}
                className="btn-ghost disabled:opacity-50"
              >
                Run Example Analysis
              </button>
            </div>
          </form>
        </div>
      </main>

      <DisclaimerBanner />
    </div>
  )
}
