import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { profileApi } from '../api/profile'
import { Field } from '../components/Field'
import { PasswordInput } from '../components/PasswordInput'
import { useAuth } from '../context/AuthContext'
import { useRequiredFields } from '../hooks/useRequiredFields'

/**
 * Man hinh buoc doi mat khau lan dau (tai khoan do admin cap / vua duoc reset).
 * Sau khi doi thanh cong se dang nhap lai bang mat khau moi de lam moi token
 * (claim `mcp` chuyen ve false), roi ve trang chu.
 */
export function ChangePasswordPage() {
  const { username, mustChangePassword, login, logout } = useAuth()
  const navigate = useNavigate()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const req = useRequiredFields(['currentPassword', 'newPassword', 'confirm'] as const)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ currentPassword, newPassword, confirm })) return
    if (newPassword !== confirm) {
      setError('Mật khẩu xác nhận không khớp')
      return
    }
    setSubmitting(true)
    try {
      await profileApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      if (username) {
        await login({ username, password: newPassword })
        navigate('/', { replace: true })
      } else {
        logout()
        navigate('/login', { replace: true })
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể đổi mật khẩu')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-page">
      <div className="block-section" style={{ maxWidth: 460, margin: '0 auto' }}>
        <h1>Đổi mật khẩu</h1>
        {mustChangePassword ? (
          <p className="state-note">
            Đây là lần đăng nhập đầu tiên hoặc mật khẩu vừa được cấp lại. Vui lòng đặt mật khẩu mới
            (tối thiểu 8 ký tự, gồm cả chữ và số) trước khi tiếp tục.
          </p>
        ) : null}

        <form onSubmit={handleSubmit} className="entity-form">
          <Field label="Mật khẩu hiện tại" required req={req} name="currentPassword">
            <PasswordInput
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              onBlur={(e) => req.mark('currentPassword', e.target.value)}
              required
            />
          </Field>
          <Field label="Mật khẩu mới" required req={req} name="newPassword">
            <PasswordInput
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onBlur={(e) => req.mark('newPassword', e.target.value)}
              required
            />
          </Field>
          <Field label="Xác nhận mật khẩu mới" required req={req} name="confirm">
            <PasswordInput
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              onBlur={(e) => req.mark('confirm', e.target.value)}
              required
            />
          </Field>
          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              Đổi mật khẩu &amp; tiếp tục
            </button>
          </div>
          {error ? (
            <p role="alert" className="form-error">
              {error}
            </p>
          ) : null}
        </form>
      </div>
    </section>
  )
}
