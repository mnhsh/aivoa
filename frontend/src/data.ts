import type { Deviation, Evidence, ExtractedField } from './types'

export const deviations: Deviation[] = [
  { id: 'DEV-2026-0042', title: 'Temperature excursion during API processing', product: 'API-ACM-01', batch: 'B240918', severity: 'High', status: 'Under Review', owner: 'Sarah Mitchell', created: 'Sep 26, 2026', aiAssisted: true },
  { id: 'DEV-2026-0041', title: 'Granulation endpoint detected late', product: 'API-ACM-02', batch: 'B240917', severity: 'Medium', status: 'Investigation', owner: 'James Wu', created: 'Sep 25, 2026', aiAssisted: true },
  { id: 'DEV-2026-0039', title: 'Raw material label mismatch', product: 'API-BXR-04', batch: 'B240912', severity: 'Low', status: 'Closed', owner: 'Priya Nair', created: 'Sep 23, 2026', aiAssisted: false },
  { id: 'DEV-2026-0037', title: 'Differential pressure below alert limit', product: 'API-ACM-01', batch: 'B240908', severity: 'High', status: 'Under Review', owner: 'Sarah Mitchell', created: 'Sep 20, 2026', aiAssisted: true },
  { id: 'DEV-2026-0034', title: 'Cleaning log entry omitted', product: 'API-CZM-08', batch: 'B240901', severity: 'Medium', status: 'Closed', owner: 'Arun Das', created: 'Sep 16, 2026', aiAssisted: false },
]

export const evidence: Evidence[] = [
  { id: 'SOP-DEV-004', title: 'Deviation Classification Procedure', detail: 'Section 4.2', meta: 'SOP · v3.2 · Active', relevance: 94, kind: 'SOP' },
  { id: 'DEV-2025-0187', title: 'Similar temperature excursion', detail: 'Batch investigated', meta: 'Historical deviation · Closed', relevance: 89, kind: 'CASE' },
  { id: 'QMS-012', title: 'Process Parameter Excursions', detail: 'Quality Manual', meta: 'Quality manual · v5.1 · Active', relevance: 86, kind: 'MANUAL' },
]

export const extractedFields: ExtractedField[] = [
  { label: 'Batch Number', value: 'B240918', confidence: 96, source: 'Deviation_Report_240918.pdf' },
  { label: 'Product', value: 'API-ACM-01', confidence: 94, source: 'Deviation_Report_240918.pdf' },
  { label: 'Parameter', value: 'Reactor Temperature', confidence: 98, source: 'Deviation_Report_240918.pdf' },
  { label: 'Actual Value', value: '86.5°C', confidence: 97, source: 'Deviation_Report_240918.pdf' },
  { label: 'Duration', value: '18 minutes', confidence: 91, source: 'Deviation_Report_240918.pdf' },
]

export const auditEvents = [
  ['14:32', 'Deviation created', 'Sarah Mitchell'],
  ['14:33', 'Document uploaded', 'Sarah Mitchell'],
  ['14:33', 'AI extraction completed', 'AIVOA AI'],
  ['14:34', 'RAG evidence retrieved', 'Knowledge Agent'],
  ['14:34', 'AI impact assessment generated', 'Risk Agent'],
  ['14:36', 'QA reviewer modified severity', 'Sarah Mitchell'],
  ['14:37', 'Deviation submitted', 'Sarah Mitchell'],
]
