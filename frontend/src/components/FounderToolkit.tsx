import { useState } from 'react'
import type { FounderToolkit as FounderToolkitType } from '../types'

interface Props {
  toolkit: FounderToolkitType
}

export default function FounderToolkit({ toolkit }: Props) {
  const [copied, setCopied] = useState(false)

  const copyInterviewScript = async () => {
    const script = [
      'Customer discovery interview script',
      '',
      ...toolkit.interview_questions.map((question, index) => `${index + 1}. ${question}`),
    ].join('\n')
    try {
      await navigator.clipboard.writeText(script)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  return (
    <section id="founder-toolkit" className="space-y-4 pt-4 border-t border-gray-200">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h2 className="section-title text-gray-900 font-display font-black tracking-tight"><span className="text-gray-400">02 /</span> Founder Action Plan</h2>
          <p className="text-xs text-gray-500 mt-1">A practical validation plan generated from your inputs and the analysis decision.</p>
        </div>
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1.5">30-day operating plan</span>
      </div>

      <div className="verseo-card p-5 sm:p-6 bg-zinc-950 text-white border-zinc-800">
        <p className="text-[10px] uppercase tracking-[0.18em] font-mono font-bold text-zinc-400 mb-2">Positioning statement</p>
        <p className="text-base sm:text-lg font-semibold leading-relaxed">{toolkit.one_sentence_pitch}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="verseo-card p-5">
          <p className="text-[10px] uppercase tracking-wider font-mono font-bold text-zinc-500 mb-2">Ideal customer profile</p>
          <p className="text-sm leading-relaxed text-zinc-800">{toolkit.ideal_customer_profile}</p>
        </div>
        <div className="verseo-card p-5">
          <p className="text-[10px] uppercase tracking-wider font-mono font-bold text-zinc-500 mb-2">Beachhead market</p>
          <p className="text-sm leading-relaxed text-zinc-800">{toolkit.beachhead_market}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="verseo-card p-5">
          <h3 className="font-bold text-zinc-900 mb-3">Recommended acquisition channels</h3>
          <ol className="space-y-2">
            {toolkit.recommended_channels.map((channel, index) => (
              <li key={channel} className="flex gap-3 text-sm text-zinc-700">
                <span className="shrink-0 w-6 h-6 rounded-lg bg-zinc-100 border border-zinc-200 grid place-items-center text-[10px] font-mono font-bold">{index + 1}</span>
                <span className="leading-relaxed">{channel}</span>
              </li>
            ))}
          </ol>
        </div>
        <div className="verseo-card p-5">
          <h3 className="font-bold text-zinc-900 mb-3">Metrics to instrument from day one</h3>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {toolkit.key_metrics.map((metric) => (
              <li key={metric} className="text-xs text-zinc-700 bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2.5 flex gap-2"><span className="text-emerald-600">+</span>{metric}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="font-display font-black text-xl text-zinc-900">Validation roadmap</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {toolkit.roadmap.map((action, index) => (
            <article key={action.phase} className="verseo-card p-5 relative overflow-hidden">
              <span className="absolute top-3 right-4 text-5xl font-black text-zinc-100 select-none">{index + 1}</span>
              <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-500 mb-1">{action.phase} · {action.budget_hint}</p>
              <h4 className="font-bold text-zinc-900 mb-3 pr-10">{action.objective}</h4>
              <ul className="space-y-2 mb-4">
                {action.actions.map((step) => <li key={step} className="text-xs text-zinc-600 leading-relaxed flex gap-2"><span aria-hidden="true">→</span><span>{step}</span></li>)}
              </ul>
              <div className="space-y-2 border-t border-zinc-100 pt-3">
                <p className="text-[11px] text-emerald-800 bg-emerald-50 rounded-lg p-2"><strong>Advance when:</strong> {action.success_metric}</p>
                <p className="text-[11px] text-rose-800 bg-rose-50 rounded-lg p-2"><strong>Stop when:</strong> {action.stop_condition}</p>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="verseo-card p-5">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h3 className="font-bold text-zinc-900">Customer interview script</h3>
            <button type="button" onClick={copyInterviewScript} className="btn-ghost px-3 py-1.5 text-xs">{copied ? 'Copied' : 'Copy script'}</button>
          </div>
          <ol className="space-y-2 list-decimal pl-5">
            {toolkit.interview_questions.map((question) => <li key={question} className="text-xs text-zinc-700 leading-relaxed pl-1">{question}</li>)}
          </ol>
        </div>
        <div className="verseo-card p-5">
          <h3 className="font-bold text-zinc-900 mb-3">Evidence-based decision rules</h3>
          <ul className="space-y-2">
            {toolkit.decision_rules.map((rule, index) => (
              <li key={rule} className={`text-xs leading-relaxed rounded-xl p-3 border ${index === 0 ? 'bg-amber-50 border-amber-200 text-amber-900 font-semibold' : 'bg-zinc-50 border-zinc-200 text-zinc-700'}`}>{rule}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
