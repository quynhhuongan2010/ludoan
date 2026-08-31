export type Classification = 'cong_khai' | 'noi_bo' | 'mat'

export const CLASSIFICATION_LABELS: Record<Classification, string> = {
  cong_khai: 'Công khai',
  noi_bo: 'Nội bộ',
  mat: 'MẬT',
}

export const CLASSIFICATION_ORDER: Classification[] = ['cong_khai', 'noi_bo', 'mat']
