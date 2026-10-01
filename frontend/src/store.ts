import { createSlice, configureStore, PayloadAction } from '@reduxjs/toolkit'
import type { ExtractedField, Evidence } from './types'

const initialForm = {
  site: '',
  occurrenceDate: '',
  title: '',
  source: 'Internal Deviation',
  product: '',
  batch: '',
  eventType: 'Process Parameter Excursion',
  parameter: 'Reactor Temperature',
  approvedRange: '78°C – 82°C',
  actualValue: '',
  duration: '',
  description: '',
  actions: '',
  initialImpact: 'Potential Quality Impact',
  initialSeverity: 'High',
  aiSeverity: 'High',
  aiReasoning: '',
}

const deviationSlice = createSlice({
  name: 'deviation',
  initialState: {
    form: initialForm,
    applied: false,
    submitted: false,
    isExtracting: false,
    extractionProgress: 0,
    highlightedFields: [] as string[],
    confidenceScores: {} as Record<string, number>,
  },
  reducers: {
    setExtractionProgress: (state, action: PayloadAction<{ isExtracting: boolean; progress: number }>) => {
      state.isExtracting = action.payload.isExtracting
      state.extractionProgress = action.payload.progress
    },
    applyExtractedFields: (state, action: PayloadAction<Record<string, string>>) => {
      const fields = action.payload
      const updatedKeys: string[] = []

      if (fields.site !== undefined) { state.form.site = fields.site; updatedKeys.push('site') }
      if (fields.occurrenceDate !== undefined) { state.form.occurrenceDate = fields.occurrenceDate; updatedKeys.push('occurrenceDate') }
      if (fields.title !== undefined) { state.form.title = fields.title; updatedKeys.push('title') }
      if (fields.source !== undefined) { state.form.source = fields.source; updatedKeys.push('source') }
      if (fields.product !== undefined) { state.form.product = fields.product; updatedKeys.push('product') }
      if (fields.batch !== undefined) { state.form.batch = fields.batch; updatedKeys.push('batch') }
      if (fields.description !== undefined) { state.form.description = fields.description; updatedKeys.push('description') }
      if (fields.parameter !== undefined) { state.form.parameter = fields.parameter; updatedKeys.push('parameter') }
      if (fields.approvedRange !== undefined) { state.form.approvedRange = fields.approvedRange; updatedKeys.push('approvedRange') }
      if (fields.actualValue !== undefined) { state.form.actualValue = fields.actualValue; updatedKeys.push('actualValue') }
      if (fields.duration !== undefined) { state.form.duration = fields.duration; updatedKeys.push('duration') }
      if (fields.actions !== undefined) { state.form.actions = fields.actions; updatedKeys.push('actions') }
      if (fields.initialImpact !== undefined) { state.form.initialImpact = fields.initialImpact; updatedKeys.push('initialImpact') }
      if (fields.initialSeverity !== undefined) { state.form.initialSeverity = fields.initialSeverity; updatedKeys.push('initialSeverity') }
      if (fields.aiSeverity !== undefined) { state.form.aiSeverity = fields.aiSeverity; updatedKeys.push('aiSeverity') }
      if (fields.aiReasoning !== undefined) { state.form.aiReasoning = fields.aiReasoning; updatedKeys.push('aiReasoning') }

      state.applied = true
      state.highlightedFields = updatedKeys
    },
    setConfidenceScores: (state, action: PayloadAction<Record<string, number>>) => {
      state.confidenceScores = action.payload
    },
    clearHighlights: (state) => {
      state.highlightedFields = []
    },
    setField: (state, action: PayloadAction<{ key: keyof typeof initialForm; value: string }>) => {
      state.form[action.payload.key] = action.payload.value
    },
    submit: (state) => { state.submitted = true },
    resetForm: (state) => {
      state.form = { ...initialForm }
      state.applied = false
      state.submitted = false
      state.isExtracting = false
      state.extractionProgress = 0
      state.highlightedFields = []
      state.confidenceScores = {}
    },
  },
})

const copilotSlice = createSlice({
  name: 'copilot',
  initialState: {
    mode: 'empty',
    processingStep: 0,
    extractedFields: [] as ExtractedField[],
    evidence: [] as Evidence[],
    similarCases: [] as Array<{ code: string; title: string; relevance: number; status: string }>,
    source: null as string | null,
  },
  reducers: {
    startAnalysis: (state, action: PayloadAction<string>) => { state.mode = 'processing'; state.processingStep = 0; state.source = action.payload },
    setProcessingStep: (state, action: PayloadAction<number>) => { state.processingStep = action.payload },
    completeAnalysis: (state) => { state.mode = 'results'; state.processingStep = 5 },
    setAnalysisResults: (state, action: PayloadAction<{ extractedFields?: ExtractedField[]; evidence?: Evidence[]; similarCases?: Array<{ code: string; title: string; relevance: number; status: string }> }>) => {
      if (action.payload.extractedFields) state.extractedFields = action.payload.extractedFields
      if (action.payload.evidence) state.evidence = action.payload.evidence
      if (action.payload.similarCases) state.similarCases = action.payload.similarCases
      state.mode = 'results'
      state.processingStep = 5
    },
    resetCopilot: (state) => {
      state.mode = 'empty'
      state.processingStep = 0
      state.extractedFields = []
      state.evidence = []
      state.similarCases = []
      state.source = null
    },
  },
})

export const {
  setExtractionProgress,
  applyExtractedFields,
  setConfidenceScores,
  clearHighlights,
  setField,
  submit,
  resetForm,
} = deviationSlice.actions

export const {
  startAnalysis,
  setProcessingStep,
  completeAnalysis,
  setAnalysisResults,
  resetCopilot,
} = copilotSlice.actions

export const store = configureStore({
  reducer: {
    deviation: deviationSlice.reducer,
    copilot: copilotSlice.reducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
