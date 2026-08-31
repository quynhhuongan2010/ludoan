import type { Classification } from './common'

export type DocumentCategory =
  | 'bieu_mau'
  | 'huong_dan'
  | 'quy_che_quy_dinh'
  | 'ke_hoach'
  | 'bao_cao'
  | 'van_ban_chi_dao'

export const DOCUMENT_CATEGORY_LABELS: Record<DocumentCategory, string> = {
  bieu_mau: 'Biểu mẫu',
  huong_dan: 'Hướng dẫn',
  quy_che_quy_dinh: 'Quy chế – Quy định',
  ke_hoach: 'Kế hoạch',
  bao_cao: 'Báo cáo',
  van_ban_chi_dao: 'Văn bản chỉ đạo',
}

export interface DocumentFormData {
  title: string
  category: DocumentCategory
  description: string
  classification: Classification
}

export interface DocumentItem {
  id: number
  title: string
  description: string | null
  category: DocumentCategory
  file_url: string
  file_name: string
  file_size: number
  content_type: string
  classification: Classification
  uploaded_by_id: number
  uploaded_by_full_name: string
  created_at: string
}
