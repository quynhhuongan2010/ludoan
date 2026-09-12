export interface AuditLogItem {
  id: number
  actor_id: number | null
  actor_username: string | null
  actor_full_name: string | null
  actor_role: number | null
  action: string
  target_type: string | null
  target_id: string | null
  target_name: string | null
  ip_address: string | null
  is_success: boolean
  details: string | null
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLogItem[]
  total: number
  page: number
  page_size: number
}

export interface AuditLogQueryParams {
  page?: number
  page_size?: number
  action?: string
  actor_id?: number
  target_type?: string
  is_success?: boolean
  from_date?: string
  to_date?: string
  search?: string
}

export const AUDIT_ACTION_LABELS: Record<string, { label: string; color: string }> = {
  LOGIN_SUCCESS: { label: 'Đăng nhập thành công', color: 'green' },
  LOGIN_FAILED: { label: 'Đăng nhập thất bại', color: 'red' },
  USER_ACTIVATE: { label: 'Kích hoạt tài khoản', color: 'blue' },
  USER_DEACTIVATE: { label: 'Khóa tài khoản', color: 'orange' },
  ROLE_CHANGE: { label: 'Đổi vai trò', color: 'purple' },
  CLEARANCE_CHANGE: { label: 'Cấp/Thu hồi cơ mật', color: 'amber' },
  DIRECTIVE_CHANNEL_ACCESS: { label: 'Quyền Kênh chỉ đạo', color: 'teal' },
  COMMAND_CHANNEL_ACCESS: { label: 'Quyền Kênh chỉ huy', color: 'indigo' },
  PASSWORD_RESET: { label: 'Đặt lại mật khẩu', color: 'pink' },
  DISPATCH_DOWNLOAD: { label: 'Tải công văn mật', color: 'red' },
}
