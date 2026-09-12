import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { Icon } from '../components/Icon'
import { PasswordInput } from '../components/PasswordInput'
import { UNIT } from '../config/unit'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLocked, setIsLocked] = useState(false)

  if (isAuthenticated) {
    const redirectTo = (location.state as { from?: string } | null)?.from ?? '/bang-tin'
    return <Navigate to={redirectTo} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsLocked(false)
    try {
      // Cắt khoảng trắng thừa (bàn phím cảm ứng / tự động điền hay thêm dấu cách
      // hoặc viết hoa chữ đầu) — username so khớp phân biệt HOA/thường ở backend.
      await login({ username: username.trim(), password: password.trim() })
      const to = (location.state as { from?: string } | null)?.from ?? '/bang-tin'
      navigate(to, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        if (err.status === 429) {
          setIsLocked(true)
        }
      } else {
        setError('Đăng nhập thất bại')
      }
    }
  }

  return (
    <div className="login-screen">
      <section className="login-card">
        <div className="login-brand">
          <span className="login-emblem" aria-hidden="true">
            <Icon name="star" size={44} />
          </span>
          <h1>{UNIT.fullName}</h1>
          <p>{UNIT.slogan}</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label>
            Tên đăng nhập
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
            />
          </label>
          <label>
            Mật khẩu
            <PasswordInput
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          {error ? (
            <div
              role="alert"
              className="form-error"
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                padding: isLocked ? '12px' : undefined,
                backgroundColor: isLocked ? '#fef2f2' : undefined,
                border: isLocked ? '1px solid #f87171' : undefined,
                borderRadius: isLocked ? '6px' : undefined,
                color: isLocked ? '#991b1b' : undefined,
                textAlign: 'left',
              }}
            >
              {isLocked ? (
                <span style={{ flexShrink: 0, marginTop: '2px', display: 'inline-flex' }}>
                  <Icon name="lock" size={20} />
                </span>
              ) : null}
              <span>{error}</span>
            </div>
          ) : null}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>

        <p className="login-note">
          Chưa có tài khoản?{' '}
          <Link to="/register" className="login-note__register">
            <strong>Đăng ký</strong>
          </Link>{' '}
          — tài khoản sẽ dùng được sau khi chỉ huy đơn vị duyệt.
        </p>
      </section>
    </div>
  )
}
