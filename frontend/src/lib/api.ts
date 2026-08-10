/** API client for the Assumption Zero backend */

import type {
  AnalysisListItem,
  AnalysisResult,
  HealthResponse,
  IdeaInput,
  ResearchDepth,
} from '../types'

export interface AnalysisCreateRequest {
  idea: IdeaInput
  ai_provider?: string
  openrouter_api_key?: string
  groq_api_key?: string
  opencode_api_key?: string
  openai_api_key?: string
  custom_base_url?: string
  ollama_base_url?: string
  research_providers?: string[]
  research_depth?: ResearchDepth
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
      if (Array.isArray(data.detail)) {
        message = data.detail
          .map((d: any) => (typeof d === 'string' ? d : d.msg || JSON.stringify(d)))
          .join(' ')
      } else if (typeof data.detail === 'string') {
        message = data.detail
      } else if (data.message) {
        message = data.message
      } else {
        message = JSON.stringify(data)
      }
    } catch {
      message = await res.text().catch(() => res.statusText)
    }

    // Clean up Pydantic type tags & URLs
    message = message
      .replace(/For further information visit https:\/\/errors\.pydantic\.dev\/[^\s]+/g, '')
      .replace(/\[type=[^\]]+\]/g, '')
      .replace(/^\d+ validation error(s)? for [^\n:]+:\s*/gi, '')
      .trim()

    if (message.startsWith('Value error, ')) {
      message = message.replace('Value error, ', '')
    }

    throw new Error(message || 'An unexpected error occurred.')
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
  custom_base_url?: string
  ollama_base_url?: string
  research_providers?: string[]
  research_depth?: ResearchDepth
}

export type DemoAnalysisRequest = Omit<AnalysisCreateRequest, 'idea'>

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

  runDemo(settings?: DemoAnalysisRequest): Promise<{ analysis_id: string; status: string; demo: boolean }> {
    return request('/demo', {
      method: 'POST',
      body: settings ? JSON.stringify(settings) : undefined,
    })
  },

  verifyKeys(settings: Record<string, any>): Promise<{ status: string; provider: string; message: string }> {
    return request('/verify-keys', { method: 'POST', body: JSON.stringify(settings) })
  },
}
