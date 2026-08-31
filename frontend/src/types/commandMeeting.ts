export type MeetingStatus = 'sap_dien_ra' | 'dang_dien_ra' | 'da_ket_thuc' | 'da_huy'
export type AttendanceStatus = 'co_mat' | 'vang_mat' | 'chua_diem_danh'

export const MEETING_STATUS_LABELS: Record<MeetingStatus, string> = {
  sap_dien_ra: 'Sắp diễn ra',
  dang_dien_ra: 'Đang diễn ra',
  da_ket_thuc: 'Đã kết thúc',
  da_huy: 'Đã huỷ',
}

export const ATTENDANCE_LABELS: Record<AttendanceStatus, string> = {
  co_mat: 'Có mặt',
  vang_mat: 'Vắng mặt',
  chua_diem_danh: 'Chưa điểm danh',
}

export interface Attendee {
  id: number
  meeting_id: number
  user_id: number
  full_name: string
  unit_id: number | null
  unit_name: string | null
  attendance: AttendanceStatus
  absence_reason: string | null
  contribution_note: string | null
}

export interface CommandMeeting {
  id: number
  title: string
  start_time: string
  end_time: string | null
  location: string | null
  meeting_link: string | null
  agenda: string | null
  minutes: string | null
  attachment_url: string | null
  attachment_name: string | null
  status: MeetingStatus
  classification: string
  created_by_id: number
  created_by_full_name: string
  created_at: string
  attendee_count: number
  present_count: number
  my_attendance: AttendanceStatus | null
}

export interface CommandMeetingDetail extends CommandMeeting {
  attendees: Attendee[]
}

export interface CommandMeetingCreate {
  title: string
  start_time: string
  end_time?: string | null
  location?: string | null
  meeting_link?: string | null
  agenda?: string | null
  attendee_user_ids: number[]
}

export interface CommandMeetingUpdate {
  title: string
  start_time: string
  end_time?: string | null
  location?: string | null
  meeting_link?: string | null
  agenda?: string | null
  status: MeetingStatus
}

export interface AttendanceUpdate {
  attendance?: AttendanceStatus
  absence_reason?: string | null
  contribution_note?: string | null
}
