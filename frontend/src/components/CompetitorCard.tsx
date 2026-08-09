/** Competitor card component */
import type { Competitor, EvidenceItem } from '../types'
import CitationBadge from './CitationBadge'
import { safeExternalUrl } from '../lib/utils'

interface Props {
  competitor: Competitor
  evidence: EvidenceItem[]
}

const LucideDollarSign = () => <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline mr-1 text-gray-500 mb-0.5"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>

export default function CompetitorCard({ competitor, evidence }: Props) {
  const isOss = competitor.competitor_type === 'indirect'
  const competitorUrl = safeExternalUrl(competitor.url)

  return (
    <div className="verseo-card p-6 bg-white hover:border-gray-400 hover:shadow-lg transition-all duration-300 relative overflow-hidden">
      <span className="verseo-corner-tl">+</span>
      <span className="verseo-corner-tr">+</span>
      <span className="verseo-corner-bl">+</span>
      <span className="verseo-corner-br">+</span>
      
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-display font-bold text-gray-900">{competitor.name}</h3>
            <span
              className={`badge text-[10px] font-mono px-2 py-0.5 rounded-md uppercase tracking-wider ${
                isOss
                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                  : 'bg-red-50 text-red-700 border-red-200'
              }`}
            >
              {isOss ? 'indirect' : 'direct'}
            </span>
          </div>
          {competitorUrl && (
            <a
              href={competitorUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono text-gray-500 hover:text-gray-900 hover:underline inline-block"
            >
              {competitor.url.replace(/^https?:\/\//, '').split('/')[0]}
            </a>
          )}
        </div>
        <span
          className={`badge text-[10px] font-mono px-2 py-0.5 rounded-md uppercase tracking-wider ${
            competitor.confidence === 'high'
              ? 'bg-green-50 text-green-700 border-green-200'
              : competitor.confidence === 'medium'
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-gray-100 text-gray-600 border-gray-200'
          }`}
        >
          {competitor.confidence} conf
        </span>
      </div>

      <p className="text-sm text-gray-600 mb-4 leading-relaxed">{competitor.description}</p>

      {competitor.pricing_evidence && (
        <p className="text-xs text-gray-500 mb-4 bg-gray-50 p-2.5 rounded-xl border border-gray-100 italic">
          <LucideDollarSign /> {competitor.pricing_evidence}
        </p>
      )}

      {(competitor.strengths.length > 0 || competitor.weaknesses.length > 0 || competitor.complaints.length > 0) && (
        <div className="grid gap-3 sm:grid-cols-3 mt-4 pt-4 border-t border-gray-100">
          {[
            ['Strengths', competitor.strengths, 'text-emerald-700'],
            ['Weaknesses', competitor.weaknesses, 'text-amber-700'],
            ['Customer complaints', competitor.complaints, 'text-red-700'],
          ].map(([label, items, color]) => (
            (items as string[]).length > 0 && (
              <div key={label as string}>
                <p className={`text-[10px] font-bold uppercase tracking-wider mb-1.5 ${color as string}`}>
                  {label as string}
                </p>
                <ul className="space-y-1">
                  {(items as string[]).slice(0, 3).map((item, index) => (
                    <li key={index} className="text-xs text-gray-600 leading-snug">• {item}</li>
                  ))}
                </ul>
              </div>
            )
          ))}
        </div>
      )}

      {competitor.differentiation.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">
            Potential Differentiation
          </p>
          <ul className="space-y-1.5">
            {competitor.differentiation.slice(0, 2).map((d, i) => (
              <li key={i} className="text-xs text-gray-700 flex items-start gap-2">
                <span className="text-emerald-500 font-bold shrink-0">✦</span>
                <span className="leading-snug">{d}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {competitor.evidence_ids.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-4 pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-500 font-medium mr-1">Sources:</span>
          {competitor.evidence_ids.map((id) => (
            <CitationBadge key={id} evidenceId={id} evidence={evidence} />
          ))}
        </div>
      )}

      {competitor.evidence_ids.length === 0 && (
        <p className="text-[10px] text-amber-700 mt-4 pt-3 border-t border-gray-100">
          User-reported candidate — independent verification is still required.
        </p>
      )}
    </div>
  )
}
