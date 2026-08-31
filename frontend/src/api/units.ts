import { apiClient } from './client'
import type { Unit, UnitCreate, UnitKind } from '../types/unit'

export const unitsApi = {
  list: (params?: { kind?: UnitKind; active?: boolean; skip?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.kind) q.set('kind', params.kind)
    if (params?.active !== undefined) q.set('active', String(params.active))
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    const qs = q.toString()
    return apiClient.get<Unit[]>(`/units/${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<Unit>(`/units/${id}`),
  create: (unit: UnitCreate) => apiClient.post<Unit>('/units/', unit),
  update: (id: number, unit: UnitCreate) => apiClient.put<Unit>(`/units/${id}`, unit),
  remove: (id: number) => apiClient.delete<void>(`/units/${id}`),
}
