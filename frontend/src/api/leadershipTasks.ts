import { apiClient } from './client'
import type {
  CommanderRole,
  CommanderBranch,
  TaskStatus,
  TaskUrgency,
  LeadershipTask,
  LeadershipTaskCreatePayload,
  LeadershipTaskReportPayload,
  LeadershipTaskReviewPayload,
  LeadershipTaskListResponse,
} from '../types/leadershipTask'

export interface LeadershipTaskQueryParams {
  skip?: number
  limit?: number
  commander_role?: CommanderRole
  target_branch?: CommanderBranch
  assigned_unit_id?: number
  status?: TaskStatus
  urgency?: TaskUrgency
}

export const leadershipTasksApi = {
  list: (params?: LeadershipTaskQueryParams) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.commander_role) q.set('commander_role', params.commander_role)
    if (params?.target_branch) q.set('target_branch', params.target_branch)
    if (params?.assigned_unit_id !== undefined)
      q.set('assigned_unit_id', String(params.assigned_unit_id))
    if (params?.status) q.set('status', params.status)
    if (params?.urgency) q.set('urgency', params.urgency)

    const qs = q.toString()
    return apiClient.get<LeadershipTaskListResponse>(
      `/leadership-tasks${qs ? `?${qs}` : ''}`
    )
  },

  getById: (id: number) => {
    return apiClient.get<LeadershipTask>(`/leadership-tasks/${id}`)
  },

  create: (data: LeadershipTaskCreatePayload) => {
    return apiClient.post<LeadershipTask>('/leadership-tasks', data)
  },

  report: (id: number, data: LeadershipTaskReportPayload) => {
    return apiClient.post<LeadershipTask>(`/leadership-tasks/${id}/report`, data)
  },

  review: (id: number, data: LeadershipTaskReviewPayload) => {
    return apiClient.post<LeadershipTask>(`/leadership-tasks/${id}/review`, data)
  },
}
