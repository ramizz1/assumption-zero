/** Competitor card component */
import type { Competitor, EvidenceItem } from '../types'
import CitationBadge from './CitationBadge'

interface Props {
  competitor: Competitor
  evidence: EvidenceItem[]
}

export default function CompetitorCard({ competitor, evidence }: Props) {
  const isOss = competitor.competitor_type === 'indirect'

  return (
    <div className="card p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-white">{competitor.name}</h3>
            <span
              className={`badge text-xs ${
                isOss
                  ? 'bg-blue-400/10 text-blue-300 border-blue-500/20'
                  : 'bg-red-400/10 text-red-300 border-red-500/20'
              }`}
            >
              {isOss ? 'indirect' : 'direct'}
            </span>
          </div>
          {competitor.url && !competitor.url.startsWith('demo://') && (
            <a
              href={competitor.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-400 hover:underline mt-0.5 inline-block"
            >
              {competitor.url.replace(/^https?:\/\//, '').split('/')[0]}
            </a>
          )}
        </div>
        <span
          className={`badge text-xs ${
            competitor.confidence === 'high'
              ? 'bg-green-400/10 text-green-300 border-green-500/20'
              : competitor.confidence === 'medium'
              ? 'bg-amber-400/10 text-amber-300 border-amber-500/20'
              : 'bg-gray-400/10 text-gray-400 border-gray-600/20'
          }`}
        >
          {competitor.confidence} confidence
        </span>
      </div>

      <p className="text-sm text-gray-400 mb-3">{competitor.description}</p>

      {competitor.pricing_evidence && (
        <p className="text-xs text-gray-500 mb-3 italic">
          💰 {competitor.pricing_evidence}
        </p>
      )}

      {competitor.differentiation.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">
            Potential Differentiation
          </p>
          <ul className="space-y-0.5">
            {competitor.differentiation.slice(0, 2).map((d, i) => (
              <li key={i} className="text-xs text-green-400/80">• {d}</li>
            ))}
          </ul>
        </div>
      )}

      {competitor.evidence_ids.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {competitor.evidence_ids.map((id) => (
            <CitationBadge key={id} evidenceId={id} evidence={evidence} />
          ))}
        </div>
      )}
    </div>
  )
}
