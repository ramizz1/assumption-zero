/** AI perspective panel */
import type { AnalysisPerspective, EvidenceItem } from '../types'
import { recommendationColor, recommendationBg } from '../lib/utils'
import CitationBadge from './CitationBadge'

interface Props {
  perspective: AnalysisPerspective
  evidence: EvidenceItem[]
}

const perspectiveIcon: Record<string, string> = {
  market_analyst: '📊',
  skeptical_investor: '🔍',
  practical_builder: '🔧',
}

const perspectiveColor: Record<string, string> = {
  market_analyst: 'border-blue-500/30',
  skeptical_investor: 'border-red-500/30',
  practical_builder: 'border-green-500/30',
}

export default function PerspectivePanel({ perspective, evidence }: Props) {
  const icon = perspectiveIcon[perspective.perspective_name] ?? '🤖'
  const borderColor = perspectiveColor[perspective.perspective_name] ?? 'border-gray-700'

  return (
    <div className={`card p-5 border ${borderColor}`}>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h3 className="font-semibold text-white">{perspective.perspective_display}</h3>
            <p className="text-xs text-gray-500 font-mono mt-0.5">{perspective.model_id}</p>
          </div>
        </div>
        <span
          className={`badge text-sm font-medium px-3 py-1 ${recommendationBg(perspective.recommendation)}`}
        >
          <span className={recommendationColor(perspective.recommendation)}>
            {perspective.recommendation}
          </span>
        </span>
      </div>

      <p className="text-sm text-gray-300 leading-relaxed mb-4">{perspective.summary}</p>

      {perspective.key_findings.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
            Key Findings
          </h4>
          <ul className="space-y-1.5">
            {perspective.key_findings.map((finding, i) => (
              <li key={i} className="text-sm text-gray-300 flex gap-2">
                <span className="text-gray-600 mt-0.5 shrink-0">•</span>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {perspective.risks.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-medium text-red-500/70 uppercase tracking-wide mb-2">
            Risks
          </h4>
          <ul className="space-y-1.5">
            {perspective.risks.map((risk, i) => (
              <li key={i} className="text-sm text-red-400/80 flex gap-2">
                <span className="text-red-600 mt-0.5 shrink-0">↓</span>
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {perspective.opportunities.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-medium text-green-500/70 uppercase tracking-wide mb-2">
            Opportunities
          </h4>
          <ul className="space-y-1.5">
            {perspective.opportunities.map((opp, i) => (
              <li key={i} className="text-sm text-green-400/80 flex gap-2">
                <span className="text-green-600 mt-0.5 shrink-0">↑</span>
                <span>{opp}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {perspective.most_dangerous_assumption && (
        <div className="mt-4 p-3 bg-amber-400/5 border border-amber-500/20 rounded-lg">
          <p className="text-xs text-amber-500/70 font-medium uppercase tracking-wide mb-1">
            Most Dangerous Assumption
          </p>
          <p className="text-sm text-amber-300/90">{perspective.most_dangerous_assumption}</p>
        </div>
      )}

      {perspective.invalid_citations.length > 0 && (
        <div className="mt-3 p-2 bg-red-400/5 border border-red-500/20 rounded-lg">
          <p className="text-xs text-red-400">
            ⚠ Invalid citations detected: {perspective.invalid_citations.join(', ')}
          </p>
        </div>
      )}

      {perspective.cited_evidence_ids.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3 pt-3 border-t border-[#1f1f26]">
          <span className="text-xs text-gray-600 mr-1">Cited:</span>
          {perspective.cited_evidence_ids.map((id) => (
            <CitationBadge key={id} evidenceId={id} evidence={evidence} />
          ))}
        </div>
      )}
    </div>
  )
}
