export type EducationCategory =
  | 'hoc_tap_chinh_tri_quan_su'
  | 'tuyen_truyen'
  | 'phap_luat_bien_gioi'
  | 'lich_su_truyen_thong'

export const EDUCATION_CATEGORY_LABELS: Record<EducationCategory, string> = {
  hoc_tap_chinh_tri_quan_su: 'Học tập chính trị – quân sự',
  tuyen_truyen: 'Tuyên truyền – phổ biến chủ trương',
  phap_luat_bien_gioi: 'Pháp luật biên giới',
  lich_su_truyen_thong: 'Lịch sử – truyền thống',
}

export interface EducationMaterial {
  id: number
  title: string
  category: EducationCategory
  period_label: string | null
  content: string
  attachment_url: string | null
  author_id: number
  author_full_name: string
  created_at: string
}

export interface EducationMaterialCreate {
  title: string
  category: EducationCategory
  period_label?: string | null
  content: string
  attachment_url?: string | null
}
