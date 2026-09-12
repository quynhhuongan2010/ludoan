// ===== Danh bạ điện thoại (contacts) =====

/** Một bộ danh bạ = một lần nhập file .xlsx/.csv. */
export interface ContactBook {
  id: number
  name: string
  description: string | null
  source_file_name: string | null
  /** Thứ tự cột gốc của file — dùng để dựng bảng động. */
  column_headers: string[]
  row_count: number
  created_by_id: number
  created_by_full_name: string
  created_at: string
}

/** Một dòng danh bạ. `extra` giữ nguyên mọi cột của file gốc. */
export interface Contact {
  id: number
  book_id: number
  row_index: number
  full_name: string | null
  unit: string | null
  position: string | null
  phone: string | null
  email: string | null
  extra: Record<string, string>
}

export interface ContactPage {
  items: Contact[]
  total: number
  skip: number
  limit: number
  /** Thứ tự cột gốc — FE dựng bảng theo mảng này. */
  columns: string[]
}
