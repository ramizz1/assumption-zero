import type { AnalysisResult } from '../types'

const PREFIX = 'assumption-zero:analysis:'
const INDEX_KEY = 'assumption-zero:analysis-index'

export function saveSessionAnalysis(result: AnalysisResult): void {
  try {
    sessionStorage.setItem(`${PREFIX}${result.analysis_id}`, JSON.stringify(result))
    const ids = JSON.parse(sessionStorage.getItem(INDEX_KEY) || '[]') as string[]
    sessionStorage.setItem(
      INDEX_KEY,
      JSON.stringify([result.analysis_id, ...ids.filter((id) => id !== result.analysis_id)].slice(0, 20)),
    )
  } catch {
    // The result still renders immediately when storage is unavailable.
  }
}

export function getSessionAnalyses(): AnalysisResult[] {
  try {
    const ids = JSON.parse(sessionStorage.getItem(INDEX_KEY) || '[]') as string[]
    return ids.map(getSessionAnalysis).filter((item): item is AnalysisResult => item !== null)
  } catch {
    return []
  }
}

export function removeSessionAnalysis(id: string): void {
  try {
    sessionStorage.removeItem(`${PREFIX}${id}`)
    const ids = JSON.parse(sessionStorage.getItem(INDEX_KEY) || '[]') as string[]
    sessionStorage.setItem(INDEX_KEY, JSON.stringify(ids.filter((item) => item !== id)))
  } catch {
    // Nothing else is required when browser storage is unavailable.
  }
}

export function getSessionAnalysis(id: string): AnalysisResult | null {
  try {
    const raw = sessionStorage.getItem(`${PREFIX}${id}`)
    return raw ? (JSON.parse(raw) as AnalysisResult) : null
  } catch {
    return null
  }
}
