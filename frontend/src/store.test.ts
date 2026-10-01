import { beforeEach, describe, expect, it } from 'vitest'

import { applyExtractedFields, resetForm, store } from './store'

describe('deviation form updates', () => {
  beforeEach(() => {
    store.dispatch(resetForm())
  })

  it('applies process fields returned by backend chat', () => {
    store.dispatch(applyExtractedFields({
      parameter: 'Reactor Temperature',
      approvedRange: '78 - 82',
      actualValue: '86.5',
      duration: '18',
      initialSeverity: 'High',
      aiSeverity: 'High',
      aiReasoning: 'The excursion exceeds the mandatory High threshold.',
    }))

    const state = store.getState().deviation
    expect(state.form.actualValue).toBe('86.5')
    expect(state.form.duration).toBe('18')
    expect(state.form.initialSeverity).toBe('High')
    expect(state.form.aiReasoning).toContain('mandatory High')
    expect(state.highlightedFields).toContain('actualValue')
  })
})
