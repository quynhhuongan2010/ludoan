import { ApiError, apiClient, getToken } from './client'
import type {
  CommandMessage,
  CommandThread,
  CommandThreadDetail,
  DispatchFormValues,
  OfficialDispatch,
  OfficialDispatchDetail,
} from '../types/commandDispatch'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const commandThreadsApi = {
  list: () => apiClient.get<CommandThread[]>('/command-threads'),
  get: (id: number) => apiClient.get<CommandThreadDetail>(`/command-threads/${id}`),
  create: (title: string) => apiClient.post<CommandThread>('/command-threads', { title }),
  postMessage: (id: number, body: string, file?: File | null) => {
    const form = new FormData()
    form.set('body', body)
    if (file) form.set('file', file)
    return apiClient.postForm<CommandMessage>(`/command-threads/${id}/messages`, form)
  },
  close: (id: number, isClosed: boolean) =>
    apiClient.patch<CommandThread>(`/command-threads/${id}/close`, { is_closed: isClosed }),
}

function dispatchForm(values: DispatchFormValues, file?: File | null): FormData {
  const form = new FormData()
  form.set('direction', values.direction)
  form.set('dispatch_number', values.dispatch_number)
  form.set('summary', values.summary)
  if (values.issuing_org) form.set('issuing_org', values.issuing_org)
  if (values.receiving_org) form.set('receiving_org', values.receiving_org)
  if (values.issued_date) form.set('issued_date', values.issued_date)
  if (values.received_date) form.set('received_date', values.received_date)
  form.set('status', values.status)
  if (values.note) form.set('note', values.note)
  if (file) form.set('file', file)
  return form
}

export const officialDispatchesApi = {
  list: (params?: { direction?: string; status_filter?: string }) => {
    const q = new URLSearchParams()
    if (params?.direction) q.set('direction', params.direction)
    if (params?.status_filter) q.set('status_filter', params.status_filter)
    const qs = q.toString()
    return apiClient.get<OfficialDispatch[]>(`/official-dispatches${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<OfficialDispatchDetail>(`/official-dispatches/${id}`),
  create: (values: DispatchFormValues, file?: File | null) =>
    apiClient.postForm<OfficialDispatchDetail>('/official-dispatches', dispatchForm(values, file)),
  update: (id: number, values: DispatchFormValues, file?: File | null) =>
    apiClient.putForm<OfficialDispatchDetail>(
      `/official-dispatches/${id}`,
      dispatchForm(values, file),
    ),
  remove: (id: number) => apiClient.delete<void>(`/official-dispatches/${id}`),
  acknowledge: (id: number, responseNote?: string | null) =>
    apiClient.post<OfficialDispatchDetail>(`/official-dispatches/${id}/acknowledge`, {
      response_note: responseNote || null,
    }),
  /** Tai tep cong van qua fetch co kem JWT (kiem soat quyen MAT), tra Blob. */
  download: async (id: number): Promise<Blob> => {
    const token = getToken()
    const res = await fetch(`${API_BASE}/official-dispatches/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new ApiError(res.status, body?.detail ?? res.statusText)
    }
    return res.blob()
  },
}
