import { apiClient } from './client'
import type { HomeSummary, PublicHome } from '../types/home'

export const homeApi = {
  summary: (limit = 5) => apiClient.get<HomeSummary>(`/home/summary?limit=${limit}`),
  publicSummary: (limit = 6) => apiClient.get<PublicHome>(`/home/public?limit=${limit}`),
}
