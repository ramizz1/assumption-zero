import { useState } from 'react'
import type { FounderToolkit as FounderToolkitType } from '../types'

interface Props { toolkit: FounderToolkitType }

export default function FounderToolkit({ toolkit }: Props) {
  const [copied, setCopied] = useState(false)
  const demandSnapshot = toolkit.demand_snapshot ?? []
  const budgetAllocation = toolkit.budget_allocation ?? []
  const budgetReleaseRules = toolkit.budget_release_rules ?? []
  const interviewQuestions = toolkit.interview_questions ?? []
  const decisionRules = toolkit.decision_rules ?? []
  const recommendedChannels = toolkit.recommended_channels ?? []
  const keyMetrics = toolkit.key_metrics ?? []

  const copyInterviewScript = async () => {
    const script = ['Customer discovery interview script', '', ...interviewQuestions.map((question, index) => `${index + 1}. ${question}`)].join('\n')
    try {
      await navigator.clipboard.writeText(script)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch { setCopied(false) }
  }

  return (
    <section id="founder-toolkit" className="space-y-4 pt-4 border-t border-gray-200">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h2 className="section-title text-gray-900 font-display font-black tracking-tight"><span className="text-gray-400">02 /</span> Demand Proof Dashboard</h2>
          <p className="text-xs text-gray-500 mt-1">What the research knows, what only customers can prove, and how much to risk next.</p>
        </div>
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-800 bg-amber-50 border border-amber-200 rounded-full px-3 py-1.5">Signals are not sales</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-4">
        <article className="verseo-card p-5 sm:p-6">
          <h3 className="font-bold text-zinc-950">Demand evidence ladder</h3>
          <p className="mt-1 text-xs text-zinc-500">The first two rows come from research. The remaining rows require you to run tests.</p>
          <ol className="mt-4 space-y-2">
            {demandSnapshot.map((item, index) => (
              <li key={item} className={`flex gap-3 rounded-xl border p-3 text-xs leading-relaxed ${index < 2 ? 'border-blue-100 bg-blue-50 text-blue-950' : 'border-amber-100 bg-amber-50 text-amber-950'}`}>
                <span className="shrink-0 w-6 h-6 rounded-lg bg-white/70 border border-current/10 grid place-items-center font-mono font-bold">{index + 1}</span>
                <span>{item}</span>
              </li>
            ))}
          </ol>
        </article>

        <article className="verseo-card p-5 sm:p-6 bg-zinc-950 text-white border-zinc-800">
          <p className="text-[10px] uppercase tracking-wider font-mono font-bold text-zinc-400">Validation budget</p>
          <p className="mt-2 text-sm font-semibold leading-relaxed">{toolkit.validation_budget}</p>
          <ul className="mt-4 space-y-2">
            {budgetAllocation.map((item) => <li key={item} className="text-xs text-zinc-300 flex gap-2"><span className="text-emerald-400">+</span>{item}</li>)}
          </ul>
        </article>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <article className="verseo-card p-5">
          <p className="text-[10px] uppercase tracking-wider font-mono font-bold text-zinc-500 mb-2">Who to test first</p>
          <p className="text-sm leading-relaxed text-zinc-800">{toolkit.ideal_customer_profile}</p>
          <p className="mt-3 text-xs leading-relaxed text-zinc-600"><strong>Beachhead:</strong> {toolkit.beachhead_market}</p>
        </article>
        <article className="verseo-card p-5">
          <p className="text-[10px] uppercase tracking-wider font-mono font-bold text-zinc-500 mb-2">Budget release rules</p>
          <ul className="space-y-2">
            {budgetReleaseRules.map((rule) => <li key={rule} className="text-xs text-zinc-700 flex gap-2"><span className="text-rose-600">→</span>{rule}</li>)}
          </ul>
        </article>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <article className="verseo-card p-5">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div>
              <h3 className="font-bold text-zinc-900">Customer interview script</h3>
              <p className="text-[11px] text-zinc-500 mt-0.5">Ask about past behavior; do not pitch until the end.</p>
            </div>
            <button type="button" onClick={copyInterviewScript} className="btn-ghost px-3 py-1.5 text-xs">{copied ? 'Copied' : 'Copy script'}</button>
          </div>
          <ol className="space-y-2 list-decimal pl-5">
            {interviewQuestions.map((question) => <li key={question} className="text-xs text-zinc-700 leading-relaxed pl-1">{question}</li>)}
          </ol>
        </article>
        <article className="verseo-card p-5">
          <h3 className="font-bold text-zinc-900 mb-3">Decision rules</h3>
          <ul className="space-y-2">
            {decisionRules.map((rule, index) => (
              <li key={rule} className={`text-xs leading-relaxed rounded-xl p-3 border ${index === 0 ? 'bg-amber-50 border-amber-200 text-amber-900 font-semibold' : 'bg-zinc-50 border-zinc-200 text-zinc-700'}`}>{rule}</li>
            ))}
          </ul>
        </article>
      </div>

      <details className="verseo-card p-5">
        <summary className="cursor-pointer font-bold text-sm text-zinc-900">Channels and metrics to track</summary>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-4">
          <ol className="space-y-2">
            {recommendedChannels.map((channel, index) => <li key={channel} className="text-xs text-zinc-700"><strong>{index + 1}.</strong> {channel}</li>)}
          </ol>
          <ul className="space-y-2">
            {keyMetrics.map((metric) => <li key={metric} className="text-xs text-zinc-700">+ {metric}</li>)}
          </ul>
        </div>
      </details>
    </section>
  )
}
