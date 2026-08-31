import { apiClient } from './client'
import type { Announcement, AnnouncementCreate } from '../types/announcement'

export const announcementsApi = {
  list: (params?: { skip?: number; limit?: number; priority?: string; pinnedOnly?: boolean }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.priority) q.set('priority', params.priority)
    if (params?.pinnedOnly) q.set('pinned_only', 'true')
    const qs = q.toString()
    return apiClient.get<Announcement[]>(`/announcements${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<Announcement>(`/announcements/${id}`),
  create: (ann: AnnouncementCreate) => apiClient.post<Announcement>('/announcements', ann),
  update: (id: number, ann: AnnouncementCreate) =>
    apiClient.put<Announcement>(`/announcements/${id}`, ann),
  remove: (id: number) => apiClient.delete<void>(`/announcements/${id}`),
}
