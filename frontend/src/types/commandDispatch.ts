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
}

export interface CommandThreadDetail extends CommandThread {
  messages: CommandMessage[]
}

// ===== So cong van mat (official dispatches) =====
export type DispatchDirection = 'di' | 'den'
export type DispatchStatus = 'moi' | 'dang_xu_ly' | 'da_xu_ly' | 'luu_tru'

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

export interface DispatchAck {
  user_id: number
  full_name: string
  role: string
  acknowledged_at: string | null
  response_note: string | null
}

export interface OfficialDispatch {
  id: number
  direction: DispatchDirection
  dispatch_number: string
  summary: string
  issuing_org: string | null
  receiving_org: string | null
  issued_date: string | null
  received_date: string | null
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

/** Truong nhap cho form so cong van (dung chung tao & sua). */
export interface DispatchFormValues {
  direction: DispatchDirection
  dispatch_number: string
  summary: string
  issuing_org: string
  receiving_org: string
  issued_date: string
  received_date: string
  status: DispatchStatus
  note: string
}
