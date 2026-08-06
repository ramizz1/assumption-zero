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
  groq_api_key?: string
  opencode_api_key?: string
  openai_api_key?: string
  ollama_base_url?: string
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
    let message = res.statusText
    try {
      const data = await res.json()
      message = data.detail || data.message || JSON.stringify(data)
    } catch {
      message = await res.text().catch(() => res.statusText)
    }
    throw new Error(message)
  }
  if (res.status === 204) return undefined as unknown as T
  return res.json()
}

export interface PromptAnalysisRequest {
  prompt: string
  ai_provider?: string
  openrouter_api_key?: string
  groq_api_key?: string
  opencode_api_key?: string
  openai_api_key?: string
  ollama_base_url?: string
  research_providers?: string[]
}

export const api = {
  health(): Promise<HealthResponse> {
    return request('/health')
  },

  createAnalysis(body: AnalysisCreateRequest): Promise<{ analysis_id: string; status: string }> {
    return request('/analyses', { method: 'POST', body: JSON.stringify(body) })
  },

  createAnalysisFromPrompt(body: PromptAnalysisRequest): Promise<{ analysis_id: string; status: string; parsed_idea: IdeaInput }> {
    return request('/analyses/from-prompt', { method: 'POST', body: JSON.stringify(body) })
  },

  listAnalyses(params?: { search?: string; status?: string; limit?: number }): Promise<AnalysisListItem[]> {
    const query = new URLSearchParams()
    if (params?.search) query.append('search', params.search)
    if (params?.status) query.append('status', params.status)
    if (params?.limit) query.append('limit', String(params.limit))
    const qs = query.toString() ? `?${query.toString()}` : ''
    return request(`/analyses${qs}`)
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
