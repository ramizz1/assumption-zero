/** API client for the Assumption Zero backend */

import type {
  AnalysisListItem,
  AnalysisResult,
  HealthResponse,
  IdeaInput,
  ResearchDepth,
} from '../types'
import { safeRequestMessage } from './errors'

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
  return safeRequestMessage(
    message || 'The request could not be completed. Please check your setup and try again.',
  )
}

const OWNER_STORAGE_KEY = 'azero_analysis_owner_v1'
const OWNER_TOKEN_PATTERN = /^[A-Za-z0-9_-]{32,128}$/
let volatileOwnerToken = ''

function createOwnerToken(): string {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join('')
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

export function getAnalysisOwnerToken(): string {
  if (volatileOwnerToken) return volatileOwnerToken

  try {
    const stored = localStorage.getItem(OWNER_STORAGE_KEY) || ''
    if (OWNER_TOKEN_PATTERN.test(stored)) {
      volatileOwnerToken = stored
      return stored
    }
    localStorage.removeItem(OWNER_STORAGE_KEY)
  } catch {
    // Private browsing can disable persistent storage; an in-memory token still isolates the tab.
  }

  volatileOwnerToken = createOwnerToken()
  try {
    localStorage.setItem(OWNER_STORAGE_KEY, volatileOwnerToken)
  } catch {
    // The analysis remains available for the current page lifetime.
  }
  return volatileOwnerToken
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  headers.set('X-Analysis-Owner', getAnalysisOwnerToken())
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,
      headers,
    })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
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

export interface AnalysisProgress {
  type: 'progress' | 'heartbeat'
  stage?: string
  description?: string
  elapsed_seconds: number
}

async function streamAnalysis(
  path: string,
  body: AnalysisCreateRequest | PromptAnalysisRequest,
  onProgress: (event: AnalysisProgress) => void,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) abort()
  let idle = false
  let timer = setTimeout(() => { idle = true; controller.abort() }, 45_000)
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined
  try {
    const response = await fetch(`${BASE}${path}`, {
      method: 'POST', body: JSON.stringify(body), signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Accept: 'application/x-ndjson',
        'X-Analysis-Owner': getAnalysisOwnerToken() },
    })
    if (!response.ok) {
      throw new ApiRequestError(friendlyApiMessage(response.status, await response.text()), response.status)
    }
    if (!response.body) throw new ApiRequestError('No analysis updates were received. Please try again.')
    reader = response.body.getReader()
    const decoder = new TextDecoder()
    let pending = ''
    const parseLine = (line: string): AnalysisResult | undefined => {
      const event = JSON.parse(line)
      if (event.type === 'error') throw new ApiRequestError(safeRequestMessage(event.message))
      if (event.type === 'result') {
        if (!event.result || event.result.status !== 'complete' || !event.result.analysis_id) {
          throw new ApiRequestError('The analysis ended without a complete report. Please try again.')
        }
        return event.result as AnalysisResult
      }
      if (event.type === 'progress' || event.type === 'heartbeat') onProgress(event)
    }
    while (true) {
      const { value, done } = await reader.read()
      clearTimeout(timer)
      timer = setTimeout(() => { idle = true; controller.abort() }, 45_000)
      pending += decoder.decode(value, { stream: !done })
      let newline: number
      while ((newline = pending.indexOf('\n')) >= 0) {
        const line = pending.slice(0, newline).trim()
        pending = pending.slice(newline + 1)
        if (line) { const result = parseLine(line); if (result) return result }
      }
      if (done) {
        if (pending.trim()) { const result = parseLine(pending); if (result) return result }
        throw new ApiRequestError('The connection ended before the report finished. Your idea is still here; try again.')
      }
    }
  } catch (error) {
    if (idle) throw new ApiRequestError('No server updates for 45 seconds. Check your connection and try again.')
    if (signal?.aborted) throw new DOMException('Analysis canceled', 'AbortError')
    if (error instanceof ApiRequestError) throw error
    throw new ApiRequestError(SERVICE_UNAVAILABLE_MESSAGE)
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abort)
    controller.abort()
    await reader?.cancel().catch(() => undefined)
    reader?.releaseLock()
  }
}

export const api = {
  runAnalysisStream(body: AnalysisCreateRequest, onProgress: (event: AnalysisProgress) => void, signal?: AbortSignal) {
    return streamAnalysis('/analyses/stream', body, onProgress, signal)
  },

  runAnalysisFromPromptStream(body: PromptAnalysisRequest, onProgress: (event: AnalysisProgress) => void, signal?: AbortSignal) {
    return streamAnalysis('/analyses/from-prompt/stream', body, onProgress, signal)
  },
  health(): Promise<HealthResponse> {
    return request('/health')
  },

  createAnalysis(body: AnalysisCreateRequest): Promise<{ analysis_id: string; status: string }> {
    return request('/analyses', { method: 'POST', body: JSON.stringify(body) })
  },

  createAnalysisFromPrompt(body: PromptAnalysisRequest): Promise<{ analysis_id: string; status: string; parsed_idea: IdeaInput }> {
    return request('/analyses/from-prompt', { method: 'POST', body: JSON.stringify(body) })
  },

  runAnalysisSync(body: AnalysisCreateRequest, signal?: AbortSignal): Promise<AnalysisResult> {
    return request('/analyses/sync', { method: 'POST', body: JSON.stringify(body), signal })
  },

  runAnalysisFromPromptSync(body: PromptAnalysisRequest, signal?: AbortSignal): Promise<AnalysisResult> {
    return request('/analyses/from-prompt/sync', { method: 'POST', body: JSON.stringify(body), signal })
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
    return request(`/analyses/${encodeURIComponent(id)}`)
  },

  deleteAnalysis(id: string): Promise<void> {
    return request(`/analyses/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  runDemo(settings?: DemoAnalysisRequest): Promise<{ analysis_id: string; status: string; demo: boolean }> {
    return request('/demo', {
      method: 'POST',
      body: settings ? JSON.stringify(settings) : undefined,
    })
  },

  verifyKeys(settings: Partial<AnalysisCreateRequest>): Promise<{ status: string; provider: string; message: string }> {
    return request('/verify-keys', { method: 'POST', body: JSON.stringify(settings) })
  },
}
