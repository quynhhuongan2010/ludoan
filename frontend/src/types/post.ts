import type { Classification } from './common'

export type PostCategory = 'huan_luyen' | 'dan_van' | 'khen_thuong' | 'guong_nguoi_tot'
export type PostStatus = 'cho_duyet' | 'da_duyet' | 'tra_lai'

export const POST_CATEGORY_LABELS: Record<PostCategory, string> = {
  huan_luyen: 'Huấn luyện',
  dan_van: 'Dân vận – Đối ngoại biên phòng',
  khen_thuong: 'Thi đua – Khen thưởng',
  guong_nguoi_tot: 'Gương người tốt việc tốt',
}

export const POST_STATUS_LABELS: Record<PostStatus, string> = {
  cho_duyet: 'Chờ duyệt',
  da_duyet: 'Đã duyệt',
  tra_lai: 'Trả lại',
}

export interface Post {
  id: number
  title: string
  category: PostCategory
  content: string
  cover_image_url: string | null
  classification: Classification
  is_featured: boolean
  status: PostStatus
  review_note: string | null
  reviewed_by_id: number | null
  reviewed_at: string | null
  author_id: number
  author_full_name: string
  created_at: string
}

export interface PostCreate {
  title: string
  category: PostCategory
  content: string
  cover_image_url?: string | null
  classification: Classification
  is_featured: boolean
}

export interface PostReview {
  status: 'da_duyet' | 'tra_lai'
  review_note?: string | null
}
