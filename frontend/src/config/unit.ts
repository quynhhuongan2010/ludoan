// Thong tin nhan dang don vi + lien he hien thi tren portal.
// Sua truc tiep cac gia tri "xxxx" ben duoi bang so lieu that cua don vi.

export const UNIT = {
  shortName: 'CỔNG THÔNG TIN ĐIỆN TỬ',
  fullName: 'LỮ ĐOÀN THÔNG TIN 21 – BỘ ĐỘI BIÊN PHÒNG',
  slogan: 'TRUNG THÀNH – MƯU TRÍ – KỊP THỜI – CHÍNH XÁC – BÍ MẬT',
  bannerSlogan: 'QUYẾT TÂM XÂY DỰNG ĐƠN VỊ VỮNG MẠNH TOÀN DIỆN "MẪU MỰC, TIÊU BIỂU"',
  copyrightOwner: 'Ban Chỉ huy Lữ đoàn Thông tin 21',
}

export const CONTACT = {
  hotlineLabel: 'Trực ban tác chiến',
  hotline: '069.xxxx.xxxx',
  address: 'Khu vực đóng quân Lữ đoàn Thông tin 21',
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
  to: string
  commanderOnly?: boolean
  adminOnly?: boolean
  directiveChannel?: boolean
  commandChannel?: boolean
}

export const NAV: NavEntry[] = [
  { label: 'Bảng tin', to: '/bang-tin' },
  { label: 'Tin tức – Hoạt động', to: '/tin-tuc' },
  { label: 'Thông báo – Lịch trực', to: '/thong-bao' },
  { label: 'Văn bản – Tài liệu', to: '/van-ban' },
  { label: 'Giáo dục chính trị', to: '/giao-duc-chinh-tri' },
  { label: 'Chỉ thị – Nhiệm vụ', to: '/chi-thi-nhiem-vu' },
  { label: 'Chỉ đạo – Báo cáo', to: '/chi-dao-bao-cao', directiveChannel: true },
  { label: 'Giao nhiệm vụ', to: '/giao-nhiem-vu', directiveChannel: true },
  { label: 'Kênh chỉ huy (MẬT)', to: '/kenh-chi-huy', commandChannel: true },
  { label: 'Giao ban trực tuyến', to: '/giao-ban', commandChannel: true },
  { label: 'Hồ sơ cá nhân', to: '/ho-so' },
  { label: 'Hướng dẫn sử dụng', to: '/huong-dan' },
  { label: 'Quản lý người dùng', to: '/quan-ly-nguoi-dung', commanderOnly: true },
  { label: 'Quản lý đơn vị', to: '/quan-ly-don-vi', adminOnly: true },
]
