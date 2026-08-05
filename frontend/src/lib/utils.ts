/** Utility functions for formatting and display */

import type { ConfidenceLevel, Recommendation } from '../types'

export function scoreColor(score: number): string {
  if (score >= 65) return 'text-green-400'
  if (score >= 45) return 'text-amber-400'
  return 'text-red-400'
}

export function scoreBgColor(score: number): string {
  if (score >= 65) return 'bg-green-400'
  if (score >= 45) return 'bg-amber-400'
  return 'bg-red-400'
}

export function scoreBorderColor(score: number): string {
  if (score >= 65) return 'border-green-500'
  if (score >= 45) return 'border-amber-500'
  return 'border-red-500'
}

export function recommendationColor(rec: Recommendation): string {
  const map: Record<Recommendation, string> = {
    Build: 'text-green-400',
    'Test First': 'text-amber-400',
    Pivot: 'text-orange-400',
    Avoid: 'text-red-400',
  }
  return map[rec] ?? 'text-gray-300'
}

export function recommendationBg(rec: Recommendation): string {
  const map: Record<Recommendation, string> = {
    Build: 'bg-green-400/10 border-green-500/30',
    'Test First': 'bg-amber-400/10 border-amber-500/30',
    Pivot: 'bg-orange-400/10 border-orange-500/30',
    Avoid: 'bg-red-400/10 border-red-500/30',
  }
  return map[rec] ?? 'bg-gray-800/50 border-gray-700'
}

export function confidenceColor(conf: ConfidenceLevel): string {
  const map: Record<ConfidenceLevel, string> = {
    high: 'text-green-400',
    medium: 'text-amber-400',
    low: 'text-red-400',
  }
  return map[conf] ?? 'text-gray-400'
}

export function reliabilityBadge(level: string): string {
  if (level === 'high') return 'bg-green-400/10 text-green-300 border-green-500/20'
  if (level === 'medium') return 'bg-amber-400/10 text-amber-300 border-amber-500/20'
  return 'bg-red-400/10 text-red-300 border-red-500/20'
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
