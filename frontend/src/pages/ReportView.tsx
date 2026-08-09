import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { AnalysisResult } from '../types'
import confetti from 'canvas-confetti'
import OpportunityGauge from '../components/OpportunityGauge'
import PerspectivePanel from '../components/PerspectivePanel'
import CompetitorCard from '../components/CompetitorCard'
import ExperimentCard from '../components/ExperimentCard'
import ProgressView from './ProgressView'
import FinancialSimulator from '../components/FinancialSimulator'
import ScoreBreakdown from '../components/ScoreBreakdown'
import { recommendationBg, recommendationColor, safeExternalUrl } from '../lib/utils'
import { generateMarkdownReport } from '../lib/report'

const DISCLAIMER = "AI analysis is based on available web data and pattern recognition. It is not financial or definitive business advice. Always perform your own due diligence."

interface Props {
  initialResult?: AnalysisResult
}

export default function ReportView({ initialResult }: Props) {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<AnalysisResult | null>(initialResult || null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [confettiFired, setConfettiFired] = useState(false)
  const [evidenceQuery, setEvidenceQuery] = useState('')
  const [showAllEvidence, setShowAllEvidence] = useState(false)

  useEffect(() => {
    if (initialResult?.status === 'complete' || initialResult?.status === 'failed') {
      setResult(initialResult)
      return
    }
    let interval: number
    const load = async () => {
      try {
        if (!id) return
        const data = await api.getAnalysis(id)
        setResult(data)

        if (data.status === 'pending' || data.status === 'running') {
          interval = window.setTimeout(load, 2000)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analysis')
      }
    }
    load()
    return () => clearTimeout(interval)
  }, [id, initialResult])

  const score = result?.opportunity_score?.total
  useEffect(() => {
    if (result && result.status !== 'running' && result.status !== 'pending' && !confettiFired && score !== undefined && score >= 70) {
      confetti({
        particleCount: 150,
        spread: 80,
        origin: { y: 0.6 },
        colors: ['#181818', '#e5e5e5', '#a3a3a3'] // monochromatic confetti!
      })
      setConfettiFired(true)
    }
  }, [result, score, confettiFired])

  if (error) {
    return (
      <div className="min-h-screen bg-[#f9f9f9] text-gray-900 flex items-center justify-center p-4">
        <div className="p-4 text-center bg-white">
        <p className="text-red-600 font-medium mb-4">{error}</p>
        <Link to="/" className="btn-ghost inline-block">Return Home</Link>
      </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-[#f9f9f9] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-gray-300 border-t-gray-900 rounded-full animate-spin"></div>
      </div>
    )
  }

  if (result.status === 'pending' || result.status === 'running') {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in duration-500">
        <div className="w-16 h-16 border-4 border-gray-100 border-t-gray-900 rounded-full animate-spin shadow-sm mb-6" />
        <h3 className="text-xl font-display font-bold text-gray-900 mb-2">Analyzing Startup Idea</h3>
        <p className="text-gray-500 font-mono text-sm max-w-sm animate-pulse">
          {result.stage_description || 'Gathering evidence and evaluating assumptions...'}
        </p>
      </div>
    )
  }

  const rec = result.recommendation
  const conf = result.evidence_confidence
  const normalizedEvidenceQuery = evidenceQuery.trim().toLowerCase()
  const usesBaselineModel = result.models_used.some((model) => {
    const normalized = model.toLowerCase()
    return normalized.includes('mock') || normalized.includes('evidence engine') || normalized.includes('template')
  })
  const filteredEvidence = result.evidence.filter((item) => !normalizedEvidenceQuery || [
    item.title, item.passage, item.evidence_type, item.evidence_origin, item.source_name,
  ].some((value) => value.toLowerCase().includes(normalizedEvidenceQuery)))
  const visibleEvidence = showAllEvidence ? filteredEvidence : filteredEvidence.slice(0, 12)

  const handleCopyMarkdown = async () => {
    if (!result) return
    try {
      await navigator.clipboard.writeText(generateMarkdownReport(result))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Your browser blocked clipboard access. Use Download Markdown instead.')
    }
  }

  const download = (content: string, type: string, extension: string) => {
    if (!result) return
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `assumption-zero-${result.idea_input.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || result.analysis_id.slice(0, 8)}.${extension}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDownloadJSON = () => download(JSON.stringify(result, null, 2), 'application/json', 'json')
  const handleDownloadMarkdown = () => result && download(generateMarkdownReport(result), 'text/markdown;charset=utf-8', 'md')

  return (
    <div className="min-h-screen bg-white verseo-grid text-gray-900 pb-20 selection:bg-gray-100" id="report">
      <div className="max-w-5xl mx-auto space-y-6 pt-8 px-4 sm:px-6">
        
        {/* Top Bar with Exports */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-white border border-gray-200 shadow-sm backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors flex items-center gap-1">
              ← Back to Home
            </Link>
            <span className="text-gray-300">|</span>
            <span className="text-xs text-gray-500 font-mono">
              ID: <code className="text-gray-900 font-bold bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">{result.analysis_id.slice(0, 8)}</code>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyMarkdown}
              className="px-3 py-1.5 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-xs font-semibold text-gray-700 transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span>{copied ? '✓ Copied!' : '📋 Copy Summary'}</span>
            </button>

            <button
              onClick={handleDownloadJSON}
              className="px-3 py-1.5 rounded-xl border border-gray-200 bg-gray-100 hover:bg-gray-200 text-xs font-semibold text-gray-800 transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span>💾 Export JSON</span>
            </button>
            <button
              onClick={handleDownloadMarkdown}
              className="px-3 py-1.5 rounded-xl border border-gray-200 bg-gray-900 hover:bg-black text-xs font-semibold text-white transition-all shadow-sm"
            >
              Download Markdown
            </button>
            <button
              onClick={() => window.print()}
              className="px-3 py-1.5 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-xs font-semibold text-gray-700 transition-all shadow-sm"
            >
              Print / PDF
            </button>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="verseo-card p-4 border border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 text-center uppercase tracking-wider font-mono font-medium">{DISCLAIMER}</p>
        </div>

        {usesBaselineModel && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
            <p className="text-xs font-bold uppercase tracking-wider mb-1">Evidence baseline mode</p>
            <p className="text-xs leading-relaxed">
              This report used deterministic analysis over collected evidence without a configured generative AI provider. Scores and experiments remain useful, but qualitative perspective depth improves when you configure a provider.
            </p>
          </div>
        )}

        {/* 1. Executive Verdict */}
        <section id="verdict" className="verseo-card p-6 sm:p-8">
          <span className="verseo-corner-tl">+</span>
          <span className="verseo-corner-tr">+</span>
          <span className="verseo-corner-bl">+</span>
          <span className="verseo-corner-br">+</span>
          <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
            {score !== undefined && <OpportunityGauge score={score} size={140} />}
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-3xl font-display font-black text-gray-900 mb-2 tracking-tight">{result.idea_input.name}</h1>
              <p className="text-gray-600 text-sm mb-5 leading-relaxed">{result.idea_input.description}</p>

              <div className="flex flex-wrap gap-3 justify-center md:justify-start mb-5">
                {rec && (
                  <span className={`badge px-4 py-2 text-sm uppercase tracking-wider font-bold shadow-sm ${recommendationBg(rec)}`}>
                    <span className={recommendationColor(rec)}>{rec}</span>
                  </span>
                )}
                {conf && (
                  <span className="badge px-3 py-2 text-xs font-mono font-bold uppercase bg-white border-gray-200 text-gray-700 shadow-sm">
                    {conf} CONFIDENCE
                  </span>
                )}
              </div>

              {result.most_dangerous_assumption && (
                <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-left">
                  <p className="text-[10px] text-red-600 font-bold uppercase tracking-widest mb-1">
                    ⚠ Most Dangerous Assumption
                  </p>
                  <p className="text-sm font-medium text-red-900">{result.most_dangerous_assumption}</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {result.opportunity_score && <ScoreBreakdown score={result.opportunity_score} />}

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="verseo-card p-5 border-l-4 border-l-emerald-500">
            <p className="text-[10px] text-emerald-700 font-bold uppercase tracking-widest mb-2">Strongest supporting signal</p>
            <p className="text-sm text-gray-700 leading-relaxed">{result.strongest_supporting || 'Insufficient supporting evidence collected.'}</p>
          </div>
          <div className="verseo-card p-5 border-l-4 border-l-rose-500">
            <p className="text-[10px] text-rose-700 font-bold uppercase tracking-widest mb-2">Strongest contradicting signal</p>
            <p className="text-sm text-gray-700 leading-relaxed">{result.strongest_contradicting || 'Insufficient contradicting evidence collected.'}</p>
          </div>
        </section>

        {(result.missing_information.length > 0 || result.disagreements.length > 0) && (
          <section className="verseo-card p-6 space-y-5">
            <div>
              <h2 className="text-xl font-display font-black text-gray-900">What to resolve before building</h2>
              <p className="text-xs text-gray-500 mt-1">Turn these unknowns into interviews, landing-page tests, or pricing probes.</p>
            </div>
            {result.missing_information.length > 0 && (
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {result.missing_information.map((item) => (
                  <li key={item} className="text-xs text-amber-900 bg-amber-50 border border-amber-100 rounded-xl p-3 flex gap-2">
                    <span aria-hidden="true">?</span><span>{item}</span>
                  </li>
                ))}
              </ul>
            )}
            {result.disagreements.map((disagreement) => (
              <div key={disagreement.topic} className="rounded-xl border border-gray-200 p-4 bg-gray-50">
                <p className="text-xs font-bold text-gray-900">Perspective disagreement: {disagreement.topic}</p>
                {disagreement.stronger_position && <p className="text-xs text-gray-600 mt-1">Stronger position: {disagreement.stronger_position}</p>}
                {disagreement.requires_human_research && <p className="text-[11px] text-amber-700 mt-2 font-semibold">Requires direct human research</p>}
              </div>
            ))}
          </section>
        )}

        {/* 1.5 Unit Economics Simulator */}
        <FinancialSimulator idea={result.idea_input} />

        {/* 2. AI Perspectives (Bento Grid) */}
        <section id="perspectives" className="space-y-4">
          <h2 className="section-title text-gray-900 font-display font-black tracking-tight"><span className="text-gray-400">01 /</span> AI Perspectives</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {result.perspectives.map((p) => (
              <PerspectivePanel key={p.perspective_name} perspective={p} evidence={result.evidence} />
            ))}
          </div>
        </section>

        {/* 3. Competitor Intelligence */}
        {result.competitors.length > 0 && (
          <section id="competitors" className="space-y-4 pt-4 border-t border-gray-200">
            <h2 className="section-title text-gray-900 font-display font-black tracking-tight"><span className="text-gray-400">02 /</span> Competitor Intelligence</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.competitors.map((comp) => (
                <CompetitorCard key={comp.name} competitor={comp} evidence={result.evidence} />
              ))}
            </div>
          </section>
        )}

        {/* 4. Validation Experiments */}
        {result.experiments.length > 0 && (
          <section id="experiments" className="space-y-4 pt-4 border-t border-gray-200">
            <h2 className="section-title text-gray-900 font-display font-black tracking-tight"><span className="text-gray-400">03 /</span> Validation Experiments</h2>
            <div className="grid grid-cols-1 gap-4">
              {result.experiments.map((exp, idx) => (
                <ExperimentCard key={exp.title} experiment={exp} index={idx} />
              ))}
            </div>
          </section>
        )}

        {/* 5. Raw Evidence / Citations */}
        {result.evidence.length > 0 && (
          <section id="evidence" className="space-y-4 pt-4 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
              <div>
                <h2 className="section-title text-gray-900 font-display font-black tracking-tight"><span className="text-gray-400">04 /</span> Cited Sources</h2>
                <p className="text-xs text-gray-500 mt-1">Search the evidence behind the score and perspective claims.</p>
              </div>
              <input
                type="search"
                value={evidenceQuery}
                onChange={(event) => { setEvidenceQuery(event.target.value); setShowAllEvidence(false) }}
                placeholder="Filter evidence..."
                className="input-field sm:max-w-xs py-2.5"
                aria-label="Filter evidence"
              />
            </div>
            <div className="verseo-card overflow-hidden">
              <ul className="divide-y divide-gray-100">
                {visibleEvidence.map((ev) => (
                  <li key={ev.evidence_id} className="p-4 sm:p-5 bg-white border border-gray-200 rounded-2xl hover:border-gray-400 hover:shadow-md transition-all">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-[10px] font-mono font-bold bg-gray-100 text-gray-600 px-2 py-0.5 rounded border border-gray-200">
                        [{ev.evidence_id}] {ev.evidence_type.toUpperCase()}
                      </span>
                      {safeExternalUrl(ev.url) && (
                        <a href={safeExternalUrl(ev.url)!} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-900 transition-colors text-xs" title="View Source">
                          [Link]
                        </a>
                      )}
                    </div>
                    <h5 className="font-bold text-sm text-gray-900 mb-2 line-clamp-2 leading-tight">{ev.title}</h5>
                    <p className="text-xs text-gray-500 mb-3 line-clamp-3 leading-relaxed bg-gray-50 p-2.5 rounded-xl border border-gray-100 italic">"{ev.passage}"</p>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-gray-400 uppercase">{ev.evidence_origin || ev.source_name}</span>
                      <span className="text-[10px] text-gray-300">•</span>
                      <span className="text-[10px] font-mono text-gray-400">Score: {ev.relevance_score.toFixed(1)}</span>
                    </div>
                  </li>
                ))}
              </ul>
              {visibleEvidence.length === 0 && (
                <p className="p-8 text-center text-sm text-gray-500">No evidence matches “{evidenceQuery}”.</p>
              )}
              {filteredEvidence.length > 12 && (
                <div className="p-4 border-t border-gray-200 bg-gray-50 text-center">
                  <button onClick={() => setShowAllEvidence((value) => !value)} className="btn-ghost">
                    {showAllEvidence ? 'Show first 12' : `Show all ${filteredEvidence.length} sources`}
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

      </div>
    </div>
  )
}
