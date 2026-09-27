export type Severity = 'Low' | 'Medium' | 'High' | 'Critical'
export type Status = 'Under Review' | 'Draft' | 'Closed' | 'Investigation'

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
