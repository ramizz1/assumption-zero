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
    expect(serialized).not.toContain('api_key')
    expect(serialized).not.toContain('bearer ')
    expect(serialized).not.toContain('sk-')
  })
})
