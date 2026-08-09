/** Validation experiment card */
import type { ValidationExperiment } from '../types'

interface Props {
  experiment: ValidationExperiment
  index: number
}

export default function ExperimentCard({ experiment, index }: Props) {
  return (
    <div id={`experiment-${index}`} className="verseo-card p-6 bg-white hover:border-gray-400 hover:shadow-lg transition-all duration-300 relative overflow-hidden">
      <span className="verseo-corner-tl">+</span>
      <span className="verseo-corner-tr">+</span>
      <span className="verseo-corner-bl">+</span>
      <span className="verseo-corner-br">+</span>
      
      <div className="flex items-start gap-4 mb-5 border-b border-gray-100 pb-4">
        <div className="w-8 h-8 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center shrink-0 shadow-sm mt-1">
          <span className="text-xs font-mono font-bold text-gray-900">{index + 1}</span>
        </div>
        <div>
          <h3 className="font-display font-bold text-gray-900 tracking-tight text-lg leading-tight">{experiment.title}</h3>
          <div className="flex gap-4 mt-2">
            <span className="text-xs font-mono text-gray-500 font-medium">⏱ {experiment.estimated_time}</span>
            <span className="text-xs font-mono text-gray-500 font-medium">💰 {experiment.estimated_cost_range}</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1.5">
            Assumption Tested
          </p>
          <p className="text-sm text-gray-900 font-medium leading-relaxed">{experiment.assumption_tested}</p>
        </div>

        <div>
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1.5">
            Why It Matters
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">{experiment.why_it_matters}</p>
        </div>

        <div>
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1.5">
            Procedure
          </p>
          <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 p-3 rounded-xl border border-gray-100">{experiment.procedure}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
            <p className="text-[10px] text-emerald-600 font-bold uppercase tracking-wider mb-1">✓ Success if</p>
            <p className="text-xs text-emerald-900 font-medium">{experiment.success_threshold}</p>
          </div>
          <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl">
            <p className="text-[10px] text-rose-600 font-bold uppercase tracking-wider mb-1">✗ Failure if</p>
            <p className="text-xs text-rose-900 font-medium">{experiment.failure_threshold}</p>
          </div>
        </div>

        <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
          <p className="text-[10px] text-blue-600 font-bold uppercase tracking-wider mb-1">→ Decision After</p>
          <p className="text-xs text-blue-900 font-medium">{experiment.decision_after}</p>
        </div>

        {experiment.legal_ethical && (
          <p className="text-[11px] text-amber-700 font-medium italic pt-2">
            <span className="not-italic mr-1">⚖️</span> {experiment.legal_ethical}
          </p>
        )}
      </div>
    </div>
  )
}
