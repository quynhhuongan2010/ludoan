export interface DutySchedule {
  id: number
  duty_date: string
  shift: string
  duty_officer: string
  role_title: string
  note: string | null
  author_id: number
  author_full_name: string
  created_at: string
}

export interface DutyScheduleCreate {
  duty_date: string
  shift: string
  duty_officer: string
  role_title: string
  note?: string | null
}
