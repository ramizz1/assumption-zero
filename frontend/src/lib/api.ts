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

const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export class ApiRequestError extends Error {
  status: number | null

  constructor(message: string, status: number | null = null) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
  }
}

const SERVICE_UNAVAILABLE_MESSAGE =
  'Live AI analysis is temporarily unavailable. Your API key was not saved or exposed. Please try again shortly.'

function friendlyApiMessage(status: number, raw: string): string {
  const contentTypeLooksLikeHtml = /<!doctype|<html|<body/i.test(raw)
  if (status === 404 || status >= 500 || contentTypeLooksLikeHtml) {
    return SERVICE_UNAVAILABLE_MESSAGE
  }

  let message = raw
  try {
    const data = raw ? JSON.parse(raw) : {}
    if (Array.isArray(data.detail)) {
      message = data.detail
        .map((detail: { msg?: string } | string) =>
          typeof detail === 'string' ? detail : detail.msg || '',
        )
        .filter(Boolean)
        .join(' ')
    } else if (typeof data.detail === 'string') {
      message = data.detail
    } else if (typeof data.message === 'string') {
      message = data.message
    }
  } catch {
    // Plain-text API responses are handled below. HTML is never shown to users.
  }

  message = message
    .replace(/For further information visit https:\/\/errors\.pydantic\.dev\/[^\s]+/g, '')
    .replace(/\[type=[^\]]+\]/g, '')
    .replace(/^\d+ validation error(s)? for [^\n:]+:\s*/gi, '')
    .trim()

  if (message.startsWith('Value error, ')) message = message.slice('Value error, '.length)
  return message || 'The request could not be completed. Please check your setup and try again.'
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new ApiRequestError(SERVICE_UNAVAILABLE_MESSAGE)
  }

  const raw = res.status === 204 ? '' : await res.text()
  if (!res.ok) {
    throw new ApiRequestError(friendlyApiMessage(res.status, raw), res.status)
  }
  if (res.status === 204) return undefined as unknown as T
  try {
    return JSON.parse(raw) as T
  } catch {
    throw new ApiRequestError(SERVICE_UNAVAILABLE_MESSAGE, res.status)
  }
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

  runAnalysisSync(body: AnalysisCreateRequest): Promise<AnalysisResult> {
    return request('/analyses/sync', { method: 'POST', body: JSON.stringify(body) })
  },

  runAnalysisFromPromptSync(body: PromptAnalysisRequest): Promise<AnalysisResult> {
    return request('/analyses/from-prompt/sync', { method: 'POST', body: JSON.stringify(body) })
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
