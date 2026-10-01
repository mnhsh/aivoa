import { afterEach, describe, expect, it, vi } from 'vitest'

import { aiApi } from './aiApi'

describe('aiApi.chat', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns the backend change set and updated deviation', async () => {
    const response = {
      deviation: { id: 'dev-1', batch: 'MET-3390', severity: 'High', version: 2 },
      updated_fields: ['batch', 'severity'],
      message: 'Updated batch, severity.',
      rationale: 'High is required by the excursion rule.',
    }
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => response })
    vi.stubGlobal('fetch', fetchMock)

    const result = await aiApi.chat('dev-1', 'Change the batch to MET-3390')

    expect(result.updated_fields).toEqual(['batch', 'severity'])
    expect(result.deviation.severity).toBe('High')
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/deviations/dev-1/chat',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('preserves structured backend rejection messages', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: {
          code: 'not_quality_deviation',
          message: 'The pasted content is an application error or stack trace.',
        },
      }),
    }))

    await expect(aiApi.analyzeText('Traceback...')).rejects.toThrow(
      'The pasted content is an application error or stack trace.',
    )
  })
})
