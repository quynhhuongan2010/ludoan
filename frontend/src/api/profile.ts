import { apiClient } from './client'
import type { PasswordChange, ProfileUpdate } from '../types/profile'
import type { UserPermissions } from '../types/rbac'
import type { User } from '../types/user'

export const profileApi = {
  me: () => apiClient.get<User>('/profile/me'),
  getPermissions: () => apiClient.get<UserPermissions>('/profile/permissions'),
  update: (payload: ProfileUpdate) => apiClient.put<User>('/profile/me', payload),
  changePassword: (payload: PasswordChange) =>
    apiClient.post<void>('/profile/change-password', payload),
}
