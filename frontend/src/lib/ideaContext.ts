import type { IdeaInput } from '../types'

const NONCOMMERCIAL = [
  'free and open source', 'free open source', 'open-source', 'open source',
  'no payments', 'no payment', 'non-commercial', 'noncommercial',
  'not for profit', 'nonprofit', 'public good', 'community maintained',
]
const COMMERCIAL = [
  'subscription', 'saas', 'transaction fee', 'commission', 'license fee',
  'paid plan', 'freemium', 'per seat', 'monthly fee',
]

export function isNoncommercialIdea(idea: IdeaInput): boolean {
  const text = [
    idea.description, idea.solution, idea.business_model, idea.price,
    idea.revenue_goal, idea.additional_context,
  ].filter(Boolean).join(' ').toLowerCase()
  if (['no payments', 'no payment', 'non-commercial', 'noncommercial'].some((term) => text.includes(term))) return true
  if (idea.price || idea.revenue_goal || COMMERCIAL.some((term) => text.includes(term))) return false
  return NONCOMMERCIAL.some((term) => text.includes(term))
}
