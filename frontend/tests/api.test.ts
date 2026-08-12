import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiRequestError } from '../src/lib/api'

describe('API error handling', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('turns an HTML 404 into a safe service message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('<!doctype html><h1>Not Found</h1>', { status: 404 }),
    ))

    await expect(api.health()).rejects.toMatchObject({
      name: 'ApiRequestError',
      status: 404,
      message: expect.stringContaining('temporarily unavailable'),
    } satisfies Partial<ApiRequestError>)
  })

  it('never exposes raw HTML or a generic unexpected-error message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('<html>private platform error</html>', { status: 500 }),
    ))

    try {
      await api.health()
      throw new Error('Expected health to fail')
    } catch (error) {
      const message = (error as Error).message
      expect(message).not.toContain('<html>')
      expect(message).not.toContain('An unexpected error occurred')
      expect(message).not.toContain('private platform error')
    }
  })
})
