import { apiClient } from './client'
import type { AuditLogListResponse, AuditLogQueryParams } from '../types/auditLog'

export const auditLogsApi = {
  getLogs: (params?: AuditLogQueryParams) => {
    const q = new URLSearchParams()
    if (params?.page !== undefined) q.set('page', String(params.page))
    if (params?.page_size !== undefined) q.set('page_size', String(params.page_size))
    if (params?.action) q.set('action', params.action)
    if (params?.actor_id !== undefined) q.set('actor_id', String(params.actor_id))
    if (params?.target_type) q.set('target_type', params.target_type)
    if (params?.is_success !== undefined) q.set('is_success', String(params.is_success))
    if (params?.from_date) q.set('from_date', params.from_date)
    if (params?.to_date) q.set('to_date', params.to_date)
    if (params?.search) q.set('search', params.search)

    const qs = q.toString()
    return apiClient.get<AuditLogListResponse>(`/audit-logs${qs ? `?${qs}` : ''}`)
  },
}
