import type { Classification } from './common'

export type DirectiveStatus = 'nhap' | 'da_ban_hanh'

export const DIRECTIVE_STATUS_LABELS: Record<DirectiveStatus, string> = {
  nhap: 'Bản nháp',
  da_ban_hanh: 'Đã ban hành',
}

export interface Directive {
  id: number
  title: string
  content: string
  status: DirectiveStatus
  classification: Classification
  author_id: number
  author_full_name: string
  created_at: string
  recipient_count: number
  acknowledged_count: number
  acknowledged_by_me: boolean
}

export interface DirectiveCreate {
  title: string
  content: string
  status: DirectiveStatus
  classification: Classification
}

export interface DirectiveAckUser {
  user_id: number
  full_name: string
  role: string
  acknowledged_at: string | null
}

export interface DirectiveAckReport {
  directive_id: number
  recipient_count: number
  acknowledged_count: number
  acknowledged: DirectiveAckUser[]
  pending: DirectiveAckUser[]
}
