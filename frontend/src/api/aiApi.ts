import type { BackendDeviation, Severity } from '../types'

const BASE_URL = 'http://localhost:8000/api/v1'

const responseError = async (response: Response, fallback: string): Promise<Error> => {
  try {
    const payload = await response.json()
    const detail = payload?.detail
    const message = typeof detail === 'string' ? detail : detail?.message
    return new Error(message || fallback)
  } catch {
    return new Error(fallback)
  }
}

export interface AnalyzeResult {
  deviation_id: string
  recommendation: Severity
  rationale: string
  extracted_fields: Array<{ label: string; value: string; confidence: number; source: string; citation: string }>
  evidence: Array<{ source_id: string; title: string; detail: string; meta: string; relevance: number; kind: 'SOP' | 'CASE' | 'MANUAL'; citation: string }>
  similar_cases: Array<{ code: string; title: string; relevance: number; status: string }>
  conflict_detected: boolean
  trace_id: string
  provider: string
  demo_mode: boolean
}

export interface ChatResult {
  deviation: BackendDeviation
  updated_fields: string[]
  message: string
  rationale: string | null
}

export const aiApi = {
  analyzeText: async (text: string): Promise<AnalyzeResult | null> => {
    try {
      const response = await fetch(`${BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!response.ok) throw await responseError(response, `Backend analyze returned ${response.status}`)
      return await response.json()
    } catch (err) {
      console.error('Backend analyze unavailable:', err)
      throw err
    }
  },

  uploadDocument: async (file: File): Promise<AnalyzeResult | null> => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${BASE_URL}/analyze/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) throw await responseError(response, `Backend analyze upload returned ${response.status}`)
      return await response.json()
    } catch (err) {
      console.error('Backend analyze upload unavailable:', err)
      throw err
    }
  },

  chat: async (deviationId: string, message: string): Promise<ChatResult> => {
    try {
      const response = await fetch(`${BASE_URL}/deviations/${deviationId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      })
      if (!response.ok) throw await responseError(response, `Backend chat returned ${response.status}`)
      return await response.json()
    } catch (err) {
      console.error('Backend chat unavailable:', err)
      throw err
    }
  }
}
