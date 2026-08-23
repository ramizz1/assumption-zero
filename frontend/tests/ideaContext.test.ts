import { describe, expect, it } from 'vitest'

import { isNoncommercialIdea } from '../src/lib/ideaContext'
import type { IdeaInput } from '../src/types'

const baseIdea: IdeaInput = {
  name: 'OpenClinic',
  description: 'Scheduling software for community clinics',
  problem: 'Clinic scheduling is fragmented',
  target_customer: 'Community clinic operators',
  geography: 'Global',
}

describe('idea model classification', () => {
  it('recognizes an explicitly free open-source project', () => {
    expect(isNoncommercialIdea({
      ...baseIdea,
      description: 'A free and open-source scheduling project with no payments',
      business_model: 'Free and open source; no payments',
    })).toBe(true)
  })

  it('keeps commercial and ambiguous ideas on the commercial path', () => {
    expect(isNoncommercialIdea({
      ...baseIdea,
      business_model: 'SaaS subscription',
      price: '$20 per month',
    })).toBe(false)
    expect(isNoncommercialIdea(baseIdea)).toBe(false)
  })
})
