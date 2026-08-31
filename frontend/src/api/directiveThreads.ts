import { apiClient } from './client'
import type {
  DirectiveMessage,
  DirectiveThread,
  DirectiveThreadCreate,
  DirectiveThreadDetail,
} from '../types/directiveThread'

export const directiveThreadsApi = {
  list: (params?: { unit_id?: number; skip?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.unit_id !== undefined) q.set('unit_id', String(params.unit_id))
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    const qs = q.toString()
    return apiClient.get<DirectiveThread[]>(`/directive-threads${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<DirectiveThreadDetail>(`/directive-threads/${id}`),
  create: (payload: DirectiveThreadCreate) =>
    apiClient.post<DirectiveThread>('/directive-threads', payload),
  postMessage: (id: number, body: string, file?: File | null) => {
    const form = new FormData()
    form.set('body', body)
    if (file) form.set('file', file)
    return apiClient.postForm<DirectiveMessage>(`/directive-threads/${id}/messages`, form)
  },
  close: (id: number, isClosed: boolean) =>
    apiClient.patch<DirectiveThread>(`/directive-threads/${id}/close`, { is_closed: isClosed }),
}
