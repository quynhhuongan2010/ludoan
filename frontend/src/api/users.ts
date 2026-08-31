import { apiClient } from './client'
import type {
  ChannelAccessUpdate,
  LoginRequest,
  RegisterRequest,
  Token,
  User,
  UserCreate,
} from '../types/user'

export const usersApi = {
  list: (params?: { skip?: number; limit?: number; active?: boolean }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.active !== undefined) q.set('active', String(params.active))
    const qs = q.toString()
    return apiClient.get<User[]>(`/users/${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<User>(`/users/${id}`),
  create: (user: UserCreate) => apiClient.post<User>('/users/', user),
  register: (payload: RegisterRequest) => apiClient.post<User>('/users/register', payload),
  activate: (id: number) => apiClient.post<User>(`/users/${id}/activate`, {}),
  deactivate: (id: number) => apiClient.post<User>(`/users/${id}/deactivate`, {}),
  setClearance: (id: number, clearance: boolean) =>
    apiClient.patch<User>(`/users/${id}/clearance`, { clearance }),
  setRole: (id: number, role: string) => apiClient.patch<User>(`/users/${id}/role`, { role }),
  setUnit: (id: number, unitId: number | null) =>
    apiClient.patch<User>(`/users/${id}/unit`, { unit_id: unitId }),
  setChannelAccess: (id: number, payload: ChannelAccessUpdate) =>
    apiClient.patch<User>(`/users/${id}/channel-access`, payload),
  resetPassword: (id: number, newPassword: string) =>
    apiClient.post<void>(`/users/${id}/reset-password`, { new_password: newPassword }),
  login: (credentials: LoginRequest) => apiClient.post<Token>('/users/login', credentials),
}
