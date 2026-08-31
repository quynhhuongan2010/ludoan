import { apiClient } from './client'
import type { DutySchedule, DutyScheduleCreate } from '../types/dutySchedule'

export const dutySchedulesApi = {
  list: (params?: { skip?: number; limit?: number; dateFrom?: string; dateTo?: string }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.dateFrom) q.set('date_from', params.dateFrom)
    if (params?.dateTo) q.set('date_to', params.dateTo)
    const qs = q.toString()
    return apiClient.get<DutySchedule[]>(`/duty-schedules${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<DutySchedule>(`/duty-schedules/${id}`),
  create: (duty: DutyScheduleCreate) => apiClient.post<DutySchedule>('/duty-schedules', duty),
  update: (id: number, duty: DutyScheduleCreate) =>
    apiClient.put<DutySchedule>(`/duty-schedules/${id}`, duty),
  remove: (id: number) => apiClient.delete<void>(`/duty-schedules/${id}`),
}
