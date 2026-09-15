import { useState, type ReactNode } from 'react'

/**
 * Trang HƯỚNG DẪN SỬ DỤNG — tài liệu tĩnh, không gọi API.
 * Trọng tâm: cách KHAI THÁC phần mềm theo từng nghiệp vụ, có hình minh hoạ giao diện
 * cho từng bước — không trình bày công nghệ/hạ tầng dựng nên hệ thống.
 * 4 tab theo đúng hành trình người dùng: Bắt đầu → Khai thác hằng ngày →
 * Chỉ đạo-điều hành → Tài khoản &amp; Hỗ trợ.
 */

type TabKey = 'bat-dau' | 'khai-thac' | 'chi-dao' | 'tai-khoan'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'bat-dau', label: '1. Bắt đầu sử dụng' },
  { key: 'khai-thac', label: '2. Tra cứu & khai thác hằng ngày' },
  { key: 'chi-dao', label: '3. Chỉ đạo – điều hành' },
  { key: 'tai-khoan', label: '4. Tài khoản của bạn' },
]

export function HuongDanPage() {
  const [tab, setTab] = useState<TabKey>('bat-dau')

  return (
    <section className="guide">
      <h1>Hướng dẫn sử dụng Cổng thông tin nội bộ</h1>
      <p className="guide-lead">
        Cổng thông tin nội bộ Lữ đoàn Thông tin 21 – Bộ đội Biên phòng. Tài liệu này hướng dẫn{' '}
        <strong>cách khai thác từng chức năng</strong> theo đúng quyền hạn tài khoản — dành cho
        toàn thể cán bộ, sĩ quan, quân nhân chuyên nghiệp được cấp tài khoản.
      </p>

      <div className="guide-authorcard">
        <h2>Thông tin sáng kiến</h2>
        <dl>
          <dt>Tên sáng kiến</dt>
          <dd>Cổng thông tin nội bộ chỉ đạo – báo cáo &amp; quản lý văn bản mật Lữ đoàn Thông tin 21</dd>
          <dt>Tác giả</dt>
          <dd>Đồng chí Lê Văn Quỳnh – Đại đội 5, Lữ đoàn Thông tin 21, Bộ đội Biên phòng</dd>
          <dt>Thời gian nghiên cứu &amp; phát triển</dt>
          <dd>Tháng 05/2026 – Tháng 08/2026</dd>
          <dt>Mục đích</dt>
          <dd>
            Số hoá công tác tuyên truyền, quản lý văn bản và chỉ đạo – báo cáo trong nội bộ đơn vị,
            thay thế một phần việc trao đổi giấy tờ, điện thoại, tin nhắn rời rạc bằng một đầu mối
            duy nhất, có phân quyền rõ ràng theo cấp bậc và vị trí công tác.
          </dd>
        </dl>
      </div>

      <div className="tab-bar" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            className={`tab${tab === t.key ? ' active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="guide-panel" role="tabpanel">
        {tab === 'bat-dau' && <BatDau />}
        {tab === 'khai-thac' && <KhaiThac />}
        {tab === 'chi-dao' && <ChiDao />}
        {tab === 'tai-khoan' && <TaiKhoan />}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ helpers */
function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="block-section">
      <div className="block-title">
        <span>{title}</span>
      </div>
      {children}
    </div>
  )
}

/** Bố cục 2 cột: văn bản hướng dẫn bên trái, hình minh hoạ bên phải (tự xuống hàng khi màn hẹp). */
function Split({ children }: { children: ReactNode }) {
  return <div className="guide-split">{children}</div>
}
function SplitText({ children }: { children: ReactNode }) {
  return <div className="guide-split-text">{children}</div>
}

/** Khung "cửa sổ trình duyệt" bao quanh mọi hình minh hoạ, để trông giống một màn hình phần mềm. */
function Frame({ children, caption }: { children: ReactNode; caption: string }) {
  return (
    <figure className="guide-illustration-wrap">
      <svg className="guide-illustration" viewBox="0 0 400 234" role="img" aria-label={caption}>
        <rect x="0.5" y="0.5" width="399" height="233" rx="10" fill="#ffffff" stroke="#d7ded8" />
        <rect x="0.5" y="0.5" width="399" height="27" rx="10" fill="#eef4ef" />
        <rect x="0.5" y="17.5" width="399" height="10" fill="#eef4ef" />
        <circle cx="16" cy="14" r="4" fill="#e6a23c" />
        <circle cx="30" cy="14" r="4" fill="#c8102e" />
        <circle cx="44" cy="14" r="4" fill="#2c6540" />
        <rect x="64" y="8" width="270" height="12" rx="6" fill="#ffffff" stroke="#d7ded8" />
        {children}
      </svg>
      <figcaption className="guide-illustration-caption">{caption}</figcaption>
    </figure>
  )
}

function Badge({ x, y, w, text, tone }: { x: number; y: number; w: number; text: string; tone: 'green' | 'amber' | 'red' | 'gray' }) {
  const fill = { green: '#2c6540', amber: '#e6a23c', red: '#c8102e', gray: '#8a94a6' }[tone]
  return (
    <g>
      <rect x={x} y={y} width={w} height={16} rx={8} fill={fill} />
      <text x={x + w / 2} y={y + 11} textAnchor="middle" fontSize="8" fill="#fff" fontWeight={700}>
        {text}
      </text>
    </g>
  )
}

/* ============================================================ hình minh hoạ */
function ArtLogin() {
  return (
    <Frame caption="Màn hình đăng nhập">
      <rect x="100" y="46" width="200" height="150" rx="8" fill="#fff" stroke="#d7ded8" />
      <text x="200" y="68" textAnchor="middle" fontSize="11" fontWeight={700} fill="#1f4c30">
        Đăng nhập hệ thống
      </text>
      <text x="122" y="86" fontSize="8" fill="#8a94a6">Tên đăng nhập</text>
      <rect x="122" y="90" width="156" height="18" rx="4" fill="#f5f7f5" stroke="#d7ded8" />
      <text x="122" y="118" fontSize="8" fill="#8a94a6">Mật khẩu</text>
      <rect x="122" y="122" width="156" height="18" rx="4" fill="#f5f7f5" stroke="#d7ded8" />
      <rect x="122" y="154" width="156" height="24" rx="5" fill="#2c6540" />
      <text x="200" y="170" textAnchor="middle" fontSize="10" fontWeight={700} fill="#fff">
        Đăng nhập
      </text>
    </Frame>
  )
}

function ArtNav() {
  return (
    <Frame caption="Thanh menu điều hướng — mục hiển thị tuỳ theo quyền tài khoản">
      <rect x="16" y="42" width="368" height="28" rx="5" fill="#fff" stroke="#d7ded8" />
      <rect x="24" y="47" width="62" height="18" rx="9" fill="#2c6540" />
      <text x="55" y="59" textAnchor="middle" fontSize="8" fontWeight={700} fill="#fff">Trang chủ</text>
      <text x="122" y="59" fontSize="9" fill="#333">Tin tức</text>
      <text x="176" y="59" fontSize="9" fill="#333">Thông báo</text>
      <text x="242" y="59" fontSize="9" fill="#333">Lịch trực</text>
      <circle cx="366" cy="56" r="10" fill="#eef4ef" stroke="#2c6540" />
      <text x="366" y="59" textAnchor="middle" fontSize="8" fill="#1f4c30">CB</text>
      <rect x="16" y="88" width="368" height="26" rx="5" fill="#fafbfa" stroke="#e5e5e5" strokeDasharray="3 3" />
      <text x="200" y="104" textAnchor="middle" fontSize="8" fill="#8a94a6">
        Không đủ quyền → mục tự động ẩn khỏi menu (ví dụ: Quản lý người dùng)
      </text>
      <text x="30" y="150" fontSize="9" fill="#333">Đăng xuất</text>
      <rect x="20" y="140" width="90" height="20" rx="4" fill="none" stroke="#c8102e" />
    </Frame>
  )
}

function ArtDashboard() {
  return (
    <Frame caption="Trang chủ — bảng tin tổng hợp">
      {[0, 1, 2, 3].map((i) => (
        <g key={i} transform={`translate(${16 + (i % 2) * 188}, ${44 + Math.floor(i / 2) * 90})`}>
          <rect width="176" height="80" rx="6" fill="#fff" stroke="#d7ded8" />
          <rect x="10" y="10" width="60" height="8" rx="4" fill="#2c6540" />
          <rect x="10" y="26" width="150" height="7" rx="3" fill="#e3e7e3" />
          <rect x="10" y="38" width="130" height="7" rx="3" fill="#e3e7e3" />
          <rect x="10" y="50" width="140" height="7" rx="3" fill="#e3e7e3" />
        </g>
      ))}
    </Frame>
  )
}

function ArtNewsFeed() {
  const rows: [string, string, 'green' | 'amber'][] = [
    ['Hội thao huấn luyện chuyên ngành thông tin', 'Huấn luyện · 10/09/2026', 'green'],
    ['Đại đội 5 giúp dân sửa chữa nhà cửa', 'Dân vận · 08/09/2026', 'green'],
    ['Bản nháp: gương người tốt việc tốt tháng 9', 'Gương người tốt · 07/09/2026', 'amber'],
  ]
  return (
    <Frame caption="Tin tức – Hoạt động đơn vị">
      {rows.map(([title, meta, tone], i) => (
        <g key={i} transform={`translate(16, ${42 + i * 62})`}>
          <rect width="368" height="52" rx="6" fill="#fff" stroke="#d7ded8" />
          <rect x="8" y="8" width="56" height="36" rx="4" fill="#dfeee3" />
          <text x="72" y="24" fontSize="9" fill="#222" fontWeight={700}>{title.slice(0, 34)}</text>
          <text x="72" y="38" fontSize="8" fill="#8a94a6">{meta}</text>
          <Badge x={286} y={18} w={72} text={tone === 'green' ? 'Đã duyệt' : 'Chờ duyệt'} tone={tone} />
        </g>
      ))}
    </Frame>
  )
}

function ArtAnnouncement() {
  const rows: [string, 'red' | 'amber' | 'green', boolean][] = [
    ['Nghỉ trực thay ca do diễn tập cuối tuần', 'red', true],
    ['Lịch kiểm tra chính trị quý III/2026', 'amber', false],
    ['Thông báo lịch cắt điện bảo trì', 'green', false],
  ]
  return (
    <Frame caption="Thông báo nội bộ — mức ưu tiên & ghim">
      <circle cx="30" cy="46" r="9" fill="#eef4ef" stroke="#2c6540" />
      <path d="M30 41 q5 0 5 6 l0 3 l2 2 h-14 l2 -2 l0 -3 q0 -6 5 -6 z" fill="#2c6540" />
      {rows.map(([text, tone, pinned], i) => (
        <g key={i} transform={`translate(16, ${64 + i * 46})`}>
          <rect width="368" height="38" rx="6" fill="#fff" stroke="#d7ded8" />
          <circle cx="16" cy="19" r="5" fill={{ red: '#c8102e', amber: '#e6a23c', green: '#2c6540' }[tone]} />
          <text x="30" y="17" fontSize="9" fill="#222">{text.slice(0, 40)}</text>
          <text x="30" y="30" fontSize="7.5" fill="#8a94a6">Đơn vị · vừa đăng</text>
          {pinned && <Badge x={318} y={11} w={40} text="Ghim" tone="gray" />}
        </g>
      ))}
    </Frame>
  )
}

function ArtDuty() {
  const days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
  return (
    <Frame caption="Lịch trực tuần — bảng tổng hợp toàn đơn vị">
      <rect x="16" y="42" width="368" height="26" rx="4" fill="#eef4ef" />
      <text x="46" y="59" fontSize="8" fill="#1f4c30" fontWeight={700}>Ca / Ngày</text>
      {days.map((d, i) => (
        <text key={d} x={112 + i * 40} y={59} textAnchor="middle" fontSize="9" fontWeight={700} fill="#1f4c30">
          {d}
        </text>
      ))}
      {['Ca ngày', 'Ca đêm'].map((label, r) => (
        <g key={label}>
          <rect x="16" y={68 + r * 34} width="368" height="34" fill={r % 2 ? '#fafbfa' : '#fff'} stroke="#e5e5e5" />
          <text x="20" y={68 + r * 34 + 21} fontSize="8" fill="#333">{label}</text>
          {days.map((_, c) => {
            const active = r === 0 && c === 3
            return (
              <g key={c}>
                <rect x={92 + c * 40} y={72 + r * 34} width="36" height="26" rx="4" fill={active ? '#2c6540' : 'none'} />
                {active && (
                  <text x={92 + c * 40 + 18} y={72 + r * 34 + 17} textAnchor="middle" fontSize="7.5" fill="#fff" fontWeight={700}>
                    Bạn trực
                  </text>
                )}
              </g>
            )
          })}
        </g>
      ))}
    </Frame>
  )
}

function ArtDocuments() {
  const rows: [string, 'green' | 'gray'][] = [
    ['Mẫu đơn xin nghỉ phép 2026.docx', 'green'],
    ['Kế hoạch huấn luyện quý III.pdf', 'gray'],
    ['Báo cáo sơ kết 6 tháng đầu năm.xlsx', 'gray'],
  ]
  return (
    <Frame caption="Văn bản – Tài liệu – Biểu mẫu">
      {rows.map(([name, tone], i) => (
        <g key={i} transform={`translate(16, ${44 + i * 52})`}>
          <rect width="368" height="42" rx="6" fill="#fff" stroke="#d7ded8" />
          <rect x="10" y="10" width="22" height="22" rx="3" fill="#eef4ef" stroke="#2c6540" />
          <path d="M15 15 h12 v12 h-12 z" fill="none" stroke="#2c6540" strokeWidth={1} />
          <text x="42" y="25" fontSize="9" fill="#222">{name.slice(0, 38)}</text>
          <Badge x={230} y={13} w={64} text={tone === 'green' ? 'Công khai' : 'Nội bộ'} tone={tone === 'green' ? 'green' : 'gray'} />
          <circle cx="340" cy="21" r="11" fill="#eef4ef" stroke="#2c6540" />
          <path d="M340 15 v9 M336 20 l4 5 l4 -5" fill="none" stroke="#2c6540" strokeWidth={1.4} />
        </g>
      ))}
    </Frame>
  )
}

function ArtEducation() {
  return (
    <Frame caption="Giáo dục chính trị — bài học theo tuần/tháng">
      <path d="M40 46 h60 v70 q-30 -8 -60 0 z" fill="#eef4ef" stroke="#2c6540" />
      <path d="M160 46 h-60 v70 q30 -8 60 0 z" fill="#eef4ef" stroke="#2c6540" />
      <line x1="100" y1="46" x2="100" y2="116" stroke="#2c6540" />
      {[0, 1].map((i) => (
        <g key={i} transform={`translate(200, ${46 + i * 56})`}>
          <rect width="184" height="46" rx="6" fill="#fff" stroke="#d7ded8" />
          <text x="10" y="18" fontSize="9" fontWeight={700} fill="#222">
            {i === 0 ? 'Học tập chính trị – quân sự' : 'Pháp luật biên giới'}
          </text>
          <Badge x={10} y={24} w={80} text={i === 0 ? 'Tuần 35/2026' : 'Tuần 34/2026'} tone="green" />
          <text x="150" y="36" fontSize="8" fill="#8a94a6">📎</text>
        </g>
      ))}
    </Frame>
  )
}

function ArtDirective() {
  return (
    <Frame caption="Chỉ thị – Nhiệm vụ & xác nhận đã tiếp thu">
      <rect x="60" y="42" width="280" height="70" rx="6" fill="#fff" stroke="#d7ded8" />
      <rect x="76" y="54" width="140" height="9" rx="2" fill="#1f4c30" />
      <rect x="76" y="70" width="248" height="6" rx="2" fill="#e3e7e3" />
      <rect x="76" y="82" width="220" height="6" rx="2" fill="#e3e7e3" />
      <rect x="76" y="94" width="180" height="6" rx="2" fill="#e3e7e3" />
      <rect x="60" y="126" width="280" height="10" rx="5" fill="#e3e7e3" />
      <rect x="60" y="126" width="200" height="10" rx="5" fill="#2c6540" />
      <text x="200" y="152" textAnchor="middle" fontSize="8.5" fill="#333">8 / 10 đơn vị đã tiếp thu</text>
      <rect x="150" y="166" width="100" height="24" rx="12" fill="#2c6540" />
      <text x="200" y="182" textAnchor="middle" fontSize="9" fontWeight={700} fill="#fff">✓ Đã tiếp thu</text>
    </Frame>
  )
}

function ArtThread() {
  return (
    <Frame caption="Kênh Chỉ đạo – Báo cáo (trao đổi theo đơn vị)">
      <g>
        <rect x="20" y="44" width="180" height="34" rx="10" fill="#eef4ef" />
        <text x="32" y="65" fontSize="8.5" fill="#222">Đại đội 5: đã nhận nhiệm vụ, triển khai ngay.</text>
      </g>
      <g>
        <rect x="200" y="86" width="180" height="34" rx="10" fill="#2c6540" />
        <text x="212" y="107" fontSize="8.5" fill="#fff">BCH: báo cáo tiến độ trước 17h.</text>
      </g>
      <g>
        <rect x="20" y="128" width="200" height="30" rx="10" fill="#eef4ef" />
        <text x="32" y="146" fontSize="8.5" fill="#222">📎 Đính kèm: bao-cao-tien-do.pdf</text>
      </g>
      <rect x="16" y="188" width="300" height="26" rx="6" fill="#fff" stroke="#d7ded8" />
      <text x="26" y="205" fontSize="8" fill="#8a94a6">Nhập nội dung trao đổi…</text>
      <rect x="326" y="188" width="58" height="26" rx="6" fill="#2c6540" />
      <text x="355" y="205" textAnchor="middle" fontSize="8.5" fontWeight={700} fill="#fff">Gửi</text>
    </Frame>
  )
}

function ArtSecure() {
  return (
    <Frame caption="Kênh chuyên BCH & Cấp uỷ (bậc MẬT)">
      <rect x="16" y="42" width="368" height="184" rx="6" fill="#fff" stroke="#c8102e" strokeWidth={1.5} />
      <rect x="30" y="52" width="70" height="16" rx="8" fill="#c8102e" />
      <text x="65" y="64" textAnchor="middle" fontSize="8" fontWeight={700} fill="#fff">MẬT</text>
      <rect x="150" y="70" width="22" height="18" rx="3" fill="none" stroke="#1f4c30" strokeWidth={1.4} />
      <path d="M154 70 v-6 a6 6 0 0 1 12 0 v6" fill="none" stroke="#1f4c30" strokeWidth={1.4} />
      <text x="30" y="112" fontSize="9" fontWeight={700} fill="#1f4c30">Sổ công văn đi — đến</text>
      {[['Đi', '17/CV-LD', 'Đã xử lý', 'green'], ['Đến', '112/BC', 'Mới', 'amber']].map(([dir, num, st, tone], i) => (
        <g key={i} transform={`translate(30, ${122 + i * 30})`}>
          <rect width="330" height="24" rx="4" fill="#fafbfa" stroke="#e5e5e5" />
          <Badge x={6} y={4} w={30} text={dir as string} tone="gray" />
          <text x={44} y={17} fontSize="8.5" fill="#222">{num}</text>
          <Badge x={260} y={4} w={62} text={st as string} tone={tone as 'green' | 'amber'} />
        </g>
      ))}
    </Frame>
  )
}

function ArtProfile() {
  return (
    <Frame caption="Hồ sơ cá nhân — sửa thông tin & đổi mật khẩu">
      <circle cx="90" cy="80" r="30" fill="#eef4ef" stroke="#2c6540" />
      <circle cx="90" cy="70" r="10" fill="#2c6540" />
      <path d="M70 100 q20 -18 40 0" fill="#2c6540" />
      <text x="90" y="122" textAnchor="middle" fontSize="8" fill="#8a94a6">Họ và tên</text>
      <rect x="150" y="52" width="220" height="16" rx="4" fill="#f5f7f5" stroke="#d7ded8" />
      <text x="150" y="48" fontSize="8" fill="#8a94a6">Họ và tên</text>
      <text x="150" y="84" fontSize="8" fill="#8a94a6">Mật khẩu hiện tại</text>
      <rect x="150" y="88" width="220" height="16" rx="4" fill="#f5f7f5" stroke="#d7ded8" />
      <text x="150" y="116" fontSize="8" fill="#8a94a6">Mật khẩu mới</text>
      <rect x="150" y="120" width="220" height="16" rx="4" fill="#f5f7f5" stroke="#d7ded8" />
      <rect x="150" y="148" width="110" height="22" rx="5" fill="#2c6540" />
      <text x="205" y="163" textAnchor="middle" fontSize="8.5" fontWeight={700} fill="#fff">Lưu thay đổi</text>
    </Frame>
  )
}

function ArtUserManage() {
  const rows: [string, string, 'green' | 'amber'][] = [
    ['Nguyễn Văn A', 'Cán bộ', 'green'],
    ['Trần Thị B', 'Chờ kích hoạt', 'amber'],
    ['Lê Văn C', 'Chỉ huy', 'green'],
  ]
  return (
    <Frame caption="Quản lý người dùng — duyệt & cấp quyền (chỉ huy/quản trị)">
      <rect x="16" y="42" width="368" height="22" rx="4" fill="#eef4ef" />
      <text x="26" y="57" fontSize="8" fontWeight={700} fill="#1f4c30">Họ tên</text>
      <text x="180" y="57" fontSize="8" fontWeight={700} fill="#1f4c30">Vai trò</text>
      <text x="300" y="57" fontSize="8" fontWeight={700} fill="#1f4c30">Kích hoạt</text>
      {rows.map(([name, role, tone], i) => (
        <g key={i} transform={`translate(0, ${64 + i * 32})`}>
          <rect x="16" width="368" height="30" fill={i % 2 ? '#fafbfa' : '#fff'} stroke="#e5e5e5" />
          <text x="26" y="20" fontSize="8.5" fill="#222">{name}</text>
          <Badge x={172} y={7} w={80} text={role} tone={tone} />
          <rect x="300" y="8" width="30" height="14" rx="7" fill={tone === 'green' ? '#2c6540' : '#d7ded8'} />
          <circle cx={tone === 'green' ? 322 : 308} cy="15" r="6" fill="#fff" />
        </g>
      ))}
    </Frame>
  )
}

/* ============================================================ tab 1 */
function BatDau() {
  return (
    <>
      <Block title="Truy cập hệ thống lần đầu">
        <Split>
          <SplitText>
            <ol className="guide-list guide-ol">
              <li>Mở trình duyệt (Chrome, Edge, Cốc Cốc…) trên máy tính đã kết nối mạng nội bộ đơn vị.</li>
              <li>Gõ địa chỉ Cổng thông tin do bộ phận kỹ thuật cung cấp, bấm <strong>Đăng nhập</strong>.</li>
              <li>Nhập <strong>tên đăng nhập</strong> và <strong>mật khẩu</strong> do chỉ huy/quản trị cấp.</li>
              <li>
                Lần đầu đăng nhập (hoặc sau khi được cấp lại mật khẩu): hệ thống{' '}
                <strong>bắt buộc đổi mật khẩu mới</strong> trước khi vào các màn hình bên trong.
              </li>
            </ol>
            <p className="guide-note">
              Quên mật khẩu hoặc đăng nhập báo lỗi? Liên hệ trực tiếp chỉ huy đơn vị hoặc quản trị hệ
              thống để được <strong>cấp lại mật khẩu</strong> — không tự đoán, không dùng chung tài
              khoản với người khác.
            </p>
          </SplitText>
          <ArtLogin />
        </Split>
      </Block>

      <Block title="Tự đăng ký tài khoản mới">
        <p>
          Nếu chưa có tài khoản, bấm <strong>Đăng ký</strong> ở màn hình đăng nhập, điền họ tên/tên
          đăng nhập/mật khẩu. Tài khoản mới ở trạng thái <strong>chờ duyệt</strong> — chưa đăng nhập
          được ngay.
        </p>
        <ul className="guide-list">
          <li>Chỉ huy đơn vị bổ sung <strong>cấp bậc, chức danh, đơn vị công tác</strong> cho tài khoản.</li>
          <li>Sau khi đủ thông tin, chỉ huy bấm <strong>kích hoạt</strong> — lúc này mới đăng nhập được.</li>
          <li>Trong lúc chờ, có thể liên hệ trực tiếp chỉ huy để được xử lý nhanh hơn.</li>
        </ul>
      </Block>

      <Block title="Làm quen giao diện & menu điều hướng">
        <Split>
          <ArtNav />
          <SplitText>
            <p>Sau khi đăng nhập, thanh menu ngang trên cùng là nơi di chuyển giữa các phân hệ:</p>
            <ul className="guide-list">
              <li>Các mục hiển thị <strong>tuỳ theo quyền tài khoản của bạn</strong> — không thấy mục nào nghĩa là tài khoản chưa được cấp quyền vào mục đó, không phải lỗi phần mềm.</li>
              <li>Góc phải hiển thị tên/vai trò tài khoản đang đăng nhập và nút <strong>Đăng xuất</strong>.</li>
              <li>Dùng máy dùng chung (phòng trực, máy công vụ): luôn bấm <strong>Đăng xuất</strong> sau khi xong việc.</li>
            </ul>
          </SplitText>
        </Split>
      </Block>

      <Block title="Vai trò tài khoản quyết định bạn thấy & làm được gì">
        <table className="guide-table">
          <thead>
            <tr>
              <th>Nhóm tài khoản</th>
              <th>Thường là ai</th>
              <th>Xem được</th>
              <th>Đăng / sửa / duyệt được</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Chỉ huy các cấp</td>
              <td>Lữ trưởng, Chính uỷ, Phó Lữ trưởng/Phó Chính uỷ, chỉ huy đơn vị</td>
              <td>Toàn bộ nội dung, kể cả bản nháp/chưa duyệt</td>
              <td>Ban hành Chỉ thị, duyệt bài viết/bảng trực, quản lý tài khoản, giao nhiệm vụ</td>
            </tr>
            <tr>
              <td>Cán bộ, sĩ quan/QNCN</td>
              <td>Cán bộ các phòng ban, đại đội</td>
              <td>Nội dung nội bộ đã duyệt + bài do mình soạn</td>
              <td>Đăng/sửa Tin tức, Giáo dục chính trị, lập bảng trực (chờ chỉ huy duyệt)</td>
            </tr>
            <tr>
              <td>Người dùng mới kích hoạt</td>
              <td>Tài khoản vừa được duyệt, chưa giao việc đăng nội dung</td>
              <td>Toàn bộ nội dung nội bộ (chỉ xem)</td>
              <td>Chưa đăng/sửa được nội dung nào</td>
            </tr>
          </tbody>
        </table>
        <p className="guide-note">
          Ngoài ra, một số tài khoản được cấp thêm quyền riêng: xem nội dung <strong>bậc MẬT</strong>,
          hoặc tham gia <strong>Kênh Chỉ đạo – Báo cáo</strong> — xem chi tiết ở tab{' '}
          <em>3. Chỉ đạo – điều hành</em>.
        </p>
      </Block>

      <Block title="Yên tâm khi đang soạn dở mà mất điện, rớt mạng">
        <p>
          Các form soạn nội dung dài (ban hành Chỉ thị, trao đổi trong Kênh Chỉ đạo, giao nhiệm vụ,
          Kênh chuyên BCH) <strong>tự động lưu bản nháp ngay trên máy đang gõ</strong>, không cần bấm
          nút lưu riêng. Lỡ tải lại trang, mất điện hay rớt mạng trước khi kịp gửi: mở lại đúng màn
          hình đó, nội dung sẽ <strong>tự khôi phục</strong>. Sau khi gửi thành công, bản nháp tạm tự
          xoá.
        </p>
      </Block>
    </>
  )
}

/* ============================================================ tab 2 */
function KhaiThac() {
  return (
    <>
      <Block title="Trang chủ — bảng tin tổng hợp">
        <Split>
          <ArtDashboard />
          <SplitText>
            <p>
              Vào hệ thống là thấy ngay <strong>Trang chủ</strong>, gộp sẵn những gì mới nhất trong
              đơn vị để không phải mở từng mục: tin tức mới, bài Giáo dục chính trị mới, Chỉ thị mới
              ban hành, thông báo mới — mỗi loại vài mục gần nhất, bấm vào để xem đầy đủ.
            </p>
          </SplitText>
        </Split>
      </Block>

      <Block title="Tin tức – Hoạt động đơn vị">
        <Split>
          <SplitText>
            <p><strong>Xem:</strong> mọi tài khoản xem được tin đã duyệt; người ngoài đơn vị (khách LAN chưa đăng nhập) chỉ xem tin công khai.</p>
            <p><strong>Đăng bài mới</strong> (cán bộ trở lên):</p>
            <ol className="guide-list guide-ol">
              <li>Vào mục <strong>Tin tức</strong> → bấm <strong>Đăng bài mới</strong>.</li>
              <li>Chọn danh mục (Huấn luyện, Dân vận, Khen thưởng, Gương người tốt…), nhập tiêu đề, nội dung, có thể tải ảnh bìa.</li>
              <li>Cán bộ đăng → bài vào trạng thái <strong>Chờ duyệt</strong>; chỉ huy đăng → hiển thị ngay.</li>
              <li>Chỉ huy vào xem danh sách chờ duyệt, bấm <strong>Duyệt</strong> hoặc <strong>Trả lại</strong> kèm ghi chú lý do.</li>
              <li>Bài bị trả lại/đã duyệt mà cán bộ sửa lại → tự quay về trạng thái Chờ duyệt.</li>
            </ol>
          </SplitText>
          <ArtNewsFeed />
        </Split>
      </Block>

      <Block title="Thông báo nội bộ">
        <Split>
          <ArtAnnouncement />
          <SplitText>
            <p>
              Danh sách thông báo sắp xếp theo thứ tự: <strong>ghim</strong> lên đầu → mức{' '}
              <strong>ưu tiên</strong> (khẩn → cao → bình thường → thấp) → mới nhất. Một số thông báo
              được đánh dấu <strong>công khai</strong>, xem được cả khi chưa đăng nhập.
            </p>
            <p>Cán bộ trở lên đăng thông báo mới, chọn mức ưu tiên, có thể ghim và đặt ngày hết hiệu lực để tự ẩn khi qua hạn.</p>
          </SplitText>
        </Split>
      </Block>

      <Block title="Lịch trực – Trực ban – Bàn giao ca">
        <Split>
          <SplitText>
            <ul className="guide-list">
              <li><strong>Xem lịch trực</strong>: mọi tài khoản xem được bảng trực tuần/ngày tổng hợp toàn đơn vị.</li>
              <li><strong>Lập bảng trực</strong> (cán bộ trở lên): tạo bảng trực theo tuần cho đơn vị mình, thêm từng ca trực (chỉ huy, tác chiến, nội vụ, chuyên môn, canh gác…) kèm người trực, số điện thoại liên hệ.</li>
              <li><strong>Duyệt bảng trực</strong>: chỉ chỉ huy được duyệt; bảng đã duyệt mới lên bảng tổng hợp toàn Lữ đoàn.</li>
              <li><strong>Bàn giao ca điện tử</strong>: kíp trực trước ghi lại quân số, tình trạng trang bị, sự việc trong ca, việc còn tồn; kíp sau xác nhận đã nhận hoặc nêu kiến nghị.</li>
            </ul>
          </SplitText>
          <ArtDuty />
        </Split>
      </Block>

      <Block title="Văn bản – Tài liệu – Biểu mẫu">
        <Split>
          <ArtDocuments />
          <SplitText>
            <p>Tìm tài liệu theo danh mục: biểu mẫu, hướng dẫn, quy chế/quy định, kế hoạch, báo cáo, văn bản chỉ đạo.</p>
            <p>Bấm biểu tượng tải xuống để lưu file về máy. Tài liệu đánh dấu <strong>Công khai</strong> xem/tải được cả khi chưa đăng nhập; còn lại cần đăng nhập.</p>
            <p>Cán bộ trở lên đăng tài liệu mới bằng cách tải file lên (.pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx), chọn danh mục và mức công khai/nội bộ.</p>
          </SplitText>
        </Split>
      </Block>

      <Block title="Giáo dục chính trị">
        <Split>
          <SplitText>
            <p>Mọi tài khoản đã đăng nhập xem được toàn bộ bài Giáo dục chính trị, phân theo chủ đề: học tập chính trị – quân sự, tuyên truyền, pháp luật biên giới, lịch sử truyền thống.</p>
            <p>Bài định kỳ theo tuần/tháng có nhãn kèm theo (ví dụ "Tuần 35/2026") để dễ theo dõi tiến độ học tập; một số bài có tài liệu đính kèm để tải về.</p>
            <p>Cán bộ trở lên đăng/biên tập bài học mới cho mục này.</p>
          </SplitText>
          <ArtEducation />
        </Split>
      </Block>
    </>
  )
}

/* ============================================================ tab 3 */
function ChiDao() {
  return (
    <>
      <Block title="Chỉ thị – Nhiệm vụ">
        <Split>
          <ArtDirective />
          <SplitText>
            <p>Chỉ huy ban hành Chỉ thị; mọi tài khoản xem được bản đã ban hành (chỉ huy còn xem được cả bản nháp chưa ban hành).</p>
            <p>Đọc xong, bấm <strong>Đã tiếp thu</strong> để xác nhận đã quán triệt nội dung — mỗi người chỉ cần bấm một lần.</p>
            <p>Chỉ huy theo dõi số đơn vị/cá nhân đã tiếp thu và danh sách còn chưa tiếp thu để đôn đốc kịp thời.</p>
          </SplitText>
        </Split>
      </Block>

      <Block title="Kênh Chỉ đạo – Báo cáo">
        <p>
          Dành cho tài khoản được cấp quyền vào kênh chỉ đạo (thường là chỉ huy đơn vị). Đây là nơi
          Ban chỉ huy Lữ đoàn trao đổi công việc trực tiếp với từng đơn vị, tách riêng theo từng luồng.
        </p>
        <Split>
          <SplitText>
            <ul className="guide-list">
              <li>Ban chỉ huy Lữ đoàn thấy tất cả các luồng; mỗi đơn vị chỉ thấy luồng của đơn vị mình.</li>
              <li>Nhắn tin qua lại, gửi kèm tệp đính kèm (báo cáo, hình ảnh…) trong luồng.</li>
              <li>Hệ thống đánh dấu tin đã đọc/chưa đọc để biết còn nội dung cần xem.</li>
              <li>Ban chỉ huy có thể <strong>đóng luồng</strong> khi công việc đã xử lý xong.</li>
            </ul>
          </SplitText>
          <ArtThread />
        </Split>
      </Block>

      <Block title="Giao nhiệm vụ & nộp báo cáo tiến độ">
        <ul className="guide-list">
          <li><strong>Giao việc</strong> (chỉ huy): tạo nhiệm vụ, chọn đơn vị hoặc cá nhân thực hiện, đặt hạn hoàn thành; có thể gắn với một Chỉ thị đã ban hành.</li>
          <li><strong>Nộp báo cáo</strong> (đơn vị/cá nhân được giao): viết nội dung báo cáo tiến độ, đính kèm tệp minh chứng nếu cần.</li>
          <li><strong>Duyệt báo cáo</strong> (chỉ huy): xem báo cáo, đánh giá <strong>Đạt</strong> hoặc <strong>Trả lại</strong> kèm ghi chú; báo cáo bị trả lại phải nộp lại.</li>
          <li>Trạng thái nhiệm vụ tự cập nhật theo tiến độ: <strong>Chưa giao</strong> → <strong>Đang thực hiện</strong> → <strong>Hoàn thành</strong>; nhiệm vụ trễ hạn được đánh dấu <strong>Quá hạn</strong> để dễ nhận biết.</li>
        </ul>
      </Block>

      <Block title="Kênh chuyên Ban Chỉ huy & Cấp uỷ (bậc MẬT)">
        <Split>
          <ArtSecure />
          <SplitText>
            <p>
              Chỉ tài khoản <strong>chỉ huy/quản trị</strong> hoặc được cấp riêng <strong>quyền xem
              MẬT</strong> mới vào được kênh này — tài khoản khác bấm vào sẽ báo không đủ quyền.
            </p>
            <ul className="guide-list">
              <li>Trao đổi nội bộ dành riêng cho Ban chỉ huy và Cấp uỷ, không phân theo đơn vị.</li>
              <li><strong>Sổ công văn đi/đến</strong>: ghi số hiệu, đơn vị gửi/nhận, ngày ban hành/nhận, tệp đính kèm.</li>
              <li>Người nhận <strong>ký nhận</strong> công văn (kèm ghi chú nếu có ý kiến).</li>
              <li>Vào sổ, sửa, xoá công văn hoặc đóng luồng: chỉ chỉ huy/quản trị được thực hiện.</li>
            </ul>
          </SplitText>
        </Split>
      </Block>
    </>
  )
}

/* ============================================================ tab 4 */
function TaiKhoan() {
  return (
    <>
      <Block title="Hồ sơ cá nhân">
        <Split>
          <ArtProfile />
          <SplitText>
            <p>Vào mục <strong>Hồ sơ cá nhân</strong> (thường ở menu góc phải, dưới tên tài khoản) để:</p>
            <ul className="guide-list">
              <li>Sửa lại họ và tên hiển thị.</li>
              <li>Đổi mật khẩu: nhập mật khẩu hiện tại + mật khẩu mới. Mật khẩu cũ nhập sai sẽ báo lỗi ngay, không đổi được.</li>
            </ul>
            <p className="guide-note">
              Cấp bậc, chức danh, đơn vị công tác do chỉ huy/quản trị chỉnh sửa — không tự sửa được ở
              mục này; nếu thông tin sai, báo lại chỉ huy đơn vị.
            </p>
          </SplitText>
        </Split>
      </Block>

      <Block title="Quản lý người dùng (dành cho chỉ huy/quản trị)">
        <Split>
          <ArtUserManage />
          <SplitText>
            <ul className="guide-list">
              <li>Xem danh sách tài khoản <strong>chờ kích hoạt</strong>, bổ sung cấp bậc/chức danh/đơn vị công tác còn thiếu, rồi bấm <strong>kích hoạt</strong>.</li>
              <li>Đổi vai trò tài khoản (ví dụ cán bộ ↔ chỉ huy) khi có quyết định điều động, bổ nhiệm.</li>
              <li>Cấp hoặc thu quyền xem nội dung <strong>MẬT</strong>, cấp quyền vào <strong>Kênh Chỉ đạo – Báo cáo</strong> cho từng tài khoản.</li>
              <li>Gán tài khoản vào đúng <strong>đơn vị công tác</strong> để nhận nhiệm vụ, xem báo cáo theo đúng đầu mối.</li>
              <li>Khoá/mở tài khoản, cấp lại mật khẩu khi cán bộ quên.</li>
            </ul>
            <p className="guide-note">
              Hệ thống luôn giữ lại tối thiểu một tài khoản chỉ huy đang hoạt động — không thể tự hạ
              quyền hoặc khoá chính mình nếu đó là tài khoản chỉ huy cuối cùng.
            </p>
          </SplitText>
        </Split>
      </Block>

      <Block title="Câu hỏi thường gặp">
        <dl className="guide-authorcard" style={{ marginBottom: 0 }}>
          <dt>Tôi không thấy một mục trên menu mà đồng nghiệp có?</dt>
          <dd>Mục đó cần quyền riêng (ví dụ quyền xem MẬT, quyền vào Kênh Chỉ đạo). Liên hệ chỉ huy/quản trị để được cấp nếu công việc yêu cầu.</dd>
          <dt>Đăng bài xong mà không thấy hiển thị ở danh sách chung?</dt>
          <dd>Bài đang ở trạng thái <strong>Chờ duyệt</strong> — vẫn thấy được trong mục của riêng mình, chờ chỉ huy duyệt mới hiển thị công khai.</dd>
          <dt>Đăng ký xong không đăng nhập được, báo tài khoản chưa kích hoạt?</dt>
          <dd>Bình thường — chờ chỉ huy bổ sung cấp bậc/chức danh/đơn vị rồi kích hoạt. Có thể báo trực tiếp chỉ huy để xử lý nhanh hơn.</dd>
          <dt>Đang thao tác bỗng bị đẩy về trang đăng nhập?</dt>
          <dd>Phiên đăng nhập có thời hạn nên tự hết hạn sau một thời gian. Đăng nhập lại là dùng tiếp bình thường; nội dung đang soạn dở đã tự lưu nháp và sẽ tự khôi phục khi mở lại đúng màn hình.</dd>
          <dt>Vừa được đổi quyền/vai trò nhưng menu chưa cập nhật?</dt>
          <dd>Đăng xuất rồi đăng nhập lại để hệ thống nạp lại đúng quyền mới.</dd>
          <dt>Không mở được trang, hoặc trang báo lỗi liên tục?</dt>
          <dd>Có thể do sự cố mạng nội bộ hoặc máy chủ — liên hệ bộ phận kỹ thuật của đơn vị để được kiểm tra, không phải lỗi thao tác của bạn.</dd>
        </dl>
      </Block>
    </>
  )
}
