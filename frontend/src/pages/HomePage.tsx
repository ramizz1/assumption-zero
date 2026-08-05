import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

const GOTUR_SAMPLE = {
  name: "Gotur.az",
  description: "P2P listing, rental, and barter marketplace in Azerbaijan connecting buyers & sellers with instant chat and boost packages",
  problem: "Local peer-to-peer sellers and small merchants in Azerbaijan face high fees, slow listing verification, and poor mobile chat experience on legacy classified platforms. Buyers lack a modern mobile-first interface with verified seller ratings and instant barter options.",
  target_customer: "Individual sellers, buyers, and local SMB merchants in Azerbaijan trading electronics, real estate, vehicles, and secondhand goods",
  geography: "Azerbaijan",
  business_model: "Freemium listing marketplace with paid VIP/Premium listing boost packages ($2 to $10) and targeted seller banner ads",
  price: "Free basic listings, $2-$10 per boost package",
  founder_skills: "Full-stack developer with experience in Vue/Nuxt.js, Python/Django REST API, and Flutter mobile development",
  budget: "$5,000 budget with 6 months runway",
  known_competitors: "tap.az, lalafo.az, boss.az, Facebook Marketplace Azerbaijan",
  unfair_advantage: "Full technical ownership (Nuxt+Django+Flutter codebase built), local market knowledge, and zero reliance on expensive agency outsourcing",
  key_assumptions: "Sellers will list on Gotur.az if chat response rate is 2x faster than tap.az and basic listings remain 100% free",
  additional_context: "Unified Django REST backend serving both Nuxt 3 web frontend and Flutter mobile apps. Integrated with local payment gateways (ePUL, MilliÖN) and Cloudflare R2 image storage."
}

export const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [customApiKey, setCustomApiKey] = useState('')
  const [showJsonExample, setShowJsonExample] = useState(false)

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
    setIdea(GOTUR_SAMPLE)
  }

  const handleAnalyze = async (e: React.FormEvent) => {
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
        ai_provider_override: 'beta',
        openrouter_api_key: customApiKey || undefined,
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
          <p className="text-sm text-gray-500 max-w-2xl mx-auto">
            Research competitors, challenge assumptions and design real validation experiments
            using source-backed analysis and multiple AI perspectives.
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

          {/* Action toolbar */}
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 p-4 bg-[#141419] border border-[#2a2a35] rounded-xl">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className="font-semibold text-white">Quick Actions:</span>
              <span>Need ready test data?</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleLoadSample}
                className="px-3 py-1.5 bg-amber-400/10 hover:bg-amber-400/20 text-amber-400 border border-amber-400/30 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <span>⚡</span> Load Gotur.az Sample Data
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
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">JSON File Format Example (for CLI --file option or API)</span>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(GOTUR_SAMPLE, null, 2))}
                  className="text-xs text-amber-400 hover:text-amber-300 underline"
                >
                  Copy JSON to Clipboard
                </button>
              </div>
              <pre className="text-xs font-mono text-gray-300 bg-[#0a0a0d] p-4 rounded-lg overflow-x-auto border border-[#1f1f26]">
                {JSON.stringify(GOTUR_SAMPLE, null, 2)}
              </pre>
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
                <span><strong className="text-gray-200">Be Specific:</strong> State exact target customer (e.g. <em>"Solo law firms in Azerbaijan"</em>).</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">2.</span>
                <span><strong className="text-gray-200">Explain the Pain:</strong> Describe what fails today & how customers solve it manually.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">3.</span>
                <span><strong className="text-gray-200">Name Competitors:</strong> List direct competitors or alternatives (e.g. <em>"tap.az, lalafo.az"</em>).</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">4.</span>
                <span><strong className="text-gray-200">State Moat & Assumptions:</strong> Include your unfair advantage and core unvalidated assumptions.</span>
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
                    placeholder="e.g. Gotur.az"
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
                    placeholder="e.g. Individual sellers & small merchants in Azerbaijan"
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
                    placeholder="e.g. Azerbaijan"
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
                  <input id="idea-model" className="input-field" placeholder="e.g. Freemium + $2-$10 boost listing packages"
                    value={idea.business_model} onChange={update('business_model')} maxLength={500} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-price">Expected Price</label>
                  <input id="idea-price" className="input-field" placeholder="e.g. Free basic listings, $5/boost package"
                    value={idea.price} onChange={update('price')} maxLength={200} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-skills">Founder Skills</label>
                  <input id="idea-skills" className="input-field" placeholder="e.g. Full-stack developer (Nuxt + Django + Flutter)"
                    value={idea.founder_skills} onChange={update('founder_skills')} maxLength={1000} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-budget">Available Budget / Runway</label>
                  <input id="idea-budget" className="input-field" placeholder="e.g. $5,000 for 6 months"
                    value={idea.budget} onChange={update('budget')} maxLength={200} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-competitors">Known Competitors</label>
                  <input id="idea-competitors" className="input-field" placeholder="e.g. tap.az, lalafo.az, boss.az"
                    value={idea.known_competitors} onChange={update('known_competitors')} maxLength={500} />
                </div>
                <div>
                  <label className="label" htmlFor="idea-advantage">Unfair Advantage / Moat</label>
                  <input id="idea-advantage" className="input-field" placeholder="e.g. Full in-house codebase built, local merchant access"
                    value={idea.unfair_advantage} onChange={update('unfair_advantage')} maxLength={1000} />
                </div>
              </div>
              <div className="mt-4">
                <label className="label" htmlFor="idea-assumptions">Core Unvalidated Assumptions</label>
                <input id="idea-assumptions" className="input-field" placeholder="e.g. Sellers will switch if mobile chat is 2x faster than tap.az"
                  value={idea.key_assumptions} onChange={update('key_assumptions')} maxLength={1000} />
              </div>
              <div className="mt-4">
                <label className="label" htmlFor="idea-context">Additional Context</label>
                <textarea id="idea-context" className="textarea-field" rows={2}
                  placeholder="Any other relevant context (tech stack, local payment integrations ePUL/MilliÖN, etc.)"
                  value={idea.additional_context} onChange={update('additional_context')} maxLength={3000} />
              </div>
            </div>

            {/* AI Provider Setup & OpenRouter API Key Tutorial */}
            <div className="card p-6 border-amber-400/30">
              <div className="flex items-center justify-between mb-2">
                <h2 className="section-title mb-0">🔑 OpenRouter AI Setup</h2>
                <a
                  href="https://openrouter.ai/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-amber-400 hover:text-amber-300 underline font-medium flex items-center gap-1"
                >
                  <span>Get your free key at openrouter.ai/keys</span>
                  <span>→</span>
                </a>
              </div>
              <p className="text-xs text-gray-400 mb-4">
                Assumption Zero runs on OpenRouter models under the hood. Leave blank to use the free built-in key, or enter your own key for higher rate limits.
              </p>
              <div>
                <label className="label" htmlFor="openrouter-key">Your OpenRouter API Key <span className="text-gray-500 font-normal">(optional)</span></label>
                <input
                  id="openrouter-key"
                  type="password"
                  className="input-field font-mono text-sm"
                  placeholder="sk-or-v1-..."
                  value={customApiKey}
                  onChange={(e) => setCustomApiKey(e.target.value)}
                />
              </div>
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
