import { apiClient } from './client'
import type {
  ChannelAccessUpdate,
  LoginRequest,
  RegisterRequest,
  Role,
  Token,
  User,
  UserCreate,
  UserInfoUpdate,
  UserPage,
} from '../types/user'

export const usersApi = {
  list: (params?: { skip?: number; limit?: number; active?: boolean }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.active !== undefined) q.set('active', String(params.active))
    const qs = q.toString()
    return apiClient.get<UserPage>(`/users/${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<User>(`/users/${id}`),
  create: (user: UserCreate) => apiClient.post<User>('/users/', user),
  /** Xoá hẳn tài khoản (role 0, 1, 2). 204 khi thành công. */
  remove: (id: number) => apiClient.delete<void>(`/users/${id}`),
  register: (payload: RegisterRequest) => apiClient.post<User>('/users/register', payload),
  activate: (id: number) => apiClient.post<User>(`/users/${id}/activate`, {}),
  deactivate: (id: number) => apiClient.post<User>(`/users/${id}/deactivate`, {}),
  setClearance: (id: number, clearance: boolean) =>
    apiClient.patch<User>(`/users/${id}/clearance`, { clearance }),
  setRole: (id: number, role: Role) => apiClient.patch<User>(`/users/${id}/role`, { role }),
  setUnit: (id: number, unitId: number | null) =>
    apiClient.patch<User>(`/users/${id}/unit`, { unit_id: unitId }),
  setInfo: (id: number, payload: UserInfoUpdate) =>
    apiClient.patch<User>(`/users/${id}/info`, payload),
  setChannelAccess: (id: number, payload: ChannelAccessUpdate) =>
    apiClient.patch<User>(`/users/${id}/channel-access`, payload),
  resetPassword: (id: number, newPassword: string) =>
    apiClient.post<void>(`/users/${id}/reset-password`, { new_password: newPassword }),
  login: (credentials: LoginRequest) =>
    apiClient.post<Token>('/users/login', credentials, { successMessage: 'Đăng nhập thành công' }),

  /** Nhập người dùng hàng loạt từ file Excel (.xlsx, .xls) hoặc Word (.docx) */
  importFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.postForm<import('../types/user').UserImportResult>(
      '/users/import',
      formData,
      { successMessage: 'Đã hoàn tất xử lý tệp danh sách' }
    )
  },

  /** Tải tệp mẫu Excel hoặc Word chuẩn quân sự */
  downloadTemplate: async (format: 'excel' | 'word') => {
    const token = localStorage.getItem('quynh_web.access_token')
    const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
    const res = await fetch(`${apiBase}/users/import/template?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Không thể tải tệp mẫu')
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = format === 'excel' ? 'mau_nhap_quan_nhan_ludoan21.xlsx' : 'mau_nhap_quan_nhan_ludoan21.docx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },

  /** Xoá sạch toàn bộ tài khoản thử nghiệm (Purge), chỉ giữ lại tài khoản admin */
  purgeTestUsers: () =>
    apiClient.delete<import('../types/user').PurgeResult>('/users/purge-test-users', {
      successMessage: 'Đã dọn dẹp sạch toàn bộ tài khoản thử nghiệm',
    }),
}

