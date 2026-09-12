import { useState, type ReactNode } from 'react'

/**
 * Trang HƯỚNG DẪN SỬ DỤNG — tài liệu tĩnh, không gọi API.
 * 4 tab: Kiến trúc phần mềm · Hạ tầng mạng LAN · Thiết lập máy trạm/người dùng · Xử lý sự cố.
 * Dùng chung cho mọi tài khoản đã đăng nhập (bộ phận kỹ thuật tiếp nhận + người dùng cuối).
 */

type TabKey = 'kien-truc' | 'ha-tang' | 'may-tram' | 'su-co'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'kien-truc', label: '1. Kiến trúc phần mềm' },
  { key: 'ha-tang', label: '2. Hạ tầng mạng nội bộ (LAN)' },
  { key: 'may-tram', label: '3. Thiết lập máy trạm & người dùng' },
  { key: 'su-co', label: '4. Cẩm nang xử lý sự cố' },
]

export function HuongDanPage() {
  const [tab, setTab] = useState<TabKey>('kien-truc')

  return (
    <section className="guide">
      <h1>Hướng dẫn sử dụng &amp; tiếp nhận hệ thống</h1>
      <p className="guide-lead">
        Cổng thông tin nội bộ Lữ đoàn Thông tin 21 – Bộ đội Biên phòng. Tài liệu này dành cho
        <strong> bộ phận kỹ thuật tiếp nhận</strong> (cài đặt, vận hành, xử lý sự cố) và
        <strong> người dùng cuối</strong> (khai thác theo quyền hạn).
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
          <dt>Phương pháp thực hiện</dt>
          <dd>
            Ứng dụng kỹ thuật <strong>Vibecoding</strong> kết hợp trí tuệ nhân tạo (AI-driven
            development): thiết kế kiến trúc 3 tầng chuẩn mực, tự động hoá quy trình Contract-First
            (đồng bộ hợp đồng API Backend ↔ Frontend) và kiểm thử toàn diện.
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
        {tab === 'kien-truc' && <KienTruc />}
        {tab === 'ha-tang' && <HaTang />}
        {tab === 'may-tram' && <MayTram />}
        {tab === 'su-co' && <SuCo />}
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

function Code({ children }: { children: ReactNode }) {
  return <pre className="guide-code">{children}</pre>
}

/* ------------------------------------------------------------------ tab 1 */
function KienTruc() {
  return (
    <>
      <Block title="Mô hình tổng thể">
        <p>
          Hệ thống là một <strong>ứng dụng web Fullstack</strong> chạy khép kín trong mạng nội bộ đơn
          vị, gồm 3 thành phần:
        </p>
        <ul className="guide-list">
          <li>
            <strong>Backend – FastAPI (Python) + MySQL</strong>: xử lý toàn bộ nghiệp vụ, xác thực,
            phân quyền và lưu trữ dữ liệu. Phục vụ API tại cổng <code>8000</code>. Tài liệu API tự
            sinh tại <code>/docs</code> (Swagger) và <code>/openapi.json</code>.
          </li>
          <li>
            <strong>Frontend – React + TypeScript + Vite</strong>: giao diện người dùng, đóng gói
            tĩnh (HTML/CSS/JS) nên chạy được trên mọi trình duyệt phổ thông, không cần cài đặt thêm.
          </li>
          <li>
            <strong>CSDL – MySQL</strong>: một database duy nhất (<code>ludoan_db</code>), đặt cùng
            máy chủ hoặc máy chủ CSDL riêng trong LAN.
          </li>
        </ul>
        <p>
          Toàn bộ tệp đính kèm (ảnh, văn bản, công văn) lưu trên ổ đĩa máy chủ tại
          <code> storage/uploads/</code> và phục vụ qua đường dẫn <code>/static</code>.
        </p>
      </Block>

      <Block title="Đóng gói vận hành sản xuất (Production): 1 tiến trình, 1 cổng duy nhất">
        <p>
          Bản build tĩnh của Frontend (<code>npm run build</code> → thư mục <code>frontend/dist</code>)
          được chính Backend FastAPI phục vụ luôn (route dự phòng SPA đăng ký sau cùng, không che bất
          kỳ endpoint API nào) — xem <code>app/main.py</code>. Kết quả: chỉ cần khởi động{' '}
          <strong>một tiến trình duy nhất</strong> (Uvicorn) trên <strong>một cổng duy nhất</strong>{' '}
          (<code>8000</code>) là có đủ cả giao diện lẫn API, thay vì phải chạy song song 2 tiến trình
          (Frontend cổng 5173 + Backend cổng 8000) như môi trường phát triển.
        </p>
        <table className="guide-table">
          <thead>
            <tr>
              <th>Tiêu chí</th>
              <th>Trước (2 tiến trình, dev)</th>
              <th>Sau (1 tiến trình, production)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Số tiến trình phải chạy/giám sát</td>
              <td>2 (Vite dev server + Uvicorn)</td>
              <td>1 (Uvicorn)</td>
            </tr>
            <tr>
              <td>Cổng cần mở trên tường lửa</td>
              <td>2 (<code>8000</code>, <code>5173</code>)</td>
              <td>1 (<code>8000</code>)</td>
            </tr>
            <tr>
              <td>Cấu hình địa chỉ API cho Frontend</td>
              <td>Phải khai <code>VITE_API_BASE_URL</code> đúng IP máy chủ trước khi build</td>
              <td>Không cần — Frontend gọi API bằng đường dẫn tương đối, tự khớp mọi địa chỉ truy cập</td>
            </tr>
            <tr>
              <td>Khởi động</td>
              <td>2 lệnh, 2 cửa sổ dòng lệnh</td>
              <td>1 cú bấm đúp <code>Chay_He_Thong.bat</code></td>
            </tr>
          </tbody>
        </table>
        <p className="guide-note">
          Tài nguyên máy chủ nội bộ (RAM, số handle mạng, số tiến trình Windows theo dõi) được tối ưu
          rõ rệt so với mô hình 2 tiến trình — phù hợp máy chủ cấu hình vừa phải đặt tại đơn vị.
        </p>
      </Block>

      <Block title="Kiến trúc 3 tầng (chuẩn mực, tách bạch trách nhiệm)">
        <table className="guide-table">
          <thead>
            <tr>
              <th>Tầng</th>
              <th>Thư mục</th>
              <th>Trách nhiệm</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Route (API)</td>
              <td><code>app/api/routes/</code></td>
              <td>Khai báo đường dẫn, phương thức, mã trạng thái, kiểm tra quyền (Depends). Không chứa logic nghiệp vụ.</td>
            </tr>
            <tr>
              <td>Service (nghiệp vụ)</td>
              <td><code>app/services/</code></td>
              <td>Quy tắc nghiệp vụ, kiểm tra sở hữu, lọc theo bậc mật, sinh lỗi 403/404/409.</td>
            </tr>
            <tr>
              <td>Repository (dữ liệu)</td>
              <td><code>app/repositories/</code></td>
              <td>Truy vấn CSDL thuần tuý (create / list / get / update / delete).</td>
            </tr>
          </tbody>
        </table>
        <p className="guide-note">
          Quy trình <strong>Contract-First</strong>: mỗi lần thay đổi API, backend xuất lại
          <code> openapi.yaml</code> và ghi biên bản vào <code>openapi.CHANGELOG.md</code>; Frontend
          sinh lại kiểu dữ liệu (<code>types/</code>) và lớp gọi API (<code>api/</code>) từ hợp đồng
          đó — hai phía luôn khớp nhau.
        </p>
      </Block>

      <Block title="Phân quyền RBAC đa cấp">
        <table className="guide-table">
          <thead>
            <tr>
              <th>Vai trò</th>
              <th>Đối tượng</th>
              <th>Quyền chính</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>admin</code></td>
              <td>Quản trị hệ thống (chủ đơn vị giữ)</td>
              <td>Toàn quyền như <code>commander</code> + độc quyền: cấp cờ kênh hạn chế, cấp lại mật khẩu, quản lý đơn vị, tạo admin khác.</td>
            </tr>
            <tr>
              <td><code>commander</code></td>
              <td>Lữ trưởng, Chính uỷ, Phó Lữ trưởng, Phó Chính uỷ</td>
              <td>Ban hành Chỉ thị – Nhiệm vụ, duyệt/đăng mọi nội dung, quản lý tài khoản.</td>
            </tr>
            <tr>
              <td><code>officer</code></td>
              <td>Cán bộ, sĩ quan/QNCN phòng ban, đại đội (mặc định khi tự đăng ký)</td>
              <td>Đăng/biên tập Tin tức – Hoạt động và Giáo dục chính trị; chỉ xem Chỉ thị – Nhiệm vụ.</td>
            </tr>
          </tbody>
        </table>
        <p>
          Chỉ cán bộ và quân nhân chuyên nghiệp (QNCN) có biên chế thực tế mới được cấp tài
          khoản mạng nội bộ — không còn vai trò &quot;Chiến sĩ&quot;. Mọi tài khoản (tự đăng ký
          hoặc chỉ huy tạo trực tiếp) đều phải có đủ <strong>Cấp bậc</strong>,{' '}
          <strong>Chức danh</strong> và <strong>Đơn vị công tác</strong> trước khi kích hoạt được
          (<code>POST /users/{'{id}'}/activate</code> trả về 409 nếu còn thiếu).
        </p>
        <p>
          Xác thực bằng <strong>JWT</strong> (token có hạn {'24 giờ'} — cấu hình
          <code> JWT_EXPIRE_MINUTES</code>). Quyền được <em>bắt buộc thực thi ở tầng Backend</em>;
          giao diện chỉ ẩn/hiện nút cho gọn — không thay cho kiểm soát máy chủ.
        </p>
      </Block>

      <Block title="Bảo mật 3 cấp độ thông tin">
        <table className="guide-table">
          <thead>
            <tr>
              <th>Bậc</th>
              <th>Giá trị</th>
              <th>Ai được xem</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Công khai</td>
              <td><code>cong_khai</code></td>
              <td>Mọi máy trong LAN, không cần đăng nhập (chỉ các mục được mở công khai).</td>
            </tr>
            <tr>
              <td>Nội bộ</td>
              <td><code>noi_bo</code></td>
              <td>Mọi tài khoản đã kích hoạt.</td>
            </tr>
            <tr>
              <td>Mật</td>
              <td><code>mat</code></td>
              <td><code>commander</code>/<code>admin</code> HOẶC tài khoản được cấp cờ <code>clearance = true</code>.</td>
            </tr>
          </tbody>
        </table>
        <p className="guide-note">
          Kênh chuyên Ban Chỉ huy &amp; Cấp uỷ và Sổ công văn mật đều gắn cứng
          bậc <code>mat</code> — không đủ quyền sẽ nhận lỗi 403 ngay tại máy chủ.
        </p>
      </Block>
    </>
  )
}

/* ------------------------------------------------------------------ tab 2 */
function HaTang() {
  return (
    <>
      <Block title="Nguyên tắc: hoạt động offline 100%">
        <p>
          Hệ thống <strong>không phụ thuộc Internet</strong>. Sau khi cài đặt, toàn bộ thư viện,
          phông chữ, mã giao diện và dữ liệu đều nằm trên máy chủ nội bộ. Chỉ cần các máy trạm và
          máy chủ thông nhau trong cùng mạng LAN/WAN quân sự là khai thác được đầy đủ.
        </p>
      </Block>

      <Block title="Cấu hình IP tĩnh cho máy chủ nội bộ">
        <p>
          Máy chủ <strong>bắt buộc dùng IP tĩnh</strong> để các máy trạm luôn tìm thấy. Ví dụ dải
          <code> 192.168.1.0/24</code>:
        </p>
        <ul className="guide-list">
          <li>Địa chỉ IP: <code>192.168.1.10</code></li>
          <li>Mặt nạ mạng: <code>255.255.255.0</code></li>
          <li>Cổng mặc định (gateway): theo thiết bị định tuyến của đơn vị</li>
          <li>DNS: để trống hoặc trỏ DNS nội bộ (không cần cho hệ thống hoạt động)</li>
        </ul>
        <p>Đặt IP tĩnh bằng dòng lệnh (chạy PowerShell/CMD với quyền Administrator):</p>
        <Code>{`netsh interface ip set address name="Ethernet" static 192.168.1.10 255.255.255.0 192.168.1.1`}</Code>
        <p>
          Hoặc: <em>Control Panel → Network and Sharing Center → Change adapter settings → </em>
          chuột phải card mạng → <em>Properties → Internet Protocol Version 4 (TCP/IPv4) → Properties</em>
          → chọn <em>Use the following IP address</em>.
        </p>
        <p className="guide-note">
          CORS của Backend đã mở sẵn cho <code>localhost</code>/<code>127.0.0.1</code> mọi cổng và các
          dải LAN riêng <code>10.x</code>, <code>192.168.x</code>, <code>172.16–31.x</code>. Nếu đơn vị
          dùng dải khác, bổ sung origin vào biến <code>EXTRA_CORS_ORIGINS</code> trong
          <code> backend/.env</code>.
        </p>
      </Block>

      <Block title="Thông tuyến tường lửa (Firewall): mở cổng 8000 và 5173">
        <table className="guide-table">
          <thead>
            <tr>
              <th>Cổng</th>
              <th>Dịch vụ</th>
              <th>Khi nào cần mở</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>8000</code> (TCP)</td>
              <td>API Backend (FastAPI/Uvicorn)</td>
              <td>Luôn cần — mọi máy trạm gọi vào cổng này.</td>
            </tr>
            <tr>
              <td><code>5173</code> (TCP)</td>
              <td>Máy chủ giao diện Vite (chế độ phát triển)</td>
              <td>Khi phục vụ Frontend trực tiếp bằng <code>npm run dev</code>. Nếu đã build tĩnh và đưa lên IIS/Nginx cổng 80 thì không cần.</td>
            </tr>
          </tbody>
        </table>
        <p>Mở cổng trên Windows Firewall (chạy với quyền Administrator):</p>
        <Code>{`netsh advfirewall firewall add rule name="LuDoan21 API 8000" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="LuDoan21 Web 5173" dir=in action=allow protocol=TCP localport=5173`}</Code>
        <p>Kiểm tra từ máy trạm (thay IP máy chủ):</p>
        <Code>{`# Trình duyệt máy trạm:
http://192.168.1.10:8000/docs      -> phải mở được trang Swagger
http://192.168.1.10:5173           -> phải mở được giao diện Cổng thông tin`}</Code>
      </Block>

      <Block title="Địa chỉ máy chủ để Frontend gọi API">
        <p>
          <strong>Chế độ Production (khuyến nghị — 1 cổng duy nhất):</strong> bản build tại
          <code> frontend/.env.production</code> đã đặt sẵn <code>VITE_API_BASE_URL</code> rỗng →
          Frontend gọi API bằng đường dẫn <em>tương đối</em>, luôn trùng gốc (origin) với địa chỉ
          đang mở trên trình duyệt. Không cần sửa gì thêm dù máy trạm truy cập qua
          <code> localhost</code> hay qua bất kỳ IP LAN nào của máy chủ — không phải build lại riêng
          cho từng địa chỉ.
        </p>
        <p>
          <strong>Chế độ phát triển (2 tiến trình, Frontend cổng 5173 riêng):</strong> Frontend đọc
          địa chỉ API từ biến môi trường <code>VITE_API_BASE_URL</code> (tệp <code>frontend/.env</code>).
          Khi cần chạy tách rời, đặt bằng IP tĩnh của máy chủ:
        </p>
        <Code>{`# frontend/.env
VITE_API_BASE_URL=http://192.168.1.10:8000`}</Code>
        <p>Sau khi sửa, khởi động lại <code>npm run dev</code> (chế độ production dùng file <code>.env.production</code> riêng, không bị ảnh hưởng).</p>
      </Block>

      <Block title="Khởi động máy chủ sản xuất 1-Click bằng Chay_He_Thong.bat (khuyến nghị)">
        <p>
          Ở thư mục gốc dự án có sẵn file <code>Chay_He_Thong.bat</code>. Bộ phận kỹ thuật chỉ cần
          <strong> bấm đúp chuột</strong> vào file này để khởi động toàn bộ hệ thống — không cần gõ
          lệnh, không cần nhớ đường dẫn <code>venv</code>.
        </p>
        <p>File này tự động thực hiện tuần tự:</p>
        <ol className="guide-list guide-ol">
          <li>Chuyển vào thư mục <code>backend/</code> và kiểm tra đã có môi trường ảo <code>venv</code> và file <code>.env</code> chưa (báo lỗi rõ ràng và dừng lại nếu thiếu, thay vì treo im lặng).</li>
          <li>Kích hoạt <code>venv</code> (tự động, không cần thao tác tay).</li>
          <li>Kiểm tra đã build giao diện (<code>frontend/dist</code>) chưa — nếu chưa, cảnh báo nhưng vẫn cho chạy ở chế độ API-only.</li>
          <li>Khởi động máy chủ Production: <code>uvicorn app.main:app --host 0.0.0.0 --port 8000</code> — <strong>không bật cờ <code>--reload</code></strong> của môi trường phát triển (tắt tự khởi động lại khi sửa file, tránh gián đoạn dịch vụ đang có người dùng).</li>
        </ol>
        <p>
          Sau khi cửa sổ hiện dòng <code>Uvicorn running on http://0.0.0.0:8000</code>, hệ thống đã
          sẵn sàng phục vụ. Truy cập <code>http://localhost:8000</code> tại máy chủ, hoặc
          <code> http://&lt;IP máy chủ&gt;:8000</code> từ bất kỳ máy trạm nào trong LAN.
        </p>
        <p className="guide-note">
          <strong>Dừng hệ thống:</strong> đóng cửa sổ dòng lệnh đó (hoặc bấm tổ hợp <code>Ctrl+C</code>
          bên trong cửa sổ). Muốn hệ thống tự khởi động lại cùng máy chủ (vd sau khi cúp điện, máy tự
          bật lại): đặt lối tắt tới <code>Chay_He_Thong.bat</code> vào thư mục Startup của Windows
          (<code>shell:startup</code>) hoặc tạo Scheduled Task chạy lúc đăng nhập.
        </p>
      </Block>

      <Block title="Sao lưu & phục hồi dữ liệu định kỳ (dành cho bộ phận kỹ thuật)">
        <p>
          Script <code>backend/scripts/backup_db.py</code> sao lưu toàn bộ CSDL MySQL
          (<code>ludoan_db</code>) ra file <strong>nén gzip</strong> (<code>.sql.gz</code>), đặt tại
          <code> backend/storage/backups/</code>. Thông tin kết nối CSDL đọc từ <code>backend/.env</code>{' '}
          — không hỏi/hiện mật khẩu trên màn hình hay dòng lệnh.
        </p>
        <p><strong>Sao lưu thủ công (chạy khi cần):</strong></p>
        <Code>{`cd backend
venv\\Scripts\\activate
python scripts\\backup_db.py`}</Code>
        <p>
          Mỗi lần chạy tạo 1 file mới dạng <code>ludoan_db_20260830_231800.sql.gz</code> (theo thời
          điểm sao lưu) và <strong>tự động xoá bớt bản cũ</strong>, chỉ giữ lại 14 bản gần nhất (đổi
          số lượng giữ lại bằng <code>--retention</code>, ví dụ <code>--retention 30</code>).
        </p>
        <p><strong>Đặt lịch sao lưu tự động hằng ngày (khuyến nghị — Windows Task Scheduler):</strong></p>
        <ol className="guide-list guide-ol">
          <li>Mở <em>Task Scheduler</em> → <em>Create Basic Task</em>.</li>
          <li>Đặt tên: <em>Sao luu CSDL Cong thong tin Lu doan 21</em>; chọn chạy <strong>Daily</strong>, giờ thấp điểm (vd 23:00).</li>
          <li>
            Action: <em>Start a program</em> — Program/script trỏ tới
            <code> &lt;đường dẫn dự án&gt;\backend\venv\Scripts\python.exe</code>, Add arguments:
            <code> scripts\backup_db.py</code>, Start in: <code>&lt;đường dẫn dự án&gt;\backend</code>.
          </li>
          <li>Chạy thử ngay (chuột phải task vừa tạo → <em>Run</em>) và kiểm tra có file mới trong <code>backend/storage/backups/</code>.</li>
        </ol>
        <p><strong>Phục hồi dữ liệu từ bản sao lưu (thận trọng — ghi đè dữ liệu hiện tại):</strong></p>
        <Code>{`cd backend
venv\\Scripts\\activate
python scripts\\backup_db.py --restore storage\\backups\\ludoan_db_20260830_231800.sql.gz
# Script se hoi xac nhan go "YES" truoc khi ghi de - danh thoi gian doc ky ten file truoc khi go`}</Code>
        <p className="guide-note">
          Khuyến nghị: định kỳ copy thư mục <code>backend/storage/backups/</code> (và
          <code> backend/storage/uploads/</code> — nơi lưu file đính kèm/công văn) sang một ổ đĩa hoặc
          máy khác ngoài máy chủ chính, để vẫn còn dữ liệu nếu máy chủ hỏng hoàn toàn (cháy nổ, hỏng ổ
          cứng...) — sao lưu tại chỗ không thay thế được sao lưu ngoài máy chủ.
        </p>
      </Block>
    </>
  )
}

/* ------------------------------------------------------------------ tab 3 */
function MayTram() {
  return (
    <>
      <Block title="Yêu cầu máy trạm">
        <ul className="guide-list">
          <li>Trình duyệt: <strong>Google Chrome</strong>, <strong>Cốc Cốc</strong>, <strong>Microsoft Edge</strong> (bản trong 2–3 năm gần đây).</li>
          <li>Cùng mạng LAN với máy chủ; ping thông tới IP máy chủ.</li>
          <li>Không cần cài đặt phần mềm gì thêm trên máy trạm.</li>
        </ul>
      </Block>

      <Block title="Truy cập và đăng nhập">
        <ol className="guide-list guide-ol">
          <li>Mở trình duyệt, gõ địa chỉ Cổng thông tin, ví dụ <code>http://192.168.1.10:5173</code> (hoặc cổng 80 nếu đã dựng web tĩnh).</li>
          <li>Trang công khai hiển thị Tin tức, Thông báo, Văn bản ở mức <em>Công khai</em> — xem được ngay không cần đăng nhập.</li>
          <li>Bấm <strong>Đăng nhập</strong>, nhập tên đăng nhập và mật khẩu do quản trị cấp.</li>
          <li>Lần đầu đăng nhập (hoặc sau khi được cấp lại mật khẩu): hệ thống <strong>bắt buộc đổi mật khẩu</strong> trước khi vào các màn hình nội bộ.</li>
          <li>Tài khoản tự đăng ký (<code>POST /users/register</code>) ở trạng thái chờ — chỉ đăng nhập được sau khi chỉ huy <strong>kích hoạt</strong>.</li>
        </ol>
        <p className="guide-note">
          Tài khoản quản trị khởi tạo sẵn: <code>admin</code> / <code>admin</code> (đổi trong
          <code> backend/.env</code>: <code>SYSTEM_ADMIN_USERNAME</code>, <code>SYSTEM_ADMIN_PASSWORD</code>).
          Bắt buộc đổi mật khẩu ngay lần đăng nhập đầu.
        </p>
      </Block>

      <Block title="Tự động lưu bản nháp & an toàn dữ liệu khi mất điện / mất mạng">
        <p>
          Các form soạn thảo nội dung dài — <strong>ban hành Chỉ thị</strong>, trao đổi/báo cáo trong{' '}
          <strong>Kênh Chỉ đạo – Báo cáo</strong>, <strong>Giao nhiệm vụ</strong> (tạo nhiệm vụ + nộp
          báo cáo tiến độ) và <strong>Kênh chuyên BCH &amp; Cấp uỷ</strong> — đều{' '}
          <strong>tự động lưu bản nháp</strong> ngay trên trình duyệt
          của máy trạm trong lúc đang gõ (không cần bấm nút lưu riêng).
        </p>
        <ul className="guide-list">
          <li>Nội dung đang soạn được lưu tạm sau mỗi lần ngừng gõ khoảng dưới 1 giây.</li>
          <li>
            <strong>Lỡ tải lại trang, mất điện đột ngột hoặc rớt mạng LAN</strong> trước khi kịp bấm
            "Gửi"/"Ban hành"/"Lưu biên bản": mở lại đúng luồng/mục đó, nội dung đang soạn sẽ{' '}
            <strong>tự khôi phục lại</strong> vào đúng ô soạn thảo.
          </li>
          <li>Sau khi gửi/lưu <strong>thành công</strong>, bản nháp tạm được xoá — không bị bung lại nội dung cũ ở lần soạn sau.</li>
          <li>
            Bản nháp chỉ lưu <strong>trên trình duyệt của máy trạm đang gõ</strong> (không đồng bộ lên
            máy chủ, không chia sẻ giữa các máy) — đây là lưới an toàn tạm thời, <strong>không thay
            thế</strong> việc bấm gửi/lưu khi soạn xong.
          </li>
        </ul>
        <p className="guide-note">
          Nếu đổi sang máy trạm khác hoặc xoá dữ liệu duyệt web (Clear browsing data) của trình duyệt,
          bản nháp tạm trên máy cũ sẽ mất — hãy hoàn tất và gửi nội dung quan trọng trước khi rời máy.
        </p>
      </Block>

      <Block title="Khai thác phân hệ theo quyền hạn">
        <table className="guide-table">
          <thead>
            <tr>
              <th>Phân hệ</th>
              <th>Xem</th>
              <th>Đăng / Sửa</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Bảng tin (trang chủ tổng hợp)</td><td>Mọi tài khoản đã đăng nhập</td><td>—</td></tr>
            <tr><td>Tin tức – Hoạt động đơn vị</td><td>Công khai (bài đã duyệt)</td><td><code>officer</code>, <code>commander</code> (duyệt: chỉ <code>commander</code>)</td></tr>
            <tr><td>Thông báo – Lịch trực kíp</td><td>Công khai khi được đánh dấu công khai</td><td><code>officer</code>, <code>commander</code></td></tr>
            <tr><td>Văn bản – Tài liệu – Biểu mẫu</td><td>Công khai khi được đánh dấu công khai</td><td><code>officer</code>, <code>commander</code></td></tr>
            <tr><td>Giáo dục chính trị</td><td>Mọi tài khoản đã đăng nhập</td><td><code>officer</code>, <code>commander</code></td></tr>
            <tr><td>Chỉ thị – Nhiệm vụ</td><td>Mọi tài khoản (bản đã ban hành)</td><td>Chỉ <code>commander</code></td></tr>
            <tr><td>Kênh Chỉ đạo – Báo cáo / Giao nhiệm vụ</td><td>Tài khoản có cờ kênh chỉ đạo (+ <code>commander</code>/<code>admin</code>)</td><td>Giao/duyệt: <code>commander</code>/<code>admin</code>; nộp báo cáo: đơn vị được giao</td></tr>
            <tr><td>Kênh chỉ huy (MẬT)</td><td>Có <code>clearance</code> hoặc <code>commander</code>/<code>admin</code></td><td>Vào sổ/đóng luồng: <code>commander</code>/<code>admin</code></td></tr>
            <tr><td>Quản lý người dùng</td><td><code>commander</code>/<code>admin</code></td><td><code>commander</code>/<code>admin</code></td></tr>
            <tr><td>Quản lý đơn vị</td><td><code>admin</code></td><td><code>admin</code></td></tr>
            <tr><td>Hồ sơ cá nhân</td><td>Chủ tài khoản</td><td>Chủ tài khoản (đổi họ tên, đổi mật khẩu)</td></tr>
          </tbody>
        </table>
        <p className="guide-note">
          Thanh menu ngang tự ẩn những mục vượt quyền — người dùng chỉ nhìn thấy phần việc của mình.
        </p>
      </Block>

      <Block title="Quy trình quản trị tài khoản (dành cho chỉ huy / quản trị)">
        <ul className="guide-list">
          <li>Xem danh sách chờ duyệt: <em>Quản lý người dùng</em> → lọc tài khoản chưa kích hoạt.</li>
          <li>Bổ sung Cấp bậc, Chức danh và Đơn vị công tác cho tài khoản chờ duyệt (bắt buộc).</li>
          <li>Kích hoạt / khoá tài khoản; đổi vai trò (officer → commander).</li>
          <li>Cấp/thu quyền xem <strong>MẬT</strong> (<code>clearance</code>); cấp cờ vào <strong>Kênh Chỉ đạo – Báo cáo</strong>.</li>
          <li>Gán <strong>đơn vị</strong> cho tài khoản để phục vụ giao nhiệm vụ / nhận báo cáo theo đầu mối.</li>
          <li>Cấp lại mật khẩu (tài khoản đó sẽ bị buộc đổi ở lần đăng nhập kế tiếp).</li>
          <li>Ràng buộc an toàn: không tự hạ quyền/khoá chính mình; luôn giữ ≥ 1 <code>commander</code> đang hoạt động.</li>
        </ul>
      </Block>
    </>
  )
}

/* ------------------------------------------------------------------ tab 4 */
function SuCo() {
  return (
    <>
      <Block title="4.1 — Mất kết nối MySQL (sai mật khẩu / chưa bật dịch vụ)">
        <p><strong>Triệu chứng:</strong> Backend không khởi động, log báo <code>Can't connect to MySQL server</code>, <code>Access denied for user</code>, hoặc <code>Unknown database</code>.</p>
        <p><strong>Xử lý:</strong></p>
        <ol className="guide-list guide-ol">
          <li>Kiểm tra dịch vụ MySQL đã chạy chưa: <Code>{`net start | findstr /I mysql
# nếu chưa chạy:
net start MySQL        # (hoặc MySQL80 tùy tên dịch vụ)`}</Code></li>
          <li>Đối chiếu thông tin trong <code>backend/.env</code>: <code>MYSQL_HOST</code>, <code>MYSQL_PORT</code>, <code>MYSQL_USER</code>, <code>MYSQL_PASSWORD</code>, <code>MYSQL_DB</code>.</li>
          <li>Kiểm tra chuỗi <code>DATABASE_URL</code>: ký tự đặc biệt trong mật khẩu phải mã hoá URL (ví dụ <code>@</code> → <code>%40</code>).</li>
          <li>Thử đăng nhập tay để cô lập lỗi tài khoản CSDL: <Code>{`mysql -u quynh_user -p -h localhost ludoan_db`}</Code></li>
          <li>Nếu chưa có database/bảng: tạo database rồi để Backend tự tạo bảng khi khởi động; chạy các script migration trong <code>backend/scripts/</code> theo đúng thứ tự nếu nâng cấp từ bản cũ.</li>
        </ol>
      </Block>

      <Block title="4.2 — Xung đột cổng (port in use)">
        <p><strong>Triệu chứng:</strong> <code>[Errno 10048]</code> / <code>address already in use</code> khi chạy Backend (8000) hoặc Frontend (5173).</p>
        <p><strong>Xử lý:</strong></p>
        <Code>{`# Tìm tiến trình đang giữ cổng 8000:
netstat -ano | findstr :8000
# Cột cuối là PID, kết thúc tiến trình đó:
taskkill /PID <PID> /F`}</Code>
        <p>Hoặc đổi cổng khi chạy: <code>uvicorn app.main:app --host 0.0.0.0 --port 8080</code> (nhớ cập nhật <code>VITE_API_BASE_URL</code> và mở cổng mới trên tường lửa).</p>
      </Block>

      <Block title="4.3 — Token hết hạn (lỗi 401)">
        <p><strong>Triệu chứng:</strong> Đang thao tác thì bị đẩy về trang đăng nhập; API trả <code>401 Unauthorized</code> / <code>Could not validate credentials</code>.</p>
        <p><strong>Nguyên nhân:</strong> JWT có hạn (mặc định <code>JWT_EXPIRE_MINUTES=1440</code> — 24 giờ), hoặc đồng hồ máy chủ sai lệch, hoặc <code>JWT_SECRET_KEY</code> bị đổi khiến token cũ vô hiệu.</p>
        <p><strong>Xử lý:</strong> Đăng nhập lại để lấy token mới. Nếu muốn phiên dài hơn, tăng <code>JWT_EXPIRE_MINUTES</code> trong <code>backend/.env</code> rồi khởi động lại Backend. Đồng bộ giờ máy chủ (<code>w32tm /resync</code> hoặc theo giờ chuẩn đơn vị).</p>
      </Block>

      <Block title="4.4 — Phân quyền không khớp (lỗi 403)">
        <p><strong>Triệu chứng:</strong> API trả <code>403 Forbidden</code>; nút thao tác không hiện hoặc bấm vào báo không đủ quyền.</p>
        <p><strong>Kiểm tra theo thứ tự:</strong></p>
        <ul className="guide-list">
          <li>Vai trò tài khoản có đúng không (officer/commander/admin)? Sửa tại <em>Quản lý người dùng → đổi vai trò</em>.</li>
          <li>Nội dung/kênh ở bậc <strong>MẬT</strong>? Tài khoản cần cờ <code>clearance = true</code> hoặc là <code>commander</code>/<code>admin</code>.</li>
          <li>Kênh Chỉ đạo – Báo cáo: tài khoản cần cờ <code>directive_channel_access</code>.</li>
          <li>Sửa/xoá nội dung của người khác: chỉ tác giả hoặc <code>commander</code> mới được phép.</li>
          <li>Sau khi đổi quyền, tài khoản phải <strong>đăng xuất và đăng nhập lại</strong> để token mang quyền mới.</li>
        </ul>
      </Block>

      <Block title="4.5 — Lỗi tải file dung lượng lớn">
        <p><strong>Triệu chứng:</strong> Upload ảnh/văn bản/công văn thất bại, báo <code>413</code> hoặc <code>File quá lớn</code>.</p>
        <p><strong>Xử lý:</strong></p>
        <ul className="guide-list">
          <li>Giới hạn mặc định <code>MAX_UPLOAD_MB=50</code> (trong <code>backend/.env</code>). Tăng giá trị này rồi khởi động lại Backend nếu cần.</li>
          <li>Kiểm tra định dạng cho phép: tài liệu <code>.pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx</code>; ảnh bìa tin tức là tệp ảnh.</li>
          <li>Nếu đặt sau reverse proxy (Nginx/IIS): nới giới hạn thân yêu cầu (<code>client_max_body_size</code> của Nginx, hoặc <code>maxAllowedContentLength</code> của IIS).</li>
          <li>Kiểm tra dung lượng trống của ổ đĩa chứa <code>storage/uploads/</code>.</li>
          <li>Giải pháp nhanh: nén tệp hoặc tách nhỏ trước khi tải lên.</li>
        </ul>
      </Block>

      <Block title="4.6 — Máy trạm không mở được Cổng thông tin">
        <ul className="guide-list">
          <li>Ping thử IP máy chủ; nếu không thông là vấn đề mạng/định tuyến, không phải phần mềm.</li>
          <li>Mở <code>http://&lt;IP máy chủ&gt;:8000/docs</code> từ máy trạm — nếu lỗi thì Backend chưa chạy hoặc tường lửa chặn cổng 8000.</li>
          <li>Giao diện mở được nhưng đăng nhập/không tải dữ liệu: kiểm tra <code>VITE_API_BASE_URL</code> có trỏ đúng IP máy chủ (không phải <code>localhost</code>) — chỉ áp dụng khi còn chạy Frontend tách rời ở cổng 5173; chế độ 1 cổng production không cần kiểm tra mục này.</li>
          <li>Lỗi CORS trong Console trình duyệt: thêm origin của máy trạm vào <code>EXTRA_CORS_ORIGINS</code>.</li>
        </ul>
      </Block>

      <Block title="4.7 — Mất điện / mất mạng LAN đột ngột giữa buổi làm việc">
        <p><strong>Nguy cơ:</strong> đang soạn Chỉ thị, báo cáo, nội dung trao đổi trong kênh... thì mất điện hoặc rớt mạng trước khi kịp gửi/lưu.</p>
        <p><strong>Đã được bảo vệ sẵn:</strong></p>
        <ul className="guide-list">
          <li>
            Nội dung đang gõ ở các form Chỉ thị, Kênh Chỉ đạo – Báo cáo, Giao nhiệm vụ, Kênh chuyên BCH
            &amp; Cấp uỷ đã được <strong>tự động lưu bản nháp</strong> trên trình
            duyệt máy trạm (xem tab 3 — mục "Tự động lưu bản nháp"). Bật lại máy/mạng, mở lại đúng
            trang đó, nội dung sẽ tự khôi phục.
          </li>
          <li>
            Dữ liệu <strong>đã gửi/lưu thành công</strong> trước đó không mất — CSDL MySQL ghi ngay khi
            máy chủ nhận được yêu cầu, không phụ thuộc trạng thái máy trạm.
          </li>
        </ul>
        <p><strong>Về phía máy chủ:</strong></p>
        <ul className="guide-list">
          <li>
            Nếu máy chủ mất điện đột ngột: kiểm tra dịch vụ MySQL đã tự khởi động lại cùng Windows
            chưa (<Code>{`net start | findstr /I mysql`}</Code>); nếu chưa, khởi động tay rồi chạy lại{' '}
            <code>Chay_He_Thong.bat</code>.
          </li>
          <li>
            Nếu nghi ngờ dữ liệu bị hỏng do tắt đột ngột giữa lúc ghi: phục hồi từ bản sao lưu gần nhất
            trong <code>backend/storage/backups/</code> (xem tab 2 — mục "Sao lưu &amp; phục hồi dữ
            liệu định kỳ"). Đây là lý do cần đặt lịch sao lưu tự động hằng ngày thay vì chỉ sao lưu khi
            nhớ ra.
          </li>
          <li>
            Máy chủ nội bộ đơn vị nên trang bị UPS (bộ lưu điện) tối thiểu đủ thời gian tắt máy an toàn
            khi mất điện lưới — giảm nguy cơ hỏng CSDL do ngắt điện đột ngột giữa lúc đang ghi.
          </li>
        </ul>
      </Block>

      <Block title="Lệnh khởi động nhanh (bộ phận kỹ thuật)">
        <p>
          <strong>Khuyến nghị:</strong> bấm đúp <code>Chay_He_Thong.bat</code> ở thư mục gốc dự án —
          xem chi tiết ở tab 2, mục "Khởi động máy chủ sản xuất 1-Click". Các lệnh dưới đây dành cho
          trường hợp cần chạy tay/gỡ lỗi.
        </p>
        <Code>{`# 1) Backend
cd backend
venv\\Scripts\\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2) Frontend (chế độ phát triển)
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173

# 3) Frontend (bản phát hành tĩnh)
npm run build      # kết quả trong frontend/dist -> đưa lên web server nội bộ`}</Code>
      </Block>
    </>
  )
}
