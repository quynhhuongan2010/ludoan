import { ApiError, apiClient, getToken } from './client'
import type { DocumentFormData, DocumentItem } from '../types/document'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function toForm(data: DocumentFormData, file?: File): FormData {
  const fd = new FormData()
  fd.append('title', data.title)
  fd.append('category', data.category)
  fd.append('classification', data.classification)
  if (data.description) fd.append('description', data.description)
  if (file) fd.append('file', file)
  return fd
}

export const documentsApi = {
  list: (params?: { skip?: number; limit?: number; category?: string }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.category) q.set('category', params.category)
    const qs = q.toString()
    return apiClient.get<DocumentItem[]>(`/documents${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<DocumentItem>(`/documents/${id}`),
  create: (data: DocumentFormData, file: File) =>
    apiClient.postForm<DocumentItem>('/documents', toForm(data, file)),
  update: (id: number, data: DocumentFormData, file?: File) =>
    apiClient.putForm<DocumentItem>(`/documents/${id}`, toForm(data, file)),
  remove: (id: number) => apiClient.delete<void>(`/documents/${id}`),

  /** Tai file ve qua fetch co kem JWT (ton trong bac phan loai), tra Blob. */
  download: async (id: number): Promise<Blob> => {
    const token = getToken()
    const res = await fetch(`${API_BASE_URL}/documents/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new ApiError(res.status, body?.detail ?? res.statusText)
    }
    return res.blob()
  },
}
