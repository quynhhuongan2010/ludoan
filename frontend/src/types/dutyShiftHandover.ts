// Dong bo openapi v8.0.0 - Bien ban ban giao ca truc & So nhat ky kip truc dien tu.
// v8.0.0 khong doi schema; chi siet hanh vi backend: acknowledge co guard trang thai +
// chi receiver duoc chi dinh moi ky (403/409), chan role 5 lap bien ban & tu ban giao (400/403).

export type DutyShiftHandoverStatus = 'cho_nhan' | 'da_nhan' | 'co_kien_nghi'

export const HANDOVER_STATUS_LABELS: Record<DutyShiftHandoverStatus, string> = {
  cho_nhan: 'Chờ nhận ca',
  da_nhan: 'Đã nhận ca',
  co_kien_nghi: 'Có kiến nghị',
}

export const HANDOVER_STATUS_COLORS: Record<
  DutyShiftHandoverStatus,
  { bg: string; text: string; border: string }
> = {
  cho_nhan: {
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    text: 'text-amber-700 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
  },
  da_nhan: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    text: 'text-emerald-700 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  co_kien_nghi: {
    bg: 'bg-rose-50 dark:bg-rose-950/40',
    text: 'text-rose-700 dark:text-rose-300',
    border: 'border-rose-200 dark:border-rose-800',
  },
}

export interface DutyShiftHandover {
  id: number
  schedule_id: number
  duty_date: string | null
  duty_type: string | null
  shift: string | null
  unit_name: string | null
  giver_id: number
  giver_name: string
  receiver_id: number | null
  receiver_name: string | null
  handover_time: string
  personnel_report: string
  equipment_status: string
  incident_log: string | null
  pending_tasks: string | null
  commander_note: string | null
  status: DutyShiftHandoverStatus
  receiver_note: string | null
  acknowledged_at: string | null
  created_at: string
  updated_at: string
}

export interface DutyShiftHandoverCreate {
  schedule_id: number
  receiver_id?: number | null
  receiver_name?: string | null
  giver_name?: string | null
  personnel_report: string
  equipment_status: string
  incident_log?: string | null
  pending_tasks?: string | null
}

export interface DutyShiftHandoverAcknowledge {
  receiver_note?: string | null
  status?: 'da_nhan' | 'co_kien_nghi'
}

export interface DutyShiftHandoverCommanderReview {
  commander_note: string
}

export interface DutyShiftHandoverListResponse {
  items: DutyShiftHandover[]
  total: number
}
