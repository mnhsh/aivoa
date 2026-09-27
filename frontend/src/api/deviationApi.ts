import { deviations } from '../data'

export const deviationApi = {
  list: async () => Promise.resolve(deviations),
  get: async (id: string) => Promise.resolve(deviations.find((item) => item.id === id) ?? deviations[0]),
  create: async () => Promise.resolve({ id: 'DEV-2026-0043' }),
}
