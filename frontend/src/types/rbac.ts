// Dong bo voi openapi.yaml v7.6.0 - Phan quyen da cap theo Khoi/Nganh co quan & Ma tran quyen quan su.

export type MilitaryBranch =
  | 'toan_lu_doan'
  | 'tham_muu'
  | 'chinh_tri'
  | 'hau_can_ky_thuat'
  | 'don_vi_co_so'

export const BRANCH_LABELS: Record<MilitaryBranch, string> = {
  toan_lu_doan: 'Ban Chỉ huy Lữ đoàn & Quản trị hệ thống',
  tham_muu: 'Khối Tham mưu (Tác chiến · Huấn luyện · TTLL)',
  chinh_tri: 'Khối Chính trị (CTĐ-CTCT · Tuyên huấn · Giáo dục)',
  hau_can_ky_thuat: 'Khối Hậu cần – Kỹ thuật (Trang bị VKTB · Vật tư)',
  don_vi_co_so: 'Đơn vị cơ sở (Tiểu đoàn · Đại đội · Trạm)',
}

export const BRANCH_ICONS: Record<MilitaryBranch, string> = {
  toan_lu_doan: 'star',
  tham_muu: 'shield',
  chinh_tri: 'book-open',
  hau_can_ky_thuat: 'layers',
  don_vi_co_so: 'users',
}

export const BRANCH_BADGE_COLORS: Record<
  MilitaryBranch,
  { bg: string; text: string; border: string }
> = {
  toan_lu_doan: {
    bg: 'bg-red-50 dark:bg-red-950/40',
    text: 'text-red-700 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
  },
  tham_muu: {
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    text: 'text-blue-700 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
  },
  chinh_tri: {
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    text: 'text-amber-700 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
  },
  hau_can_ky_thuat: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    text: 'text-emerald-700 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  don_vi_co_so: {
    bg: 'bg-slate-50 dark:bg-slate-800',
    text: 'text-slate-700 dark:text-slate-300',
    border: 'border-slate-200 dark:border-slate-700',
  },
}

export interface UserPermissions {
  user_id: number
  username: string
  full_name: string
  role: number
  role_label: string
  branch: MilitaryBranch
  branch_label: string
  unit_id: number | null
  unit_name: string | null
  permissions: Record<string, boolean>
}

export const PERMISSION_LABELS: Record<string, { label: string; group: string }> = {
  is_admin: { label: 'Quản trị viên toàn hệ thống', group: 'Hệ thống' },
  is_commander: { label: 'Cương vị Chỉ huy đơn vị', group: 'Chỉ huy' },
  has_classified_clearance: { label: 'Quyền truy cập tài liệu MẬT', group: 'Bảo mật' },
  access_command_channel: { label: 'Truy cập Kênh chỉ huy tác chiến', group: 'Kênh hạn chế' },
  access_directive_channel: { label: 'Truy cập Kênh chỉ thị nhiệm vụ', group: 'Kênh hạn chế' },
  view_audit_logs: { label: 'Xem Nhật ký an ninh & Giám sát hệ thống', group: 'Bảo mật' },
  manage_tham_muu: { label: 'Quản lý nghiệp vụ Khối Tham mưu', group: 'Khối / Ngành' },
  manage_chinh_tri: { label: 'Quản lý nghiệp vụ Khối Chính trị', group: 'Khối / Ngành' },
  manage_hau_can_ky_thuat: { label: 'Quản lý nghiệp vụ Khối Hậu cần - Kỹ thuật', group: 'Khối / Ngành' },
  review_duty_schedule: { label: 'Thẩm định & Phê duyệt Lịch trực', group: 'Nhiệm vụ tác chiến' },
  create_duty_handover: { label: 'Lập biên bản bàn giao ca trực', group: 'Nhiệm vụ tác chiến' },
  review_duty_handover: { label: 'Ghi bút phê chỉ đạo ca trực', group: 'Chỉ huy' },
  publish_news: { label: 'Đăng tin tức & Hoạt động nội bộ', group: 'Tuyên truyền' },
  manage_political_education: { label: 'Biên tập Tư liệu Giáo dục chính trị', group: 'Tuyên truyền' },
  manage_documents: { label: 'Quản lý Văn bản - Biểu mẫu cơ quan', group: 'Văn thư' },
  manage_users: { label: 'Quản lý danh sách tài khoản quân nhân', group: 'Hệ thống' },
}
