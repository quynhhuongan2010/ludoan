import { apiClient } from './client'
import type {
  DutyDayBoard,
  DutyPlanAttachment,
  DutySchedule,
  DutyScheduleCreate,
  DutyWeekBoard,
  DutyWeekPlan,
  DutyWeekPlanCreate,
  DutyWeekPlanDetail,
  DutyWeekPlanReview,
  DutyWeekPlanUpdate,
} from '../types/dutySchedule'

/** Dong ca truc: chi con doc danh sach + sua/xoa tung dong + 2 bang tong hop. */
export const dutySchedulesApi = {
  list: (params?: {
    skip?: number
    limit?: number
    dateFrom?: string
    dateTo?: string
    unitId?: number
    dutyType?: string
  }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.dateFrom) q.set('date_from', params.dateFrom)
    if (params?.dateTo) q.set('date_to', params.dateTo)
    if (params?.unitId !== undefined) q.set('unit_id', String(params.unitId))
    if (params?.dutyType) q.set('duty_type', params.dutyType)
    const qs = q.toString()
    return apiClient.get<DutySchedule[]>(`/duty-schedules${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<DutySchedule>(`/duty-schedules/${id}`),
  updateEntry: (id: number, entry: DutyScheduleCreate) =>
    apiClient.put<DutySchedule>(`/duty-schedules/${id}`, entry),
  removeEntry: (id: number) => apiClient.delete<void>(`/duty-schedules/${id}`),

  /** Tinh nang 1: kip truc toan Lu doan theo ngay, gom theo don vi. */
  dayBoard: (day: string, unitId?: number) => {
    const q = new URLSearchParams({ day })
    if (unitId !== undefined) q.set('unit_id', String(unitId))
    return apiClient.get<DutyDayBoard>(`/duty-schedules/board/day?${q.toString()}`)
  },
  /** Tinh nang 2: truc tuan - khung nhin 7 ngay + ma tran phe duyet theo don vi. */
  weekBoard: (weekOf: string, unitId?: number) => {
    const q = new URLSearchParams({ week_of: weekOf })
    if (unitId !== undefined) q.set('unit_id', String(unitId))
    return apiClient.get<DutyWeekBoard>(`/duty-schedules/board/week?${q.toString()}`)
  },
}

/** Bang truc tuan cua don vi: lap - trinh - chi huy phe duyet. */
export const dutyWeekPlansApi = {
  list: (params?: { unitId?: number; weekOf?: string; status?: string }) => {
    const q = new URLSearchParams()
    if (params?.unitId !== undefined) q.set('unit_id', String(params.unitId))
    if (params?.weekOf) q.set('week_of', params.weekOf)
    if (params?.status) q.set('status_filter', params.status)
    const qs = q.toString()
    return apiClient.get<DutyWeekPlan[]>(`/duty-week-plans${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<DutyWeekPlanDetail>(`/duty-week-plans/${id}`),
  create: (plan: DutyWeekPlanCreate) =>
    apiClient.post<DutyWeekPlan>('/duty-week-plans', plan),
  update: (id: number, data: DutyWeekPlanUpdate) =>
    apiClient.put<DutyWeekPlan>(`/duty-week-plans/${id}`, data),
  remove: (id: number) => apiClient.delete<void>(`/duty-week-plans/${id}`),
  addEntry: (id: number, entry: DutyScheduleCreate) =>
    apiClient.post<DutySchedule>(`/duty-week-plans/${id}/entries`, entry),
  submit: (id: number) => apiClient.post<DutyWeekPlan>(`/duty-week-plans/${id}/submit`, {}),
  review: (id: number, review: DutyWeekPlanReview) =>
    apiClient.post<DutyWeekPlan>(`/duty-week-plans/${id}/review`, review),
  reopen: (id: number) => apiClient.post<DutyWeekPlan>(`/duty-week-plans/${id}/reopen`, {}),

  // --- Tep dinh kem cua bang truc tuan (nhieu tep moi loai / bang) ---
  listAttachments: (planId: number) =>
    apiClient.get<DutyPlanAttachment[]>(`/duty-week-plans/${planId}/attachments`),
  uploadAttachment: (planId: number, file: File, label?: string) => {
    const fd = new FormData()
    fd.append('file', file)
    if (label?.trim()) fd.append('label', label.trim())
    return apiClient.postForm<DutyPlanAttachment>(`/duty-week-plans/${planId}/attachments`, fd, {
      successMessage: 'Đã đính kèm tệp lịch trực',
    })
  },
  deleteAttachment: (planId: number, attachmentId: number) =>
    apiClient.delete<void>(`/duty-week-plans/${planId}/attachments/${attachmentId}`),
}
