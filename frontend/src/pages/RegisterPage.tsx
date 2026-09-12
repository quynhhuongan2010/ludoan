import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { usersApi } from '../api/users'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { PasswordInput } from '../components/PasswordInput'
import { UNIT } from '../config/unit'
import { useAuth } from '../context/AuthContext'
import { useRequiredFields } from '../hooks/useRequiredFields'

export function RegisterPage() {
  const { isAuthenticated } = useAuth()

  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const req = useRequiredFields(['fullName', 'username', 'password', 'confirm'] as const)

  if (isAuthenticated) return <Navigate to="/bang-tin" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ fullName, username, password, confirm })) return
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
              Đã gửi yêu cầu đăng ký. Tài khoản sẽ được sử dụng sau khi{' '}
              <strong>chỉ huy đơn vị bổ sung Cấp bậc, Chức danh, Đơn vị công tác và duyệt</strong>.
            </p>
            <Link to="/login" className="btn-solid">
              Về trang đăng nhập
            </Link>
          </div>
        ) : (
          <>
            <p className="login-note">
              Chỉ dành cho cán bộ / quân nhân chuyên nghiệp có biên chế thực tế tại đơn vị. Sau
              khi gửi đăng ký, chỉ huy sẽ bổ sung Cấp bậc, Chức danh, Đơn vị công tác rồi mới kích
              hoạt được tài khoản.
            </p>
            <form onSubmit={handleSubmit}>
              <Field label="Họ và tên" required req={req} name="fullName">
                <input
                  type="text"
                  maxLength={100}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  onBlur={(e) => req.mark('fullName', e.target.value)}
                  required
                  autoFocus
                />
              </Field>
              <Field label="Tên đăng nhập" required req={req} name="username">
                <input
                  type="text"
                  minLength={3}
                  maxLength={50}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onBlur={(e) => req.mark('username', e.target.value)}
                  required
                  autoComplete="username"
                />
              </Field>
              <Field label="Mật khẩu (tối thiểu 6 ký tự)" required req={req} name="password">
                <PasswordInput
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={(e) => req.mark('password', e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </Field>
              <Field label="Nhập lại mật khẩu" required req={req} name="confirm">
                <PasswordInput
                  minLength={6}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  onBlur={(e) => req.mark('confirm', e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </Field>
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
              Đã có tài khoản?{' '}
              <Link to="/login" className="login-note__register">
                <strong>Đăng nhập</strong>
              </Link>
            </p>
          </>
        )}
      </section>
    </div>
  )
}
