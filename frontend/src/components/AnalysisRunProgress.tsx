import React from 'react'
import type { ResearchDepth } from '../types'

export const ANALYSIS_REQUEST_TIMEOUT_MS = 270_000

const EXPECTED_SECONDS: Record<ResearchDepth, number> = {
  standard: 75,
  deep: 135,
  exhaustive: 240,
}

const DEPTH_LABELS: Record<ResearchDepth, string> = {
  standard: 'Standard',
  deep: 'Deep regional',
  exhaustive: 'Exhaustive',
}

export interface AnalysisRunEstimate {
  percent: number
  phase: string
  detail: string
  delayed: boolean
}

export function formatElapsedTime(elapsedSeconds: number): string {
  const seconds = Math.max(0, Math.floor(elapsedSeconds))
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds % 60
  return minutes > 0 ? `${minutes}m ${remainder.toString().padStart(2, '0')}s` : `${remainder}s`
}

export function estimateAnalysisRun(
  elapsedSeconds: number,
  depth: ResearchDepth,
): AnalysisRunEstimate {
  const expectedSeconds = EXPECTED_SECONDS[depth]
  const ratio = Math.max(0, elapsedSeconds) / expectedSeconds
  const percent = Math.min(94, Math.round(8 + Math.min(1, ratio) * 82))

  if (ratio < 0.08) {
    return {
      percent,
      phase: 'Connecting to the AI provider',
      detail: 'Starting the selected model and checking the analysis request.',
      delayed: false,
    }
  }
  if (ratio < 0.18) {
    return {
      percent,
      phase: 'Understanding your idea',
      detail: 'Extracting the customer, problem, offer, geography, and assumptions.',
      delayed: false,
    }
  }
  if (ratio < 0.55) {
    return {
      percent,
      phase: 'Collecting live market evidence',
      detail: 'Searching multiple sources and deduplicating useful evidence.',
      delayed: false,
    }
  }
  if (ratio < 0.88) {
    return {
      percent,
      phase: 'Running independent AI perspectives',
      detail: 'Comparing market, customer, regional, investor, and builder viewpoints.',
      delayed: false,
    }
  }

  return {
    percent,
    phase: 'Checking citations and finishing the report',
    detail: ratio >= 1
      ? 'Still working—provider response times vary. The request will stop safely before the hosting limit.'
      : 'Scoring the evidence and preparing experiments and recommendations.',
    delayed: ratio >= 1,
  }
}

interface AnalysisRunProgressProps {
  depth: ResearchDepth
  elapsedSeconds: number
  onCancel: () => void
}

const AnalysisRunProgress: React.FC<AnalysisRunProgressProps> = ({
  depth,
  elapsedSeconds,
  onCancel,
}) => {
  const estimate = estimateAnalysisRun(elapsedSeconds, depth)
  const elapsed = formatElapsedTime(elapsedSeconds)

  return (
    <div
      className={`rounded-2xl border p-4 text-left ${
        estimate.delayed ? 'border-amber-300 bg-amber-50' : 'border-emerald-200 bg-emerald-50'
      }`}
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-700">
            Analysis in progress
          </p>
          <p className="mt-1 text-sm font-bold text-zinc-950">{estimate.phase}</p>
        </div>
        <span className="shrink-0 font-mono text-xs font-bold tabular-nums text-zinc-600">
          {elapsed}
        </span>
      </div>

      <div
        className="mt-3 h-2.5 overflow-hidden rounded-full border border-black/5 bg-white"
        role="progressbar"
        aria-label="Estimated analysis progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={estimate.percent}
        aria-valuetext={`${estimate.percent}% estimated, ${estimate.phase}`}
      >
        <div
          className="h-full rounded-full bg-emerald-700 transition-[width] duration-1000 ease-linear"
          style={{ width: `${estimate.percent}%` }}
        />
      </div>

      <div className="mt-2 flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] leading-relaxed text-zinc-700">{estimate.detail}</p>
          <p className="mt-1 text-[10px] font-mono text-zinc-500">
            {estimate.percent}% estimated · {DEPTH_LABELS[depth]} research · exact timing depends on live providers
          </p>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="shrink-0 rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-[11px] font-bold text-zinc-700 transition-colors hover:border-zinc-500 hover:text-zinc-950"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

export default AnalysisRunProgress
