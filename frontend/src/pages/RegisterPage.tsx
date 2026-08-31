import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { usersApi } from '../api/users'
import { Icon } from '../components/Icon'
import { UNIT } from '../config/unit'
import { useAuth } from '../context/AuthContext'

export function RegisterPage() {
  const { isAuthenticated } = useAuth()

  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated) return <Navigate to="/bang-tin" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (password !== confirm) {
      setError('Mật khẩu nhập lại không khớp')
      return
    }
    setSubmitting(true)
    try {
      await usersApi.register({ username, password, full_name: fullName })
      setDone(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Đăng ký không thành công')
    } finally {
      setSubmitting(false)
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
          <p>Đăng ký tài khoản truy cập cổng thông tin nội bộ</p>
        </div>

        {done ? (
          <div className="register-done">
            <Icon name="check" size={40} />
            <p>
              Đã gửi yêu cầu đăng ký. Tài khoản sẽ được sử dụng sau khi <strong>chỉ huy đơn vị duyệt</strong>.
            </p>
            <Link to="/login" className="btn-solid">
              Về trang đăng nhập
            </Link>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit}>
              <label>
                Họ và tên
                <input
                  type="text"
                  maxLength={100}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  autoFocus
                />
              </label>
              <label>
                Tên đăng nhập
                <input
                  type="text"
                  minLength={3}
                  maxLength={50}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                />
              </label>
              <label>
                Mật khẩu (tối thiểu 6 ký tự)
                <input
                  type="password"
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </label>
              <label>
                Nhập lại mật khẩu
                <input
                  type="password"
                  minLength={6}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </label>
              {error ? (
                <p role="alert" className="form-error">
                  {error}
                </p>
              ) : null}
              <button type="submit" disabled={submitting}>
                {submitting ? 'Đang gửi...' : 'Gửi yêu cầu đăng ký'}
              </button>
            </form>
            <p className="login-note">
              Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
            </p>
          </>
        )}
      </section>
    </div>
  )
}
