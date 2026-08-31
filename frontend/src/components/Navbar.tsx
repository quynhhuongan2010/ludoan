import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Navbar() {
  const { isAuthenticated, username, isCommander, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  if (!isAuthenticated) return null

  return (
    <nav className="navbar">
      <div className="navbar-links">
        <NavLink to="/posts" className={({ isActive }) => (isActive ? 'active' : '')}>
          Tin tức
        </NavLink>
        <NavLink to="/education" className={({ isActive }) => (isActive ? 'active' : '')}>
          Giáo dục chính trị
        </NavLink>
        <NavLink to="/items" className={({ isActive }) => (isActive ? 'active' : '')}>
          Items
        </NavLink>
        {isCommander ? (
          <NavLink to="/users" className={({ isActive }) => (isActive ? 'active' : '')}>
            Users
          </NavLink>
        ) : null}
      </div>
      <div className="navbar-user">
        {username ? <span>Xin chào, {username}</span> : null}
        <button type="button" onClick={handleLogout}>
          Đăng xuất
        </button>
      </div>
    </nav>
  )
}
