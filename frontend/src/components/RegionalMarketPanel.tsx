import type { RegionalEvidenceSignal, RegionalMarketAnalysis, ResearchCoverage } from '../types'

interface Props {
  analysis: RegionalMarketAnalysis
  coverage?: ResearchCoverage
}

const SignalList = ({ title, items }: { title: string; items: RegionalEvidenceSignal[] }) => (
  <div className="rounded-2xl border border-zinc-200 bg-white p-4">
    <div className="flex items-center justify-between gap-3 mb-3">
      <h3 className="text-xs font-bold text-zinc-900">{title}</h3>
      <span className="text-[10px] font-mono text-zinc-400">{items.length} cited</span>
    </div>
    {items.length ? (
      <ul className="space-y-2">
        {items.slice(0, 5).map((item) => (
          <li key={`${title}-${item.evidence_id}`} className="text-[11px] leading-relaxed text-zinc-600 border-t border-zinc-100 first:border-0 pt-2 first:pt-0">
            <span className="font-mono font-bold text-zinc-900">[{item.evidence_id}]</span> {item.title}
            <span className="block text-[10px] text-zinc-400 mt-0.5">{item.source_name} · relevance {item.relevance_score.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    ) : <p className="text-[11px] text-amber-700 bg-amber-50 rounded-lg p-2.5">No region-specific evidence collected for this category.</p>}
  </div>
)

export default function RegionalMarketPanel({ analysis, coverage }: Props) {
  const scoreTone = analysis.demand_score >= 70 ? 'text-emerald-700' : analysis.demand_score >= 45 ? 'text-amber-700' : 'text-rose-700'

  return (
    <section id="regional-market" className="space-y-4 pt-4 border-t border-zinc-200">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h2 className="section-title text-zinc-900 font-display font-black tracking-tight"><span className="text-zinc-400">01 /</span> Regional Market Reality</h2>
          <p className="text-xs text-zinc-500 mt-1">Demand, pricing, regulation, and distribution evidence specifically tied to {analysis.geography}.</p>
        </div>
        {coverage && <span className="text-[10px] font-mono font-bold uppercase tracking-wider rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1.5">{coverage.depth} research</span>}
      </div>

      <div className="verseo-card p-5 sm:p-6">
        <div className="grid grid-cols-1 md:grid-cols-[150px_1fr] gap-6 items-center">
          <div className="text-center md:text-left">
            <p className={`text-5xl font-black tabular-nums ${scoreTone}`}>{analysis.demand_score.toFixed(0)}</p>
            <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-500 mt-1">Regional evidence score</p>
            <p className="text-[10px] font-mono text-zinc-400 mt-2">{analysis.confidence} confidence</p>
          </div>
          <div>
            <p className="text-sm text-zinc-700 leading-relaxed">{analysis.summary}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
              {[
                ['Local evidence', analysis.evidence_count],
                ['Local sources', analysis.source_count],
                ['Queries run', coverage?.queries_executed ?? '—'],
                ['All evidence', coverage?.evidence_collected ?? '—'],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-zinc-50 border border-zinc-200 p-2.5">
                  <p className="text-lg font-black text-zinc-900">{value}</p>
                  <p className="text-[9px] font-mono uppercase text-zinc-400">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <SignalList title="Demand and buyer pain" items={analysis.demand_signals} />
        <SignalList title="Local pricing" items={analysis.pricing_signals} />
        <SignalList title="Regulation and compliance" items={analysis.regulatory_signals} />
        <SignalList title="Distribution and channels" items={analysis.distribution_signals} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="verseo-card p-5">
          <h3 className="font-bold text-zinc-900 mb-3">Localization checklist</h3>
          <ul className="space-y-2">
            {analysis.localization_requirements.map((item) => <li key={item} className="text-xs leading-relaxed text-zinc-700 flex gap-2"><span className="text-emerald-600">✓</span><span>{item}</span></li>)}
          </ul>
        </div>
        <div className="verseo-card p-5 border-amber-200 bg-amber-50/50">
          <h3 className="font-bold text-amber-950 mb-3">Regional research gaps</h3>
          <ul className="space-y-2">
            {analysis.research_gaps.map((item) => <li key={item} className="text-xs leading-relaxed text-amber-900 flex gap-2"><span>?</span><span>{item}</span></li>)}
          </ul>
        </div>
      </div>

      {coverage && (
        <p className="text-[10px] font-mono text-zinc-400 text-center">Generated {coverage.queries_generated} candidate queries · executed {coverage.queries_executed} balanced queries · providers: {coverage.providers_used.join(', ') || 'none available'}</p>
      )}
    </section>
  )
}
