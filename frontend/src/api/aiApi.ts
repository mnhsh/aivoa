import { evidence, extractedFields } from '../data'

export const aiApi = {
  analyze: async () => Promise.resolve({ extractedFields, evidence, recommendation: 'High' as const }),
  assess: async () => Promise.resolve({ recommendation: 'High' as const }),
}
