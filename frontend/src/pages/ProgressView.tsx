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
  const currentIndex = Math.max(0, STAGES.indexOf(result.stage))
  const progressPercent = Math.min(100, Math.round(((currentIndex + 1) / STAGES.length) * 100))

  return (
    <div className="max-w-2xl mx-auto py-6">
      <div className="verseo-card p-8 shadow-sm relative overflow-hidden bg-white">
        <span className="verseo-corner-tl">+</span>
        <span className="verseo-corner-tr">+</span>
        <span className="verseo-corner-bl">+</span>
        <span className="verseo-corner-br">+</span>

        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] font-bold text-gray-700 uppercase tracking-widest bg-gray-100 px-2.5 py-1 rounded-full border border-gray-200">
            ✦ AI Engine Active
          </span>
          <span className="text-xs font-mono font-bold text-gray-500">{progressPercent}%</span>
        </div>

        <h1 className="text-2xl font-display font-black text-gray-900 tracking-tight mb-2">
          Evaluating: {result.idea_input.name}
        </h1>
        <p className="text-sm text-gray-500 mb-8">
          Gathering live evidence, challenging moat assumptions & computing opportunity score...
        </p>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-8 border border-gray-200">
          <div
            className="h-full bg-gray-900 transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Current stage indicator */}
        <div className="mb-8 p-4 rounded-xl bg-gray-50 border border-gray-200 flex items-start gap-4 shadow-sm">
          <div className="w-6 h-6 border-2 border-gray-400 border-t-gray-900 rounded-full animate-spin shrink-0 mt-0.5" />
          <div>
            <p className="text-gray-900 font-bold text-sm tracking-tight">{stageLabel(result.stage)}</p>
            {result.stage_description && (
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">{result.stage_description}</p>
            )}
          </div>
        </div>

        {/* Stage list */}
        <div className="space-y-2">
          {STAGES.filter((s) => s !== 'complete').map((stage, i) => {
            const isDone = i < currentIndex
            const isCurrent = i === currentIndex

            return (
              <div
                key={stage}
                className={`flex items-center gap-3.5 py-2 px-3.5 rounded-xl transition-all ${
                  isCurrent
                    ? 'bg-gray-100 border border-gray-200 text-gray-900 shadow-sm'
                    : isDone
                    ? 'text-green-700 bg-green-50'
                    : 'text-gray-400 bg-white'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                    isDone
                      ? 'bg-green-100 text-green-700 border border-green-200 shadow-sm'
                      : isCurrent
                      ? 'border-2 border-gray-300 border-t-gray-900 animate-spin'
                      : 'border border-gray-200 text-gray-400 bg-gray-50'
                  }`}
                >
                  {isDone ? '✓' : ''}
                </div>
                <span className={`text-xs font-medium ${isCurrent ? 'font-bold text-gray-900' : ''}`}>
                  {stageLabel(stage)}
                </span>
              </div>
            )
          })}
        </div>

        {/* Live stats */}
        {(result.evidence.length > 0 || result.competitors.length > 0) && (
          <div className="mt-8 pt-6 border-t border-gray-100 grid grid-cols-2 gap-4">
            <div className="text-center p-3 rounded-xl bg-gray-50 border border-gray-200">
              <p className="text-2xl font-black text-gray-900 tabular-nums">{result.evidence.length}</p>
              <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mt-0.5">Evidence Cited</p>
            </div>
            <div className="text-center p-3 rounded-xl bg-gray-50 border border-gray-200">
              <p className="text-2xl font-black text-gray-900 tabular-nums">{result.competitors.length}</p>
              <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mt-0.5">Competitors Found</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
