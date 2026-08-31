export type AnnouncementPriority = 'thap' | 'binh_thuong' | 'cao' | 'khan'

export const ANNOUNCEMENT_PRIORITY_LABELS: Record<AnnouncementPriority, string> = {
  thap: 'Thấp',
  binh_thuong: 'Bình thường',
  cao: 'Cao',
  khan: 'Khẩn',
}

export interface Announcement {
  id: number
  title: string
  content: string
  priority: AnnouncementPriority
  is_pinned: boolean
  is_public: boolean
  starts_at: string | null
  ends_at: string | null
  author_id: number
  author_full_name: string
  created_at: string
}

export interface AnnouncementCreate {
  title: string
  content: string
  priority: AnnouncementPriority
  is_pinned: boolean
  is_public: boolean
  starts_at?: string | null
  ends_at?: string | null
}
