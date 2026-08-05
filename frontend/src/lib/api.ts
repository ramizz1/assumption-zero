/** API client for the Assumption Zero backend */

import type {
  AnalysisListItem,
  AnalysisResult,
  HealthResponse,
  IdeaInput,
} from '../types'

export interface AnalysisCreateRequest {
  idea: IdeaInput
  ai_provider_override?: string
  openrouter_api_key?: string
  research_providers?: string[]
}

const BASE = '/api'

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${text}`)
  }
  if (res.status === 204) return undefined as unknown as T
  return res.json()
}

export interface PromptAnalysisRequest {
  prompt: str
  ai_provider?: string
  openrouter_api_key?: string
  research_providers?: string[]
}

export const api = {
  health(): Promise<HealthResponse> {
    return request('/health')
  },

  createAnalysis(body: AnalysisCreateRequest): Promise<{ analysis_id: string; status: string }> {
    return request('/analyses', { method: 'POST', body: JSON.stringify(body) })
  },

  createAnalysisFromPrompt(body: { prompt: string; openrouter_api_key?: string }): Promise<{ analysis_id: string; status: string; parsed_idea: IdeaInput }> {
    return request('/analyses/from-prompt', { method: 'POST', body: JSON.stringify(body) })
  },

  listAnalyses(): Promise<AnalysisListItem[]> {
    return request('/analyses')
  },

  getAnalysis(id: string): Promise<AnalysisResult> {
    return request(`/analyses/${id}`)
  },

  deleteAnalysis(id: string): Promise<void> {
    return request(`/analyses/${id}`, { method: 'DELETE' })
  },

  runDemo(): Promise<{ analysis_id: string; status: string; demo: boolean }> {
    return request('/demo', { method: 'POST' })
  },
}
