/** Utility functions for formatting and display */

import type { ConfidenceLevel, Recommendation } from '../types'

export function scoreColor(score: number): string {
  if (score >= 65) return 'text-emerald-600'
  if (score >= 45) return 'text-amber-600'
  return 'text-rose-600'
}

export function scoreBgColor(score: number): string {
  if (score >= 65) return 'bg-emerald-600'
  if (score >= 45) return 'bg-amber-600'
  return 'bg-rose-600'
}

export function scoreBorderColor(score: number): string {
  if (score >= 65) return 'border-emerald-500'
  if (score >= 45) return 'border-amber-500'
  return 'border-rose-500'
}

export function recommendationColor(rec: Recommendation): string {
  const map: Record<Recommendation, string> = {
    Build: 'text-emerald-700',
    'Test First': 'text-amber-700',
    Pivot: 'text-orange-700',
    Avoid: 'text-rose-700',
  }
  return map[rec] ?? 'text-gray-700'
}

export function recommendationBg(rec: Recommendation): string {
  const map: Record<Recommendation, string> = {
    Build: 'bg-emerald-50 border-emerald-200',
    'Test First': 'bg-amber-50 border-amber-200',
    Pivot: 'bg-orange-50 border-orange-200',
    Avoid: 'bg-rose-50 border-rose-200',
  }
  return map[rec] ?? 'bg-gray-100 border-gray-200'
}

export function confidenceColor(conf: ConfidenceLevel): string {
  const map: Record<ConfidenceLevel, string> = {
    high: 'text-emerald-600',
    medium: 'text-amber-600',
    low: 'text-rose-600',
  }
  return map[conf] ?? 'text-gray-600'
}

export function reliabilityBadge(level: string): string {
  if (level === 'high') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (level === 'medium') return 'bg-amber-50 text-amber-700 border-amber-200'
  return 'bg-rose-50 text-rose-700 border-rose-200'
}

export function formatDate(iso?: string): string {
  if (!iso) return 'Unknown'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}

export function stageLabel(stage: string): string {
  const labels: Record<string, string> = {
    clarifying_idea: 'Clarifying Idea',
    generating_queries: 'Generating Queries',
    collecting_evidence: 'Collecting Evidence',
    finding_competitors: 'Finding Competitors',
    running_perspectives: 'Running AI Perspectives',
    checking_citations: 'Validating Citations',
    calculating_scores: 'Calculating Scores',
    generating_experiments: 'Generating Experiments',
    complete: 'Complete',
  }
  return labels[stage] ?? stage
}

export const DISCLAIMER =
  'Assumption Zero provides decision support, not a prediction or substitute for real customer validation.'
