/** Validation experiment card */
import type { ValidationExperiment } from '../types'

interface Props {
  experiment: ValidationExperiment
  index: number
}

export default function ExperimentCard({ experiment, index }: Props) {
  return (
    <div id={`experiment-${index}`} className="card p-5 hover:border-cyan-800/50 transition-colors">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-7 h-7 rounded-full bg-cyan-400/10 border border-cyan-500/30 flex items-center justify-center shrink-0">
          <span className="text-xs font-bold text-cyan-400">{index}</span>
        </div>
        <div>
          <h3 className="font-semibold text-white">{experiment.title}</h3>
          <div className="flex gap-3 mt-1">
            <span className="text-xs text-gray-500">⏱ {experiment.estimated_time}</span>
            <span className="text-xs text-gray-500">💰 {experiment.estimated_cost_range}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">
            Assumption Tested
          </p>
          <p className="text-sm text-gray-200">{experiment.assumption_tested}</p>
        </div>

        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">
            Why It Matters
          </p>
          <p className="text-sm text-gray-400">{experiment.why_it_matters}</p>
        </div>

        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">
            Procedure
          </p>
          <p className="text-sm text-gray-400 leading-relaxed">{experiment.procedure}</p>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="p-3 bg-green-400/5 border border-green-500/20 rounded-lg">
            <p className="text-xs text-green-500/70 font-medium mb-1">✓ Success if</p>
            <p className="text-xs text-green-300/80">{experiment.success_threshold}</p>
          </div>
          <div className="p-3 bg-red-400/5 border border-red-500/20 rounded-lg">
            <p className="text-xs text-red-500/70 font-medium mb-1">✗ Failure if</p>
            <p className="text-xs text-red-300/80">{experiment.failure_threshold}</p>
          </div>
        </div>

        <div className="p-3 bg-blue-400/5 border border-blue-500/20 rounded-lg">
          <p className="text-xs text-blue-500/70 font-medium mb-1">→ After the result</p>
          <p className="text-xs text-blue-300/80">{experiment.decision_after}</p>
        </div>

        {experiment.legal_ethical && (
          <p className="text-xs text-amber-400/60 italic">
            ⚖ {experiment.legal_ethical}
          </p>
        )}
      </div>
    </div>
  )
}
