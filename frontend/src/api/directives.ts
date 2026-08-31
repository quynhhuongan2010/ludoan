import { apiClient } from './client'
import type { Directive, DirectiveAckReport, DirectiveCreate, DirectiveStatus } from '../types/directive'

export const directivesApi = {
  list: (params?: { skip?: number; limit?: number; status?: DirectiveStatus }) => {
    const query = new URLSearchParams()
    if (params?.skip !== undefined) query.set('skip', String(params.skip))
    if (params?.limit !== undefined) query.set('limit', String(params.limit))
    if (params?.status) query.set('status_filter', params.status)
    const qs = query.toString()
    return apiClient.get<Directive[]>(`/directives${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<Directive>(`/directives/${id}`),
  create: (directive: DirectiveCreate) => apiClient.post<Directive>('/directives', directive),
  update: (id: number, directive: DirectiveCreate) =>
    apiClient.put<Directive>(`/directives/${id}`, directive),
  remove: (id: number) => apiClient.delete<void>(`/directives/${id}`),
  acknowledge: (id: number) => apiClient.post<Directive>(`/directives/${id}/acknowledge`, {}),
  acknowledgements: (id: number) =>
    apiClient.get<DirectiveAckReport>(`/directives/${id}/acknowledgements`),
}
