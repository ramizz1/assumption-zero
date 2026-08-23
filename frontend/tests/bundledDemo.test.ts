import { describe, expect, it } from 'vitest'

import { BUNDLED_DEMO_ID, getBundledDemo } from '../src/lib/bundledDemo'

describe('bundled public demo', () => {
  it('loads a complete, evidence-backed report without credentials', () => {
    const demo = getBundledDemo(BUNDLED_DEMO_ID)
    const serialized = JSON.stringify(demo).toLowerCase()

    expect(demo?.status).toBe('complete')
    expect(demo?.is_demo).toBe(true)
    expect(demo?.evidence.length).toBeGreaterThanOrEqual(8)
    expect(demo?.evidence.some((item) => item.url.includes('americanbar.org'))).toBe(true)
    expect(demo?.evidence.some((item) => item.url.includes('github.com/openai/whisper'))).toBe(true)
    expect(demo?.experiments).toHaveLength(5)
    expect(new Set(demo?.experiments.map((item) => item.test_type)).size).toBe(5)
    for (const experiment of demo?.experiments || []) {
      expect(experiment.target_sample).toBeTruthy()
      expect(experiment.primary_metric).toBeTruthy()
      expect(experiment.data_to_capture.length).toBeGreaterThanOrEqual(4)
      expect(experiment.success_threshold).toBeTruthy()
      expect(experiment.failure_threshold).toBeTruthy()
      expect(experiment.decision_after).toBeTruthy()
      expect(experiment.budget_rationale).toBeTruthy()
    }
    expect(demo?.founder_toolkit?.demand_snapshot.length).toBeGreaterThanOrEqual(5)
    expect(demo?.founder_toolkit?.budget_allocation.length).toBeGreaterThanOrEqual(5)
    expect(demo?.founder_toolkit?.budget_release_rules.length).toBeGreaterThanOrEqual(4)
    expect(serialized).not.toContain('api_key')
    expect(serialized).not.toContain('bearer ')
    expect(serialized).not.toContain('sk-')
  })
})
