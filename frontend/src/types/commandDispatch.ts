import type { Role } from './user'

// ===== Luong trao doi Ban Chi huy & Cap uy (command threads) =====
export interface CommandMessage {
  id: number
  thread_id: number
  sender_id: number
  sender_full_name: string
  body: string
  attachment_url: string | null
  created_at: string
}

export interface CommandThread {
  id: number
  title: string
  classification: string
  created_by_id: number
  created_by_full_name: string
  created_at: string
  last_message_at: string | null
  is_closed: boolean
  message_count: number
  unread_count: number
  member_count: number
}

export interface ThreadMember {
  user_id: number
  full_name: string
  unit_name: string | null
  added_at: string
}

export interface CommandThreadDetail extends CommandThread {
  messages: CommandMessage[]
  members: ThreadMember[]
}

// ===== Kho van ban cua luong (chung/rieng) =====
export type DocVisibility = 'chung' | 'rieng'

export const DOC_VISIBILITY_LABELS: Record<DocVisibility, string> = {
  chung: 'Chung (cả luồng xem được)',
  rieng: 'Riêng (chỉ người tải lên + BCH)',
}

export interface CommandThreadDocument {
  id: number
  thread_id: number
  title: string
  visibility: DocVisibility
  file_url: string
  file_name: string
  file_size: number
  content_type: string | null
  uploaded_by_id: number
  uploaded_by_full_name: string
  created_at: string
}

// ===== Bien ban thao luan (tu ghep tu lich su tin nhan) =====
export interface CommandThreadMinutes {
  id: number
  thread_id: number
  content: string
  message_count: number
  generated_by_id: number
  generated_by_full_name: string
  generated_at: string
}

// ===== So dang ky van ban di - den / So cong van mat (official dispatches) =====
export type DispatchDirection = 'di' | 'den'
export type DispatchStatus = 'moi' | 'dang_xu_ly' | 'da_xu_ly' | 'luu_tru'

export type DocType =
  | 'cong_van'
  | 'dien_mat'
  | 'chi_thi'
  | 'quyet_dinh'
  | 'menh_lenh'
  | 'thong_bao'
  | 'thong_tri'
  | 'ke_hoach'
  | 'bao_cao'
  | 'to_trinh'
  | 'bien_ban'
  | 'huong_dan'
  | 'giay_moi'
  | 'khac'

export type SecurityLevel = 'thuong' | 'mat' | 'toi_mat' | 'tuyet_mat'
export type Urgency = 'thuong' | 'khan' | 'thuong_khan' | 'hoa_toc'

export const DISPATCH_DIRECTION_LABELS: Record<DispatchDirection, string> = {
  di: 'Văn bản đi',
  den: 'Văn bản đến',
}

export const DISPATCH_STATUS_LABELS: Record<DispatchStatus, string> = {
  moi: 'Mới',
  dang_xu_ly: 'Đang xử lý',
  da_xu_ly: 'Đã xử lý',
  luu_tru: 'Lưu trữ',
}

export const DOC_TYPE_LABELS: Record<DocType, string> = {
  cong_van: 'Công văn',
  dien_mat: 'Điện mật',
  chi_thi: 'Chỉ thị',
  quyet_dinh: 'Quyết định',
  menh_lenh: 'Mệnh lệnh',
  thong_bao: 'Thông báo',
  thong_tri: 'Thông tri',
  ke_hoach: 'Kế hoạch',
  bao_cao: 'Báo cáo',
  to_trinh: 'Tờ trình',
  bien_ban: 'Biên bản',
  huong_dan: 'Hướng dẫn',
  giay_moi: 'Giấy mời',
  khac: 'Khác',
}

export const SECURITY_LEVEL_LABELS: Record<SecurityLevel, string> = {
  thuong: 'Thường',
  mat: 'Mật',
  toi_mat: 'Tối mật',
  tuyet_mat: 'Tuyệt mật',
}

export const URGENCY_LABELS: Record<Urgency, string> = {
  thuong: 'Thường',
  khan: 'Khẩn',
  thuong_khan: 'Thượng khẩn',
  hoa_toc: 'Hoả tốc',
}

export interface DispatchAck {
  user_id: number
  full_name: string
  role: Role
  acknowledged_at: string | null
  response_note: string | null
}

export interface OfficialDispatch {
  id: number
  direction: DispatchDirection
  doc_type: DocType
  dispatch_number: string
  summary: string
  issuing_org: string | null
  receiving_org: string | null
  signer: string | null
  issued_date: string | null
  received_date: string | null
  deadline: string | null
  page_count: number | null
  security_level: SecurityLevel
  urgency: Urgency
  archive_ref: string | null
  status: DispatchStatus
  classification: string
  note: string | null
  attachment_url: string | null
  attachment_name: string | null
  created_by_id: number
  created_by_full_name: string
  created_at: string
  recipient_count: number
  acknowledged_count: number
  acknowledged_by_me: boolean
}

export interface OfficialDispatchDetail extends OfficialDispatch {
  acknowledged: DispatchAck[]
  pending: DispatchAck[]
}

/** Truong nhap cho form so dang ky van ban (dung chung tao & sua). */
export interface DispatchFormValues {
  direction: DispatchDirection
  doc_type: DocType
  dispatch_number: string
  summary: string
  issuing_org: string
  receiving_org: string
  signer: string
  issued_date: string
  received_date: string
  deadline: string
  page_count: string
  security_level: SecurityLevel
  urgency: Urgency
  archive_ref: string
  status: DispatchStatus
  note: string
}
