/** AI perspective panel */
import type { AnalysisPerspective, EvidenceItem } from '../types'
import { recommendationColor, recommendationBg } from '../lib/utils'
import CitationBadge from './CitationBadge'

interface Props {
  perspective: AnalysisPerspective
  evidence: EvidenceItem[]
}

const LucideBarChart = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>
const LucideSearch = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
const LucideWrench = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
const LucideBot = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="14" x="3" y="7" rx="2" ry="2"/><path d="M12 3v4"/><path d="M8 3h8"/><path d="M15 12v.01"/><path d="M9 12v.01"/></svg>
const LucideGlobe = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></svg>
const LucideUsers = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>

const perspectiveIcon: Record<string, React.ReactNode> = {
  market_analyst: <LucideBarChart />,
  regional_strategist: <LucideGlobe />,
  skeptical_investor: <LucideSearch />,
  customer_researcher: <LucideUsers />,
  practical_builder: <LucideWrench />,
}

const perspectiveGlow: Record<string, string> = {
  market_analyst: 'border-blue-200 hover:border-blue-400',
  regional_strategist: 'border-violet-200 hover:border-violet-400',
  skeptical_investor: 'border-rose-200 hover:border-rose-400',
  customer_researcher: 'border-amber-200 hover:border-amber-400',
  practical_builder: 'border-emerald-200 hover:border-emerald-400',
}

export default function PerspectivePanel({ perspective, evidence }: Props) {
  const icon = perspectiveIcon[perspective.perspective_name] ?? <LucideBot />
  const glow = perspectiveGlow[perspective.perspective_name] ?? 'border-gray-200'

  return (
    <div className={`verseo-card p-6 border ${glow} relative overflow-hidden bg-white`}>
      <span className="verseo-corner-tl">+</span>
      <span className="verseo-corner-tr">+</span>
      <span className="verseo-corner-bl">+</span>
      <span className="verseo-corner-br">+</span>
      
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-200 flex items-center justify-center text-xl shadow-sm">
            {icon}
          </div>
          <div>
            <h3 className="font-display font-bold text-gray-900 tracking-tight text-base">{perspective.perspective_display}</h3>
            <p className="text-[11px] text-gray-400 font-mono mt-0.5">{perspective.model_id}</p>
          </div>
        </div>

        <span
          className={`badge text-xs font-bold px-3 py-1.5 rounded-xl border ${recommendationBg(perspective.recommendation)}`}
        >
          <span className={recommendationColor(perspective.recommendation)}>
            {perspective.recommendation}
          </span>
        </span>
      </div>

      <p className="text-sm text-gray-600 leading-relaxed mb-5">{perspective.summary}</p>

      {perspective.key_findings.length > 0 && (
        <div className="mb-4">
          <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            Key Findings
          </h4>
          <ul className="space-y-2">
            {perspective.key_findings.map((finding, i) => (
              <li key={i} className="text-xs text-gray-700 flex items-start gap-2.5 bg-gray-50 p-2.5 rounded-xl border border-gray-100">
                <span className="text-blue-500 font-bold shrink-0">▸</span>
                <span className="leading-normal">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {perspective.risks.length > 0 && (
        <div className="mb-4">
          <h4 className="text-[11px] font-bold text-rose-500 uppercase tracking-wider mb-2">
            Critical Risks
          </h4>
          <ul className="space-y-2">
            {perspective.risks.map((risk, i) => (
              <li key={i} className="text-xs text-rose-900 flex items-start gap-2.5 bg-rose-50 p-2.5 rounded-xl border border-rose-100">
                <span className="text-rose-500 shrink-0 font-bold">↓</span>
                <span className="leading-normal">{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {perspective.opportunities.length > 0 && (
        <div className="mb-4">
          <h4 className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider mb-2">
            Growth Opportunities
          </h4>
          <ul className="space-y-2">
            {perspective.opportunities.map((opp, i) => (
              <li key={i} className="text-xs text-emerald-900 flex items-start gap-2.5 bg-emerald-50 p-2.5 rounded-xl border border-emerald-100">
                <span className="text-emerald-500 shrink-0 font-bold">↑</span>
                <span className="leading-normal">{opp}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {perspective.most_dangerous_assumption && (
        <div className="mt-4 p-3.5 bg-amber-50 border border-amber-200 rounded-xl">
          <p className="text-[10px] text-amber-600 font-bold uppercase tracking-widest mb-1 flex items-center gap-1">
            <span>⚠️</span> Most Dangerous Assumption
          </p>
          <p className="text-xs font-medium text-amber-900 leading-relaxed">{perspective.most_dangerous_assumption}</p>
        </div>
      )}

      {perspective.cited_evidence_ids.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mt-4 pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-500 font-medium mr-1">Evidence Sources:</span>
          {perspective.cited_evidence_ids.map((id) => (
            <CitationBadge key={id} evidenceId={id} evidence={evidence} />
          ))}
        </div>
      )}
    </div>
  )
}
