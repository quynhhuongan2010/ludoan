import { apiClient } from './client'
import type {
  AssignmentTarget,
  DirectiveAssignment,
  DirectiveAssignmentCreate,
  DirectiveAssignmentDetail,
  DirectiveAssignmentUpdate,
  ReviewRequest,
  TargetInput,
} from '../types/directiveAssignment'

export const directiveAssignmentsApi = {
  list: (params?: { status_filter?: string; directive_id?: number; skip?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.status_filter) q.set('status_filter', params.status_filter)
    if (params?.directive_id !== undefined) q.set('directive_id', String(params.directive_id))
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    const qs = q.toString()
    return apiClient.get<DirectiveAssignment[]>(`/directive-assignments${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<DirectiveAssignmentDetail>(`/directive-assignments/${id}`),
  create: (payload: DirectiveAssignmentCreate) =>
    apiClient.post<DirectiveAssignmentDetail>('/directive-assignments', payload),
  update: (id: number, payload: DirectiveAssignmentUpdate) =>
    apiClient.put<DirectiveAssignmentDetail>(`/directive-assignments/${id}`, payload),
  remove: (id: number) => apiClient.delete<void>(`/directive-assignments/${id}`),
  addTargets: (id: number, targets: TargetInput[]) =>
    apiClient.post<DirectiveAssignmentDetail>(`/directive-assignments/${id}/targets`, targets),
  removeTarget: (id: number, targetId: number) =>
    apiClient.delete<DirectiveAssignmentDetail>(
      `/directive-assignments/${id}/targets/${targetId}`,
    ),
  submit: (id: number, targetId: number, content: string, file?: File | null) => {
    const form = new FormData()
    form.set('content', content)
    if (file) form.set('file', file)
    return apiClient.postForm<AssignmentTarget>(
      `/directive-assignments/${id}/targets/${targetId}/submit`,
      form,
    )
  },
  review: (id: number, targetId: number, payload: ReviewRequest) =>
    apiClient.post<AssignmentTarget>(
      `/directive-assignments/${id}/targets/${targetId}/review`,
      payload,
    ),
}
