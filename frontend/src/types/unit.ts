export type UnitKind =
  | 'phong_ban'
  | 'tieu_doan'
  | 'dai_doi'
  | 'tram'
  | 'bch_lu_doan'
  | 'cap_uy'

export interface Unit {
  id: number
  name: string
  unit_kind: UnitKind
  description: string | null
  is_active: boolean
  created_at: string
  user_count: number
}

export interface UnitCreate {
  name: string
  unit_kind: UnitKind
  description?: string | null
  is_active: boolean
}

export const UNIT_KIND_LABELS: Record<UnitKind, string> = {
  phong_ban: 'Phòng / Ban',
  tieu_doan: 'Tiểu đoàn',
  dai_doi: 'Đại đội',
  tram: 'Trạm',
  bch_lu_doan: 'Ban chỉ huy Lữ đoàn',
  cap_uy: 'Cấp uỷ / Đảng bộ',
}
