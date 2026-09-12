export interface User {
  id: number
  username: string
  full_name: string
  /** Vai trò: số nguyên 0..5 (xem `Role` / `ROLE_LABELS`). */
  role: Role
  /** Nhãn tiếng Việt của vai trò (backend tự sinh). */
  role_label: string
  /** Cấp bậc quân hàm (vd "Thiếu tá", "Thượng uý QNCN") — null nếu chưa bổ sung. */
  rank: string | null
  /** Chức danh công tác (vd "Trợ lý Tham mưu") — null nếu chưa bổ sung. */
  position: string | null
  is_active: boolean
  clearance: boolean
  unit_id: number | null
  unit_name: string | null
  directive_channel_access: boolean
  command_channel_access: boolean
  is_system: boolean
  must_change_password: boolean
}

export interface Paginated<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export type UserPage = Paginated<User>

export interface UserCreate {
  username: string
  password: string
  full_name: string
  /** Vai trò: số nguyên 0..5 (mặc định 4 = Cá nhân). */
  role: Role
  /** Bắt buộc — chỉ cán bộ/QNCN có biên chế mới được cấp tài khoản. */
  rank: string
  /** Bắt buộc — chức danh công tác. */
  position: string
  /** Bắt buộc — đơn vị làm việc. */
  unit_id: number
  directive_channel_access?: boolean
  command_channel_access?: boolean
}

/** PATCH /users/{id}/info — chỉ huy bổ sung/sửa Cấp bậc + Chức danh. */
export interface UserInfoUpdate {
  rank: string
  position: string
}

export interface ChannelAccessUpdate {
  directive_channel_access?: boolean
  command_channel_access?: boolean
}

export interface RegisterRequest {
  username: string
  password: string
  full_name: string
}

export interface LoginRequest {
  username: string
  password: string
}

/**
 * Vai trò tài khoản (openapi v5.1.0 — nguồn sự thật: backend app/core/roles.py):
 * 0 = Quản trị hệ thống (admin) · 1 = Lữ trưởng - Chính uỷ · 2 = Lữ phó - Phó chính uỷ
 * 3 = Chỉ huy các đơn vị · 4 = Cá nhân · 5 = Người dùng
 */
export type Role = 0 | 1 | 2 | 3 | 4 | 5

/** Nhãn tiếng Việt cho từng vai trò (khớp `role_label` phía backend). */
export const ROLE_LABELS: Record<Role, string> = {
  0: 'Quản trị hệ thống',
  1: 'Lữ trưởng - Chính uỷ',
  2: 'Lữ phó - Phó chính uỷ',
  3: 'Chỉ huy đơn vị',
  4: 'Cá nhân',
  5: 'Người dùng',
}

export function roleLabel(role: Role | number | null | undefined): string {
  if (role === null || role === undefined) return ''
  return ROLE_LABELS[role as Role] ?? `Vai trò ${role}`
}

export interface Token {
  access_token: string
  token_type: string
  /** Vai trò của tài khoản vừa đăng nhập */
  role: Role
}

export interface UserImportRowError {
  row_index: number
  username?: string | null
  error: string
}

export interface UserImportResult {
  total_rows: number
  success_count: number
  error_count: number
  errors: UserImportRowError[]
  created_usernames: string[]
}

export interface PurgeResult {
  purged_count: number
  message: string
}
