import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { CONTACT, NAV, UNIT } from '../config/unit'
import { Icon } from './Icon'

const ROLE_LABELS: Record<string, string> = {
  commander: 'Chỉ huy',
  officer: 'Cán bộ',
  soldier: 'Chiến sĩ',
}

export function PortalLayout() {
  const {
    username,
    role,
    isCommander,
    isAdmin,
    canDirectiveChannel,
    canCommandChannel,
    hasClearance,
    logout,
  } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const menu = NAV.filter((entry) => {
    if (entry.commanderOnly && !isCommander) return false
    if (entry.adminOnly && !isAdmin) return false
    if (entry.directiveChannel && !canDirectiveChannel) return false
    if (entry.commandChannel && !canCommandChannel) return false
    return true
  })

  return (
    <div className="portal">
      <div className="main-header">
        <div className="container header-content">
          <div className="unit-brand">
            <span className="unit-logo" aria-hidden="true">
              <Icon name="star" size={40} />
            </span>
            <div className="unit-titles">
              <h1>{UNIT.shortName}</h1>
              <p className="unit-full">{UNIT.fullName}</p>
              <p className="unit-slogan">{UNIT.slogan}</p>
            </div>
          </div>
          <div className="header-user">
            <span className="header-user-name">
              <Icon name="user" size={14} /> {username ?? 'Người dùng'}
              {role ? <em> · {ROLE_LABELS[role] ?? role}</em> : null}
              {hasClearance && !isCommander ? (
                <span className="clearance-chip">
                  <Icon name="lock" size={11} /> Quyền xem MẬT
                </span>
              ) : null}
            </span>
            <button type="button" className="btn-logout" onClick={handleLogout}>
              <Icon name="logout" size={14} /> Đăng xuất
            </button>
          </div>
        </div>
      </div>

      <nav className="main-nav">
        <div className="container">
          <ul className="nav-list">
            {menu.map((entry) => (
              <li key={entry.to} className="nav-item">
                <NavLink to={entry.to} end={entry.to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
                  {entry.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      <main className="container portal-main">
        <Outlet />
      </main>

      <footer className="main-footer">
        <div className="container footer-grid">
          <div className="footer-col">
            <h4>{UNIT.shortName}</h4>
            <p>{UNIT.fullName}</p>
            <p>© Bản quyền nội bộ thuộc {UNIT.copyrightOwner}.</p>
            <p>Nghiêm cấm sao chép, trích dẫn tài liệu mật khi chưa được Chỉ huy đơn vị phê duyệt.</p>
          </div>
          <div className="footer-col">
            <h4>Thông tin liên hệ</h4>
            <p>Địa chỉ: {CONTACT.address}</p>
            <p>Điện thoại nội bộ: {CONTACT.internalPhone}</p>
            <p>Email: {CONTACT.email}</p>
          </div>
          <div className="footer-col">
            <h4>Truy cập nhanh</h4>
            <p>
              <NavLink to="/tin-tuc">Tin tức – Hoạt động đơn vị</NavLink>
            </p>
            <p>
              <NavLink to="/giao-duc-chinh-tri">Giáo dục chính trị</NavLink>
            </p>
            <p>
              <NavLink to="/chi-thi-nhiem-vu">Chỉ thị – Nhiệm vụ</NavLink>
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
