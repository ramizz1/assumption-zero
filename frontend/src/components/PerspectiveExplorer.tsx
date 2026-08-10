import { useState } from 'react'
import type { AnalysisPerspective, EvidenceItem } from '../types'
import { recommendationBg, recommendationColor } from '../lib/utils'
import PerspectivePanel from './PerspectivePanel'

interface Props {
  perspectives: AnalysisPerspective[]
  evidence: EvidenceItem[]
}

export default function PerspectiveExplorer({ perspectives, evidence }: Props) {
  const [selectedName, setSelectedName] = useState<string | null>(null)
  const selected = perspectives.find((item) => item.perspective_name === selectedName) ?? perspectives[0]

  if (!selected) return null

  return (
    <div className="space-y-3">
      <div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-2"
        role="tablist"
        aria-label="AI perspectives"
      >
        {perspectives.map((perspective, index) => {
          const isSelected = perspective.perspective_name === selected.perspective_name

          return (
            <button
              key={perspective.perspective_name}
              type="button"
              id={`perspective-tab-${perspective.perspective_name}`}
              role="tab"
              aria-selected={isSelected}
              aria-controls="selected-perspective"
              onClick={() => setSelectedName(perspective.perspective_name)}
              className={`rounded-2xl border p-3 text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2 ${
                isSelected
                  ? 'border-zinc-900 bg-zinc-950 text-white shadow-lg shadow-zinc-200'
                  : 'border-zinc-200 bg-white text-zinc-900 hover:border-zinc-400 hover:-translate-y-0.5'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className={`text-[10px] font-mono font-bold ${isSelected ? 'text-zinc-400' : 'text-zinc-400'}`}>
                  {String(index + 1).padStart(2, '0')}
                </span>
                <span className={`badge px-2 py-0.5 text-[10px] ${recommendationBg(perspective.recommendation)}`}>
                  <span className={recommendationColor(perspective.recommendation)}>{perspective.recommendation}</span>
                </span>
              </div>
              <span className="mt-3 block text-sm font-display font-bold leading-tight">
                {perspective.perspective_display}
              </span>
              <span className={`mt-1 block truncate text-[10px] font-mono ${isSelected ? 'text-zinc-400' : 'text-zinc-500'}`}>
                {perspective.model_id}
              </span>
            </button>
          )
        })}
      </div>

      <div
        id="selected-perspective"
        role="tabpanel"
        aria-labelledby={`perspective-tab-${selected.perspective_name}`}
      >
        <PerspectivePanel perspective={selected} evidence={evidence} />
      </div>
    </div>
  )
}
