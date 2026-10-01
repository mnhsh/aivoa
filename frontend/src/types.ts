export type Severity = 'Low' | 'Medium' | 'High' | 'Critical'
export type Status = 'Under Review' | 'Draft' | 'Closed' | 'Investigation'

export interface BackendDeviation {
  id: string
  code: string
  site: string
  occurrence_date: string | null
  title: string
  source: string
  product: string
  batch: string
  severity: Severity
  status: Status
  owner: string
  parameter: string
  approved_min: number | null
  approved_max: number | null
  actual_value: number | null
  duration_minutes: number | null
  description: string
  actions: string
  initial_impact: string
  version: number
}

export interface Deviation {
  id: string
  title: string
  product: string
  batch: string
  severity: Severity
  status: Status
  owner: string
  created: string
  aiAssisted: boolean
}

export interface Evidence {
  id: string
  title: string
  detail: string
  meta: string
  relevance: number
  kind: 'SOP' | 'CASE' | 'MANUAL'
}

export interface ExtractedField {
  label: string
  value: string
  confidence: number
  source: string
}
