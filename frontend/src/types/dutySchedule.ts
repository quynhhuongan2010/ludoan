// Dong bo voi openapi.yaml v4.0.0 - module Lich truc - Kip truc.
// Bang truc tuan theo don vi (DutyWeekPlan) + luong phe duyet + 2 bang tong hop.

export type DutyType =
  | 'truc_chi_huy'
  | 'truc_ban_tac_chien'
  | 'truc_ban_noi_vu'
  | 'truc_chuyen_mon'
  | 'truc_ca_kip'
  | 'truc_bao_ve'
  | 'khac'

export const DUTY_TYPE_LABELS: Record<DutyType, string> = {
  truc_chi_huy: 'Trực chỉ huy',
  truc_ban_tac_chien: 'Trực ban tác chiến',
  truc_ban_noi_vu: 'Trực ban nội vụ',
  truc_chuyen_mon: 'Trực chuyên môn',
  truc_ca_kip: 'Trực ca kíp',
  truc_bao_ve: 'Trực bảo vệ / vệ binh',
  khac: 'Khác',
}

export type DutyPlanStatus = 'nhap' | 'cho_duyet' | 'da_duyet' | 'tra_lai'

export const DUTY_PLAN_STATUS_LABELS: Record<DutyPlanStatus, string> = {
  nhap: 'Nháp',
  cho_duyet: 'Chờ duyệt',
  da_duyet: 'Đã duyệt',
  tra_lai: 'Trả lại',
}

// ----- Dong ca truc (con cua bang truc tuan) -----

export interface DutySchedule {
  id: number
  week_plan_id: number | null
  duty_date: string
  unit_id: number | null
  unit_name: string | null
  duty_type: string
  duty_type_label: string
  shift: string
  duty_officer: string
  role_title: string
  contact_phone: string | null
  personnel_present: number | null
  personnel_total: number | null
  note: string | null
  author_id: number
  author_full_name: string
  created_at: string
}

/** Body them/sua 1 dong ca truc. unit_id + tuan suy tu bang cha. */
export interface DutyScheduleCreate {
  duty_date: string
  duty_type: DutyType
  shift: string
  duty_officer: string
  role_title: string
  contact_phone?: string | null
  personnel_present?: number | null
  personnel_total?: number | null
  note?: string | null
}

// ----- Bang truc tuan cua don vi -----

export interface DutyWeekPlan {
  id: number
  unit_id: number
  unit_name: string
  week_start: string
  week_end: string
  week_label: string
  status: DutyPlanStatus
  status_label: string
  note: string | null
  entry_count: number
  attachment_count: number
  personnel_present: number
  personnel_total: number
  submitted_by_id: number | null
  submitted_by_name: string | null
  submitted_at: string | null
  reviewed_by_id: number | null
  reviewed_by_name: string | null
  reviewed_at: string | null
  review_note: string | null
  author_id: number
  author_full_name: string
  created_at: string
}

// ----- Tep dinh kem cua bang truc tuan (nhieu tep / bang) -----

export interface DutyPlanAttachment {
  id: number
  week_plan_id: number
  file_url: string
  original_name: string
  file_size: number
  content_type: string | null
  label: string | null
  uploaded_by_id: number
  uploaded_by_name: string
  created_at: string
}

export interface DutyWeekPlanDetail extends DutyWeekPlan {
  entries: DutySchedule[]
  attachments: DutyPlanAttachment[]
}

export interface DutyWeekPlanCreate {
  unit_id: number
  week_start: string
  note?: string | null
}

export interface DutyWeekPlanUpdate {
  note?: string | null
}

export interface DutyWeekPlanReview {
  status: 'da_duyet' | 'tra_lai'
  review_note?: string | null
}

// ----- Tinh nang 1: bang kip truc theo ngay (gom theo don vi) -----

export interface DutyUnitGroup {
  unit_id: number | null
  unit_name: string
  plan_id: number | null
  plan_status: DutyPlanStatus | null
  plan_status_label: string | null
  entries: DutySchedule[]
  entry_count: number
  personnel_present: number
  personnel_total: number
}

export interface DutyDayBoard {
  date: string
  weekday_label: string
  groups: DutyUnitGroup[]
  total_entries: number
  personnel_present: number
  personnel_total: number
}

// ----- Tinh nang 2: bang truc tuan (7 ngay) -----

export interface DutyWeekPlanBrief {
  plan_id: number
  unit_id: number
  unit_name: string
  status: DutyPlanStatus
  status_label: string
  entry_count: number
  submitted_at: string | null
  reviewed_at: string | null
}

export interface DutyWeekDay {
  date: string
  weekday_label: string
  is_today: boolean
  entries: DutySchedule[]
  entry_count: number
  personnel_present: number
  personnel_total: number
}

export interface DutyWeekBoard {
  week_start: string
  week_end: string
  week_label: string
  days: DutyWeekDay[]
  unit_plans: DutyWeekPlanBrief[]
  total_entries: number
}
