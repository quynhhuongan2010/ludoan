import type { Classification } from './common'

export type PostCategory =
  | 'huan_luyen'
  | 'dan_van'
  | 'khen_thuong'
  | 'guong_nguoi_tot'
  | 'hoat_dong_don_vi'
  | 'cong_tac_dang'
  | 'thong_tin_lien_lac'
  | 'su_kien_le_ky_niem'
export type PostStatus = 'nhap' | 'cho_duyet' | 'da_duyet' | 'tra_lai'

export const POST_CATEGORY_LABELS: Record<PostCategory, string> = {
  huan_luyen: 'Huấn luyện',
  dan_van: 'Dân vận – Đối ngoại biên phòng',
  khen_thuong: 'Thi đua – Khen thưởng',
  guong_nguoi_tot: 'Gương người tốt việc tốt',
  hoat_dong_don_vi: 'Hoạt động đơn vị',
  cong_tac_dang: 'Công tác Đảng – công tác chính trị',
  thong_tin_lien_lac: 'Thông tin liên lạc – chuyên môn',
  su_kien_le_ky_niem: 'Sự kiện – Lễ, kỷ niệm',
}

export const POST_STATUS_LABELS: Record<PostStatus, string> = {
  nhap: 'Bản nháp',
  cho_duyet: 'Chờ duyệt',
  da_duyet: 'Đã duyệt',
  tra_lai: 'Trả lại',
}

export interface Post {
  id: number
  title: string
  summary: string | null
  slug: string | null
  category: PostCategory
  content: string
  tags: string[]
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
  summary?: string | null
  /** Để trống → backend tự sinh từ tiêu đề (bỏ dấu tiếng Việt), trùng thì thêm hậu tố. */
  slug?: string | null
  category: PostCategory
  content: string
  tags: string[]
  cover_image_url?: string | null
  classification: Classification
  is_featured: boolean
}

export interface PostReview {
  status: 'da_duyet' | 'tra_lai'
  review_note?: string | null
}
