import { ApiError, apiClient, getToken } from './client'
import type {
  AttendanceUpdate,
  Attendee,
  CommandMeeting,
  CommandMeetingCreate,
  CommandMeetingDetail,
  CommandMeetingUpdate,
} from '../types/commandMeeting'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const commandMeetingsApi = {
  list: (params?: { status_filter?: string; date_from?: string; date_to?: string }) => {
    const q = new URLSearchParams()
    if (params?.status_filter) q.set('status_filter', params.status_filter)
    if (params?.date_from) q.set('date_from', params.date_from)
    if (params?.date_to) q.set('date_to', params.date_to)
    const qs = q.toString()
    return apiClient.get<CommandMeeting[]>(`/command-meetings${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<CommandMeetingDetail>(`/command-meetings/${id}`),
  create: (payload: CommandMeetingCreate) =>
    apiClient.post<CommandMeetingDetail>('/command-meetings', payload),
  update: (id: number, payload: CommandMeetingUpdate) =>
    apiClient.put<CommandMeetingDetail>(`/command-meetings/${id}`, payload),
  remove: (id: number) => apiClient.delete<void>(`/command-meetings/${id}`),
  setMinutes: (id: number, minutes: string, markFinished = false) =>
    apiClient.post<CommandMeetingDetail>(`/command-meetings/${id}/minutes`, {
      minutes,
      mark_finished: markFinished,
    }),
  uploadAttachment: (id: number, file: File) => {
    const form = new FormData()
    form.set('file', file)
    return apiClient.postForm<CommandMeetingDetail>(
      `/command-meetings/${id}/attachment`,
      form,
    )
  },
  invite: (id: number, userIds: number[]) =>
    apiClient.post<CommandMeetingDetail>(`/command-meetings/${id}/attendees`, {
      user_ids: userIds,
    }),
  removeAttendee: (id: number, userId: number) =>
    apiClient.delete<void>(`/command-meetings/${id}/attendees/${userId}`),
  setAttendance: (id: number, userId: number, payload: AttendanceUpdate) =>
    apiClient.patch<Attendee>(`/command-meetings/${id}/attendees/${userId}`, payload),
  download: async (id: number): Promise<Blob> => {
    const token = getToken()
    const res = await fetch(`${API_BASE}/command-meetings/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new ApiError(res.status, body?.detail ?? res.statusText)
    }
    return res.blob()
  },
}
