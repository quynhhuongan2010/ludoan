import { apiClient } from './client'
import type {
  DutyShiftHandover,
  DutyShiftHandoverAcknowledge,
  DutyShiftHandoverCommanderReview,
  DutyShiftHandoverCreate,
  DutyShiftHandoverListResponse,
} from '../types/dutyShiftHandover'

export interface DutyShiftHandoverQueryParams {
  skip?: number
  limit?: number
  date_from?: string
  date_to?: string
  unit_id?: number
  status?: string
}

export const dutyShiftHandoversApi = {
  list: (params?: DutyShiftHandoverQueryParams) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.date_from) q.set('date_from', params.date_from)
    if (params?.date_to) q.set('date_to', params.date_to)
    if (params?.unit_id !== undefined) q.set('unit_id', String(params.unit_id))
    if (params?.status) q.set('status', params.status)

    const qs = q.toString()
    return apiClient.get<DutyShiftHandoverListResponse>(
      `/duty-shift-handovers${qs ? `?${qs}` : ''}`
    )
  },

  getBySchedule: (scheduleId: number) => {
    return apiClient.get<DutyShiftHandover | null>(
      `/duty-shift-handovers/by-schedule/${scheduleId}`
    )
  },

  create: (data: DutyShiftHandoverCreate) => {
    return apiClient.post<DutyShiftHandover>('/duty-shift-handovers', data)
  },

  acknowledge: (handoverId: number, data: DutyShiftHandoverAcknowledge) => {
    return apiClient.post<DutyShiftHandover>(
      `/duty-shift-handovers/${handoverId}/acknowledge`,
      data
    )
  },

  review: (handoverId: number, data: DutyShiftHandoverCommanderReview) => {
    return apiClient.post<DutyShiftHandover>(
      `/duty-shift-handovers/${handoverId}/review`,
      data
    )
  },
}
