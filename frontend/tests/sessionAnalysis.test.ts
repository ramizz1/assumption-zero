import { describe, expect, it } from 'vitest'
import demo from '../src/data/demo-analysis.json'
import { getSessionAnalyses, getSessionAnalysis, saveSessionAnalysis } from '../src/lib/sessionAnalysis'
import type { AnalysisResult } from '../src/types'

describe('session analysis cache', () => {
  it('keeps completed reports in session storage for serverless navigation', () => {
    const result = { ...demo, analysis_id: 'session-result-1', is_demo: false } as unknown as AnalysisResult
    saveSessionAnalysis(result)
    expect(getSessionAnalysis('session-result-1')?.analysis_id).toBe('session-result-1')
    expect(getSessionAnalyses().some((item) => item.analysis_id === 'session-result-1')).toBe(true)
  })
})
