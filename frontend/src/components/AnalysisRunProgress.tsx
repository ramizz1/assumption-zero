import type { ResearchDepth } from '../types'
import type { AnalysisProgress } from '../lib/api'

export const ANALYSIS_REQUEST_TIMEOUT_MS = 270_000
const STAGES = [
  ['starting_analysis', 'Connecting'], ['parsing_idea', 'Understanding your idea'],
  ['clarifying_idea', 'Clarifying assumptions'], ['generating_queries', 'Planning research'],
  ['collecting_evidence', 'Collecting evidence'], ['finding_competitors', 'Finding competitors'],
  ['running_perspectives', 'Analyzing evidence'], ['checking_citations', 'Checking citations'],
  ['calculating_scores', 'Evaluating the opportunity'],
  ['generating_experiments', 'Preparing your action plan'], ['complete', 'Saving your report'],
]

export function formatElapsedTime(elapsedSeconds: number): string {
  const seconds = Math.max(0, Math.floor(elapsedSeconds))
  return seconds >= 60 ? `${Math.floor(seconds / 60)}m ${(seconds % 60).toString().padStart(2, '0')}s` : `${seconds}s`
}

export default function AnalysisRunProgress({ depth, elapsedSeconds, progress, lastUpdateSeconds, onCancel }: {
  depth: ResearchDepth
  elapsedSeconds: number
  progress: AnalysisProgress | null
  lastUpdateSeconds: number
  onCancel: () => void
}) {
  const index = Math.max(0, STAGES.findIndex(([stage]) => stage === progress?.stage))
  const waiting = elapsedSeconds - lastUpdateSeconds > 25
  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-left" aria-label="Analysis progress">
      <div className="flex justify-between gap-4">
        <div role="status" aria-live="polite">
          <p className="text-xs font-mono text-zinc-600">Analysis in progress</p>
          <p className="mt-1 text-sm font-bold text-zinc-950">{STAGES[index][1]}</p>
          <p className="mt-1 text-xs text-zinc-600">{progress?.description || 'Waiting for the server to accept your request.'}</p>
        </div>
        <span className="shrink-0 text-xs font-mono tabular-nums">{formatElapsedTime(elapsedSeconds)}</span>
      </div>
      <div role="progressbar" aria-label="Analysis stages" aria-valuemin={0} aria-valuemax={STAGES.length}
        aria-valuenow={index} aria-valuetext={`${STAGES[index][1]} — server-reported stage`}
        className="mt-3 h-2.5 overflow-hidden rounded-full bg-white">
        <div className="h-full rounded-full bg-emerald-700 transition-[width] duration-300" style={{ width: `${Math.max(3, index / STAGES.length * 100)}%` }} />
      </div>
      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-[11px] text-zinc-600">{waiting ? 'Waiting for the next server update…' : 'Live server updates'} · {depth} research</p>
        <button type="button" onClick={onCancel} className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs font-bold">Cancel</button>
      </div>
    </section>
  )
}
