export type AssignmentStatus = 'chua_giao' | 'dang_thuc_hien' | 'hoan_thanh' | 'qua_han'
export type TargetStatus = 'chua_nop' | 'cho_duyet' | 'da_duyet' | 'tra_lai'
export type ReviewResult = 'da_duyet' | 'tra_lai'

export const ASSIGNMENT_STATUS_LABELS: Record<AssignmentStatus, string> = {
  chua_giao: 'Chưa giao',
  dang_thuc_hien: 'Đang thực hiện',
  hoan_thanh: 'Hoàn thành',
  qua_han: 'Quá hạn',
}

export const TARGET_STATUS_LABELS: Record<TargetStatus, string> = {
  chua_nop: 'Chưa nộp',
  cho_duyet: 'Chờ duyệt',
  da_duyet: 'Đã duyệt',
  tra_lai: 'Trả lại',
}

export interface Submission {
  id: number
  target_id: number
  content: string
  attachment_url: string | null
  submitted_by_id: number
  submitted_by_full_name: string
  created_at: string
  review_result: ReviewResult | null
  review_note: string | null
  reviewed_by_id: number | null
  reviewed_at: string | null
}

export interface AssignmentTarget {
  id: number
  assignment_id: number
  unit_id: number
  unit_name: string
  assignee_id: number | null
  assignee_full_name: string | null
  status: TargetStatus
  submitted_at: string | null
  submission_count: number
  submissions: Submission[]
}

export interface DirectiveAssignment {
  id: number
  directive_id: number | null
  directive_title: string | null
  title: string
  description: string | null
  due_date: string | null
  status: AssignmentStatus
  created_by_id: number
  created_by_full_name: string
  created_at: string
  target_count: number
  approved_count: number
  pending_count: number
}

export interface DirectiveAssignmentDetail extends DirectiveAssignment {
  targets: AssignmentTarget[]
}

export interface TargetInput {
  unit_id: number
  assignee_id?: number | null
}

export interface DirectiveAssignmentCreate {
  directive_id?: number | null
  title: string
  description?: string | null
  due_date?: string | null
  targets: TargetInput[]
}

export interface DirectiveAssignmentUpdate {
  title: string
  description?: string | null
  due_date?: string | null
  directive_id?: number | null
}

export interface ReviewRequest {
  result: ReviewResult
  review_note?: string | null
}
