const CAPACITY_PATTERN = /(?:\b402\b|\b429\b|rate[ -]?limit|quota|token limit|out of (?:tokens|credits)|credit balance|generation capacity)/i
const AUTH_PATTERN = /(?:\b401\b|unauthori[sz]ed|invalid api key|key (?:was )?rejected|rejected the configured key)/i
const TEMPORARY_PATTERN = /(?:timeout|timed out|network|unreachable|temporarily unavailable|\b50[234]\b)/i
const INTERNAL_PATTERN = /(?:fallback-chain|perspective\s+[\w-]+\s+failed|openrouter\/|groq\/|ollama\/|opencode\/|openai-compat\/|https?:\/\/|traceback|runtimeerror|chat\/completions|api[_ -]?key\s*[:=]\s*\S+)/i

export const AI_CAPACITY_MESSAGE =
  'No AI generation capacity is available for this key right now. It may have reached its token or rate limit. Wait briefly, check the provider balance, or choose another provider.'

export const AI_AUTH_MESSAGE =
  'The AI provider rejected the configured key. Re-enter or verify it in AI Setup.'

export const AI_TEMPORARY_MESSAGE =
  'The AI service is temporarily unavailable. Your API key was not saved or exposed. Try again shortly or choose another provider.'

export const AI_GENERIC_MESSAGE =
  'The AI service could not complete the analysis. Verify AI Setup and try again.'

function cleanText(value?: string | null): string {
  return (value || '').replace(/<[^>]+>/g, '').replace(/[\u0000-\u001f\u007f]/g, ' ').trim()
}

export function isAiCapacityError(value?: string | null): boolean {
  return CAPACITY_PATTERN.test(cleanText(value))
}

export function safeAnalysisMessage(value?: string | null): string {
  const message = cleanText(value)
  if (CAPACITY_PATTERN.test(message)) return AI_CAPACITY_MESSAGE
  if (AUTH_PATTERN.test(message)) return AI_AUTH_MESSAGE
  if (TEMPORARY_PATTERN.test(message)) return AI_TEMPORARY_MESSAGE
  return AI_GENERIC_MESSAGE
}

export function safeRequestMessage(value?: string | null): string {
  const message = cleanText(value)
  if (!message || INTERNAL_PATTERN.test(message)) return safeAnalysisMessage(message)
  if (CAPACITY_PATTERN.test(message) || AUTH_PATTERN.test(message) || TEMPORARY_PATTERN.test(message)) {
    return safeAnalysisMessage(message)
  }
  return message.slice(0, 400)
}

export function analysisErrorTitle(value?: string | null): string {
  if (isAiCapacityError(value)) return 'No AI Capacity Available'
  if (AUTH_PATTERN.test(cleanText(value))) return 'AI Key Rejected'
  return 'Analysis Could Not Finish'
}
