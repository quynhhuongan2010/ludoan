import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { profileApi } from '../api/profile'
import type { User } from '../types/user'

const ROLE_LABELS: Record<string, string> = {
  commander: 'Chỉ huy',
  officer: 'Cán bộ',
  soldier: 'Chiến sĩ',
}

export function ProfilePage() {
  const [me, setMe] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [fullName, setFullName] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileMsg, setProfileMsg] = useState<string | null>(null)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [savingPassword, setSavingPassword] = useState(false)
  const [passwordMsg, setPasswordMsg] = useState<string | null>(null)
  const [passwordErr, setPasswordErr] = useState<string | null>(null)

  useEffect(() => {
    profileApi
      .me()
      .then((user) => {
        setMe(user)
        setFullName(user.full_name)
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải hồ sơ cá nhân'),
      )
      .finally(() => setLoading(false))
  }, [])

  async function handleProfileSubmit(event: FormEvent) {
    event.preventDefault()
    setProfileMsg(null)
    setError(null)
    setSavingProfile(true)
    try {
      const updated = await profileApi.update({ full_name: fullName })
      setMe(updated)
      setFullName(updated.full_name)
      setProfileMsg('Đã cập nhật họ tên.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể cập nhật hồ sơ')
    } finally {
      setSavingProfile(false)
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault()
    setPasswordMsg(null)
    setPasswordErr(null)
    setSavingPassword(true)
    try {
      await profileApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setPasswordMsg('Đổi mật khẩu thành công.')
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      setPasswordErr(
        err instanceof ApiError ? err.message : 'Không thể đổi mật khẩu',
      )
    } finally {
      setSavingPassword(false)
    }
  }

  if (loading) return <p className="state-note">Đang tải hồ sơ...</p>
  if (error && !me) return <p className="state-note form-error">{error}</p>
  if (!me) return null

  return (
    <section>
      <h1>Hồ sơ cá nhân</h1>

      <div className="profile-grid">
        <dl className="profile-facts">
          <dt>Tên đăng nhập</dt>
          <dd>{me.username}</dd>
          <dt>Vai trò</dt>
          <dd>{ROLE_LABELS[me.role] ?? me.role}</dd>
          <dt>Trạng thái</dt>
          <dd>{me.is_active ? 'Đang hoạt động' : 'Đã vô hiệu hoá'}</dd>
        </dl>

        <form onSubmit={handleProfileSubmit} className="entity-form">
          <h2>Cập nhật họ tên</h2>
          <label>
            Họ tên
            <input
              type="text"
              maxLength={100}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={savingProfile}>
              Lưu thay đổi
            </button>
          </div>
          {profileMsg ? <p className="form-success">{profileMsg}</p> : null}
          {error ? <p role="alert" className="form-error">{error}</p> : null}
        </form>

        <form onSubmit={handlePasswordSubmit} className="entity-form">
          <h2>Đổi mật khẩu</h2>
          <label>
            Mật khẩu hiện tại
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </label>
          <label>
            Mật khẩu mới
            <input
              type="password"
              minLength={6}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={savingPassword}>
              Đổi mật khẩu
            </button>
          </div>
          {passwordMsg ? <p className="form-success">{passwordMsg}</p> : null}
          {passwordErr ? <p role="alert" className="form-error">{passwordErr}</p> : null}
        </form>
      </div>
    </section>
  )
}
