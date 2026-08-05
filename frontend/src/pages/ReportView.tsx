import { Link } from 'react-router-dom'
import type { AnalysisResult } from '../types'
import {
  scoreColor,
  recommendationColor,
  recommendationBg,
  confidenceColor,
  reliabilityBadge,
  formatDate,
  DISCLAIMER,
} from '../lib/utils'
import OpportunityGauge from '../components/OpportunityGauge'
import ScoreBreakdown from '../components/ScoreBreakdown'
import CompetitorCard from '../components/CompetitorCard'
import PerspectivePanel from '../components/PerspectivePanel'
import ExperimentCard from '../components/ExperimentCard'
import CitationBadge from '../components/CitationBadge'

interface Props {
  result: AnalysisResult
}

export default function ReportView({ result }: Props) {
  const score = result.opportunity_score
  const conf = result.evidence_confidence
  const rec = result.recommendation

  return (
    <div className="max-w-5xl mx-auto space-y-6" id="report">
      {/* Disclaimer (permanent, top of report) */}
      <div className="card p-4 border-amber-500/20 bg-amber-400/5">
        <p className="text-xs text-amber-400/80 text-center">{DISCLAIMER}</p>
      </div>

      {/* 1. Executive Verdict */}
      <section id="verdict" className="card p-6">
        <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
          {score && <OpportunityGauge score={score.total} size={140} />}
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-2xl font-bold text-white mb-1">{result.idea_input.name}</h1>
            <p className="text-gray-400 text-sm mb-4">{result.idea_input.description}</p>

            <div className="flex flex-wrap gap-3 justify-center md:justify-start mb-4">
              {rec && (
                <span className={`badge px-4 py-2 text-base font-semibold ${recommendationBg(rec)}`}>
                  <span className={recommendationColor(rec)}>{rec}</span>
                </span>
              )}
              {conf && (
                <span className={`badge px-3 py-1.5 text-sm bg-white/5 border-white/10`}>
                  <span className={confidenceColor(conf)}>
                    {conf.toUpperCase()} confidence
                  </span>
                </span>
              )}
            </div>

            {result.most_dangerous_assumption && (
              <div className="p-4 bg-amber-400/5 border border-amber-500/20 rounded-lg text-left">
                <p className="text-xs text-amber-500/70 font-medium uppercase tracking-wide mb-1">
                  ⚠ Most Dangerous Assumption
                </p>
                <p className="text-sm text-amber-300">{result.most_dangerous_assumption}</p>
              </div>
            )}
          </div>
        </div>

        {/* Interpreted idea */}
        {result.interpreted_idea && (
          <div className="mt-6 pt-6 border-t border-[#1f1f26]">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-2">
              What we're evaluating
            </p>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">{result.interpreted_idea}</p>
          </div>
        )}

        {/* Provider info */}
        {result.models_used.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2 items-center">
            <span className="text-xs text-gray-600">Models:</span>
            {result.models_used.map((m) => (
              <span key={m} className="badge bg-white/5 border-white/10 text-gray-400 text-xs font-mono">{m}</span>
            ))}
          </div>
        )}

        {/* Provider errors */}
        {result.provider_errors.length > 0 && (
          <div className="mt-4 p-3 bg-amber-400/5 border border-amber-500/20 rounded-lg">
            <p className="text-xs text-amber-400 font-medium mb-1">
              ⚠ Provider warnings
            </p>
            {result.provider_errors.map((err, i) => (
              <p key={i} className="text-xs text-amber-400/60">• {err}</p>
            ))}
          </div>
        )}
      </section>

      {/* 2. Score Breakdown */}
      {score && <ScoreBreakdown score={score} />}

      {/* 3. Evidence summary */}
      <section id="evidence-summary" className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title mb-0">Evidence</h2>
          <span className="text-sm text-gray-500">
            {result.evidence.length} items from{' '}
            {new Set(result.evidence.map((e) => e.source_name)).size} sources
          </span>
        </div>

        {/* Supporting / Contradicting */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {result.strongest_supporting && result.strongest_supporting !== 'Insufficient evidence' && (
            <div className="p-4 bg-green-400/5 border border-green-500/20 rounded-lg">
              <p className="text-xs text-green-500/70 font-medium uppercase tracking-wide mb-2">
                ↑ Strongest Supporting
              </p>
              <p className="text-sm text-green-300/80 leading-relaxed">{result.strongest_supporting}</p>
            </div>
          )}
          {result.strongest_contradicting && result.strongest_contradicting !== 'Insufficient evidence' && (
            <div className="p-4 bg-red-400/5 border border-red-500/20 rounded-lg">
              <p className="text-xs text-red-500/70 font-medium uppercase tracking-wide mb-2">
                ↓ Strongest Contradicting
              </p>
              <p className="text-sm text-red-300/80 leading-relaxed">{result.strongest_contradicting}</p>
            </div>
          )}
        </div>
      </section>

      {/* 4. Competitors */}
      {result.competitors.length > 0 && (
        <section id="competitors">
          <h2 className="section-title px-1">Competitor Landscape</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.competitors.map((comp, i) => (
              <CompetitorCard key={i} competitor={comp} evidence={result.evidence} />
            ))}
          </div>
        </section>
      )}

      {/* 5. AI Perspectives */}
      {result.perspectives.length > 0 && (
        <section id="perspectives">
          <h2 className="section-title px-1">AI Perspectives</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {result.perspectives.map((p, i) => (
              <PerspectivePanel key={i} perspective={p} evidence={result.evidence} />
            ))}
          </div>
        </section>
      )}

      {/* 6. Disagreements */}
      {result.disagreements.length > 0 && (
        <section id="disagreements" className="card p-6">
          <h2 className="section-title">Model Disagreements</h2>
          <div className="space-y-4">
            {result.disagreements.map((d, i) => (
              <div key={i} className="border border-[#2a2a35] rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-amber-400">↔</span>
                  <h3 className="font-medium text-white">{d.topic}</h3>
                  {d.requires_human_research && (
                    <span className="badge bg-amber-400/10 text-amber-300 border-amber-500/20 text-xs ml-auto">
                      Needs human research
                    </span>
                  )}
                </div>
                <div className="space-y-2">
                  {d.positions.map((pos, j) => (
                    <div key={j} className="flex gap-3">
                      <span className="text-xs text-gray-500 w-32 shrink-0">{pos.perspective}</span>
                      <span className="text-sm text-gray-300">{pos.position}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 7. Validation Experiments */}
      {result.experiments.length > 0 && (
        <section id="experiments">
          <h2 className="section-title px-1">Validation Experiments</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.experiments.map((exp, i) => (
              <ExperimentCard key={i} experiment={exp} index={i + 1} />
            ))}
          </div>
        </section>
      )}

      {/* 8. Missing Information */}
      {result.missing_information.length > 0 && (
        <section id="missing-info" className="card p-6">
          <h2 className="section-title">Missing Information</h2>
          <ul className="space-y-2">
            {result.missing_information.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-400">
                <span className="text-amber-500 mt-0.5">•</span>
                {item}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* 9. Sources */}
      {result.evidence.length > 0 && (
        <section id="sources" className="card p-6">
          <h2 className="section-title">Sources ({result.evidence.length})</h2>
          <div className="space-y-3">
            {result.evidence.map((e) => (
              <div key={e.evidence_id} className="flex gap-3 py-2 border-b border-[#1a1a22] last:border-0">
                <span className="citation-badge shrink-0 self-start">{e.evidence_id}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-2 flex-wrap">
                    <a
                      href={e.url.startsWith('demo://') ? '#' : e.url}
                      target={e.url.startsWith('demo://') ? '_self' : '_blank'}
                      rel="noopener noreferrer"
                      className="text-sm text-blue-400 hover:underline leading-tight"
                    >
                      {e.title}
                    </a>
                    <span className={`badge text-xs ${reliabilityBadge(e.reliability)} shrink-0`}>
                      {e.reliability}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">{e.passage}</p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {e.source_name} · {formatDate(e.publication_date || e.retrieval_date)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 10. Methodology disclaimer */}
      <section id="methodology" className="card p-6 border-amber-500/10 bg-amber-400/5">
        <h2 className="section-title">Methodology & Limitations</h2>
        <div className="prose prose-sm prose-invert max-w-none text-gray-400 space-y-2">
          <p>{DISCLAIMER}</p>
          <p>
            Opportunity Score (0–100) is calculated deterministically by Python from dimension
            scores returned by each AI perspective. Weights: Problem Evidence 20%, Demand
            Signals 20%, Competitive Gap 15%, Distribution 15%, Economics 15%, Founder Fit 10%,
            Legal Risk 5%.
          </p>
          <p>
            Evidence Confidence reflects source quantity, diversity, reliability, recency, and
            citation validity — not the strength of the business idea itself.
          </p>
          <p>
            AI models may produce incorrect or outdated information. Every factual claim should
            be independently verified before making business decisions.
          </p>
        </div>
      </section>

      {/* Bottom actions */}
      <div className="flex justify-center gap-3 pb-8">
        <Link to="/" className="btn-ghost">← New Analysis</Link>
      </div>
    </div>
  )
}
