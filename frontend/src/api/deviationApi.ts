import { deviations } from '../data'
import type { BackendDeviation, Deviation, Severity, Status } from '../types'

const BASE_URL = 'http://localhost:8000/api/v1'

export interface DeviationWritePayload {
  site: string
  occurrence_date: string | null
  title: string
  source: string
  product: string
  batch: string
  severity: Severity
  status: Status
  parameter: string
  approved_min: number | null
  approved_max: number | null
  actual_value: number | null
  duration_minutes: number | null
  description: string
  actions: string
  initial_impact: string
}

export const deviationApi = {
  list: async (): Promise<Deviation[]> => {
    try {
      const response = await fetch(`${BASE_URL}/deviations`)
      if (!response.ok) throw new Error(`Status ${response.status}`)
      const data = await response.json()
      if (!Array.isArray(data) || data.length === 0) return deviations
      return data.map((d: any) => ({
        id: d.code || d.id,
        title: d.title,
        product: d.product,
        batch: d.batch,
        severity: d.severity,
        status: d.status,
        owner: d.owner || 'AIVOA AI',
        created: d.created_at
          ? new Date(d.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
          : 'Today',
        aiAssisted: d.ai_assisted ?? true,
      }))
    } catch (err) {
      console.warn('Backend /deviations unavailable, using mock data:', err)
      return deviations
    }
  },
  get: async (id: string): Promise<BackendDeviation> => {
    const response = await fetch(`${BASE_URL}/deviations/${id}`)
    if (!response.ok) throw new Error(`Status ${response.status}`)
    return await response.json()
  },

  update: async (id: string, payload: DeviationWritePayload & { expected_version: number }): Promise<BackendDeviation> => {
    const response = await fetch(`${BASE_URL}/deviations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!response.ok) throw new Error(`Status ${response.status}`)
    return await response.json()
  },
  create: async (payload: DeviationWritePayload): Promise<BackendDeviation> => {
    const response = await fetch(`${BASE_URL}/deviations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) throw new Error(`Status ${response.status}`)
    return await response.json()
  },
}
