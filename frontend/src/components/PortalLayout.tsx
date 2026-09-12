import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { CONTACT, NAV, UNIT } from '../config/unit'
import type { NavEntry } from '../config/unit'
import { Icon } from './Icon'
import { roleLabel } from '../types/user'
import { chatsApi } from '../api/chats'

export function PortalLayout() {
  const {
    role,
    isAuthenticated,
    isCommander,
    isAdmin,
    canDirectiveChannel,
    canCommandChannel,
    logout,
  } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  // Dieu khien mo/dong bang CLICK (khong chi dua vao :hover cua CSS) de dung
  // duoc tren man hinh cam ung va khi bam chuot.
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [openGroup, setOpenGroup] = useState<string | null>(null)
  const [unreadChatCount, setUnreadChatCount] = useState<number>(0)
  const navRef = useRef<HTMLElement>(null)

  // Polling tong tin nhan chua doc moi 8s
  useEffect(() => {
    if (!isAuthenticated) return
    let active = true
    const fetchUnread = async () => {
      try {
        const res = await chatsApi.getUnreadCount()
        if (active) setUnreadChatCount(res.total_unread)
      } catch {
        // im lang neu loi mang tam thoi
      }
    }
    fetchUnread()
    const timer = setInterval(fetchUnread, 8000)
    return () => {
      active = false
      clearInterval(timer)
    }
  }, [isAuthenticated, pathname])

  // Doi trang -> dong het menu.
  useEffect(() => {
    setUserMenuOpen(false)
    setOpenGroup(null)
  }, [pathname])

  // Bam ra ngoai thanh dieu huong -> dong het menu.
  useEffect(() => {
    function onPointerDown(e: PointerEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false)
        setOpenGroup(null)
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [])

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  function canSee(entry: NavEntry) {
    if (entry.commanderOnly && !isCommander) return false
    if (entry.adminOnly && !isAdmin) return false
    if (entry.directiveChannel && !canDirectiveChannel) return false
    if (entry.commandChannel && !canCommandChannel) return false
    return true
  }

  const menu = NAV.filter(canSee)
    .map((entry) => (entry.children ? { ...entry, children: entry.children.filter(canSee) } : entry))
    .filter((entry) => !entry.children || entry.children.length > 0)

  return (
    <div className="portal">
      <div className="main-header">
        <div className="container header-content">
          <Link to="/bang-tin" className="unit-brand" aria-label="Về Bảng tin">
            <span className="unit-logo" aria-hidden="true">
              <img src="/logo-bdbp.png" alt="" onError={(e) => (e.currentTarget.style.display = 'none')} />
              <Icon name="star" size={40} className="unit-logo-fallback" />
            </span>
            <div className="unit-titles">
              <p className="unit-kicker">{UNIT.shortName}</p>
              <h1>{UNIT.fullName}</h1>
              <p className="unit-slogan">{UNIT.slogan}</p>
            </div>
          </Link>
       
        </div>
      </div>

      <nav className="main-nav" ref={navRef}>
        <Link to="/bang-tin" className="nav-home" aria-label="Về Bảng tin">
          <Icon name="home" size={18} />
        </Link>
        <div className="container nav-bar-inner">
          <ul className="nav-list">
            {menu.map((entry) => {
              if (entry.children) {
                const groupActive = entry.children.some((child) => child.to && pathname.startsWith(child.to))
                const isOpen = openGroup === entry.label
                return (
                  <li
                    key={entry.label}
                    className={isOpen ? 'nav-item has-children open' : 'nav-item has-children'}
                  >
                    <button
                      type="button"
                      className={groupActive || isOpen ? 'nav-parent active' : 'nav-parent'}
                      aria-expanded={isOpen}
                      onClick={() => setOpenGroup((cur) => (cur === entry.label ? null : entry.label))}
                    >
                      {entry.label} <span aria-hidden="true">▾</span>
                    </button>
                    <ul className="nav-dropdown">
                      {entry.children.map((child) => (
                        <li key={child.to} className="nav-item">
                          <NavLink to={child.to!} className={({ isActive }) => (isActive ? 'active' : '')}>
                            {child.label}
                          </NavLink>
                        </li>
                      ))}
                    </ul>
                  </li>
                )
              }
              return (
                <li key={entry.to} className="nav-item">
                  <NavLink to={entry.to!} end={entry.to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
                    {entry.label}
                  </NavLink>
                </li>
              )
            })}
          </ul>

          <div className="header-user">
            <NavLink
              to="/tin-nhan"
              className={({ isActive }) => (isActive ? 'header-chat-btn active' : 'header-chat-btn')}
              title="Tin nhắn tác chiến nội bộ"
            >
              <Icon name="message-square" size={15} />
              <span className="header-chat-text">Tin nhắn</span>
              {unreadChatCount > 0 ? (
                <span className="header-chat-badge">{unreadChatCount > 99 ? '99+' : unreadChatCount}</span>
              ) : null}
            </NavLink>

            <div className={userMenuOpen ? 'user-menu open' : 'user-menu'}>
              <button
                type="button"
                className="user-menu-trigger"
                aria-expanded={userMenuOpen}
                onClick={() => setUserMenuOpen((v) => !v)}
              >
                <span className="user-avatar" aria-hidden="true">
                  <Icon name="user" size={13} />
                </span>
                {/* {username ?? 'Người dùng'} */}
                {role !== null ? <em>  {roleLabel(role)}</em> : null}
                <span aria-hidden="true" className="user-menu-caret">
                  ▾
                </span>
              </button>
              <ul className="user-menu-dropdown">
                {isCommander || isAdmin ? (
                  <li>
                    <NavLink to="/quan-ly-nguoi-dung">
                      <Icon name="user" size={14} /> Tạo tài khoản trực tiếp
                    </NavLink>
                  </li>
                ) : null}
                <li>
                  <NavLink to="/ho-so">
                    <Icon name="user" size={14} /> Hồ sơ cá nhân
                  </NavLink>
                </li>
                <li>
                  <button type="button" onClick={handleLogout}>
                    <Icon name="logout" size={14} /> Đăng xuất
                  </button>
                </li>
              </ul>
            </div>
            {/* {hasClearance && !isCommander ? (
              <span className="clearance-chip">
                <Icon name="lock" size={11} /> Quyền xem MẬT
              </span>
            ) : null} */}
          </div>
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
