import rawDemo from '../data/demo-analysis.json'
import type { AnalysisResult } from '../types'

export const BUNDLED_DEMO_ID = 'demo-legalmind-local'

export function getBundledDemo(analysisId: string | null): AnalysisResult | null {
  if (analysisId !== BUNDLED_DEMO_ID) return null

  return {
    ...(rawDemo as unknown as AnalysisResult),
    analysis_id: BUNDLED_DEMO_ID,
    is_demo: true,
  }
}
