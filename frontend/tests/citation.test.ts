/**
 * Tests for citation badge rendering logic.
 */
import { describe, it, expect } from 'vitest'
import { safeExternalUrl } from '../src/lib/utils'

// Test the citation lookup logic (pure function, no React rendering needed)
function findEvidence(evidenceId: string, evidence: Array<{ evidence_id: string; url: string }>) {
  return evidence.find((e) => e.evidence_id === evidenceId) ?? null
}

const SAMPLE_EVIDENCE = [
  { evidence_id: 'E001', url: 'https://example.com/e1', title: 'Item 1' },
  { evidence_id: 'E002', url: 'https://example.com/e2', title: 'Item 2' },
]

describe('Citation lookup', () => {
  it('finds valid evidence by ID', () => {
    const result = findEvidence('E001', SAMPLE_EVIDENCE)
    expect(result).not.toBeNull()
    expect(result?.evidence_id).toBe('E001')
  })

  it('returns null for invalid evidence ID', () => {
    const result = findEvidence('E999', SAMPLE_EVIDENCE)
    expect(result).toBeNull()
  })

  it('returns null for empty evidence list', () => {
    const result = findEvidence('E001', [])
    expect(result).toBeNull()
  })
})

describe('Citation URL handling', () => {
  it('identifies demo:// URLs correctly', () => {
    const isDemoUrl = (url: string) => url.startsWith('demo://')
    expect(isDemoUrl('demo://fixture')).toBe(true)
    expect(isDemoUrl('https://example.com')).toBe(false)
  })

  it('identifies real external URLs', () => {
    const isExternal = (url: string) => url.startsWith('https://') || url.startsWith('http://')
    expect(isExternal('https://github.com/repo')).toBe(true)
    expect(isExternal('demo://fixture')).toBe(false)
  })

  it('blocks unsafe or malformed source URLs', () => {
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
    expect(safeExternalUrl('demo://fixture')).toBeNull()
    expect(safeExternalUrl('https://example.com/source')).toBe('https://example.com/source')
  })
})
