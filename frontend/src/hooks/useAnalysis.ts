/** useAnalysis hook — polls the API until the analysis completes */
import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { getBundledDemo } from '../lib/bundledDemo'
import type { AnalysisResult } from '../types'

const POLL_INTERVAL = 2500 // ms

export function useAnalysis(analysisId: string | null) {
  const [data, setData] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!analysisId) return

    const bundledDemo = getBundledDemo(analysisId)
    if (bundledDemo) {
      setData(bundledDemo)
      setError(null)
      return
    }

    const poll = async () => {
      try {
        const result = await api.getAnalysis(analysisId)
        setData(result)

        if (result.status === 'complete' || result.status === 'failed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    }

    // Fetch immediately then poll
    poll()
    intervalRef.current = setInterval(poll, POLL_INTERVAL)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [analysisId])

  return { data, error }
}
