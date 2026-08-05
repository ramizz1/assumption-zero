import type { AnalysisResult } from '../types'
import { stageLabel } from '../lib/utils'

const STAGES = [
  'clarifying_idea',
  'generating_queries',
  'collecting_evidence',
  'finding_competitors',
  'running_perspectives',
  'checking_citations',
  'calculating_scores',
  'generating_experiments',
  'complete',
]

interface Props {
  result: AnalysisResult
}

export default function ProgressView({ result }: Props) {
  const currentIndex = STAGES.indexOf(result.stage)

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card p-8 mb-6">
        <h1 className="text-xl font-bold text-white mb-1">
          Analysing: {result.idea_input.name}
        </h1>
        <p className="text-sm text-gray-500 mb-8">
          Running real research queries across all configured providers…
        </p>

        {/* Current stage indicator */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-cyan-300 font-medium">{stageLabel(result.stage)}</p>
          </div>
          {result.stage_description && (
            <p className="text-sm text-gray-500 ml-8">{result.stage_description}</p>
          )}
        </div>

        {/* Stage list */}
        <div className="space-y-2">
          {STAGES.filter((s) => s !== 'complete').map((stage, i) => {
            const isDone = i < currentIndex
            const isCurrent = i === currentIndex
            const isPending = i > currentIndex

            return (
              <div key={stage} className={`flex items-center gap-3 py-1.5 px-3 rounded-lg transition-colors ${
                isCurrent ? 'bg-cyan-400/5 border border-cyan-500/20' : ''
              }`}>
                <div className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
                  isDone
                    ? 'bg-green-400'
                    : isCurrent
                    ? 'border-2 border-cyan-400 border-t-transparent animate-spin'
                    : 'border border-gray-700'
                }`}>
                  {isDone && (
                    <svg className="w-2.5 h-2.5 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
                <span className={`text-sm ${
                  isDone ? 'text-green-400' : isCurrent ? 'text-cyan-300' : 'text-gray-600'
                }`}>
                  {stageLabel(stage)}
                </span>
              </div>
            )
          })}
        </div>

        {/* Live stats */}
        {(result.evidence.length > 0 || result.competitors.length > 0) && (
          <div className="mt-6 pt-6 border-t border-[#1f1f26] grid grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-white tabular-nums">{result.evidence.length}</p>
              <p className="text-xs text-gray-500 mt-0.5">Evidence items</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white tabular-nums">{result.competitors.length}</p>
              <p className="text-xs text-gray-500 mt-0.5">Competitors found</p>
            </div>
          </div>
        )}

        {/* Provider errors */}
        {result.provider_errors.length > 0 && (
          <div className="mt-4 p-3 bg-amber-400/5 border border-amber-500/20 rounded-lg">
            <p className="text-xs text-amber-400 font-medium mb-1">
              Provider warnings ({result.provider_errors.length}):
            </p>
            {result.provider_errors.slice(0, 2).map((err, i) => (
              <p key={i} className="text-xs text-amber-400/60">{err.slice(0, 120)}…</p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
