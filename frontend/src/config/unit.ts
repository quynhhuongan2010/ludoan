// Thong tin nhan dang don vi + lien he hien thi tren portal.
// Sua truc tiep cac gia tri "xxxx" ben duoi bang so lieu that cua don vi.

export const UNIT = {
  shortName: 'CỔNG THÔNG TIN ĐIỆN TỬ',
  fullName: 'LỮ ĐOÀN THÔNG TIN 21 – BỘ ĐỘI BIÊN PHÒNG',
  slogan: 'KỊP THỜI - CHÍNH XÁC – BÍ MẬT – AN TOÀN',
  bannerSlogan: 'QUYẾT TÂM XÂY DỰNG ĐƠN VỊ VỮNG MẠNH TOÀN DIỆN "MẪU MỰC, TIÊU BIỂU"',
  copyrightOwner: 'Ban Chỉ huy Lữ đoàn Thông tin 21',
}

export const CONTACT = {
  hotlineLabel: 'Trực ban tác chiến',
  hotline: '069.xxxx.xxxx',
  address: 'Số 32 Đường Cầu Diễn, Phường Phúc Diễn, Quận Bắc Từ Liêm, Hà Nội',
  internalPhone: 'xxx-xxx',
  email: 'vanphong@ld21.bdbp.vn',
}

// Menu dieu huong chinh.
//   commanderOnly       -> chi role `commander` (hoac `admin`) thay
//   adminOnly           -> chi role `admin` thay
//   directiveChannel    -> chi user co quyen Kenh Chi dao - Bao cao
//   commandChannel      -> chi user co quyen Kenh chuyen BCH + Cap uy
export interface NavEntry {
  label: string
  to?: string
  commanderOnly?: boolean
  adminOnly?: boolean
  directiveChannel?: boolean
  commandChannel?: boolean
  children?: NavEntry[]
}

export const NAV: NavEntry[] = [
  {
    label: 'Bản tin',
    children: [
      { label: 'Bảng tin', to: '/bang-tin' },
      { label: 'Tin tức – Hoạt động', to: '/tin-tuc' },
      { label: 'Thông báo nội bộ', to: '/thong-bao' },
      { label: 'Danh bạ điện thoại', to: '/danh-ba' },
    ],
  },
  { label: 'Giáo dục chính trị', to: '/giao-duc-chinh-tri' },
  { label: 'Văn bản – Tài liệu', to: '/van-ban' },
  {
    label: 'Điều hành – Nhiệm vụ',
    children: [
      { label: 'Chỉ thị – Nhiệm vụ', to: '/chi-thi-nhiem-vu' },
      { label: 'Lịch trực – Kíp trực', to: '/lich-truc' },
      { label: 'Tin nhắn tác chiến', to: '/tin-nhan' },
      { label: 'Chỉ đạo – Báo cáo', to: '/chi-dao-bao-cao', directiveChannel: true },
      { label: 'Giao nhiệm vụ', to: '/giao-nhiem-vu', directiveChannel: true },
    ],
  },
  {
    label: 'Kênh chỉ huy (MẬT)',
    children: [
      { label: 'Trao đổi – Công văn', to: '/kenh-chi-huy', commandChannel: true },
    ],
  },
  {
    label: 'Quản trị',
    children: [
      { label: 'Quản lý người dùng', to: '/quan-ly-nguoi-dung', commanderOnly: true },
      { label: 'Quản lý đơn vị', to: '/quan-ly-don-vi', adminOnly: true },
      { label: 'Nhật ký an ninh', to: '/nhat-ky-an-ninh', commanderOnly: true },
    ],
  },
  { label: 'Hướng dẫn sử dụng', to: '/huong-dan' },
]
