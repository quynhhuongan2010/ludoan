import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { profileApi } from '../api/profile'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { PasswordInput } from '../components/PasswordInput'
import { useRequiredFields } from '../hooks/useRequiredFields'
import {
  BRANCH_BADGE_COLORS,
  PERMISSION_LABELS,
  type UserPermissions,
} from '../types/rbac'
import { roleLabel, type User } from '../types/user'

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2)
  return (parts[0][0] + parts[parts.length - 1][0])
}

export function ProfilePage() {
  const [me, setMe] = useState<User | null>(null)
  const [perms, setPerms] = useState<UserPermissions | null>(null)
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

  const nameReq = useRequiredFields(['fullName'] as const)
  const pwReq = useRequiredFields(['currentPassword', 'newPassword'] as const)

  useEffect(() => {
    Promise.all([
      profileApi.me(),
      profileApi.getPermissions().catch(() => null),
    ])
      .then(([user, userPerms]) => {
        setMe(user)
        setFullName(user.full_name)
        setPerms(userPerms)
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
    if (!nameReq.validate({ fullName })) return
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
    if (!pwReq.validate({ currentPassword, newPassword })) return
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
      setPasswordErr(err instanceof ApiError ? err.message : 'Không thể đổi mật khẩu')
    } finally {
      setSavingPassword(false)
    }
  }

  if (loading) return <p className="state-note">Đang tải hồ sơ...</p>
  if (error && !me) return <p className="state-note form-error">{error}</p>
  if (!me) return null

  const profileDirty = fullName.trim() !== me.full_name && fullName.trim().length > 0

  return (
    <section className="profile-page">
      <h1>Hồ sơ cá nhân</h1>

      <div className="profile-identity">
        <div className="profile-avatar" aria-hidden="true">
          {initials(me.full_name)}
        </div>
        <div className="profile-identity-main">
          <h2>{me.full_name}</h2>
          {me.rank || me.position ? (
            <p className="profile-rank">
              {[me.rank, me.position].filter(Boolean).join(' · ')}
            </p>
          ) : null}
          <p className="profile-username">
            <Icon name="user" size={13} /> {me.username}
          </p>
          <div className="profile-chips">
            <span className="chip chip-role">{me.role_label || roleLabel(me.role)}</span>
            {perms?.branch_label ? (
              <span
                className={`chip font-medium border ${BRANCH_BADGE_COLORS[perms.branch]?.bg || ''} ${BRANCH_BADGE_COLORS[perms.branch]?.text || ''} ${BRANCH_BADGE_COLORS[perms.branch]?.border || ''}`}
              >
                <Icon name="shield" size={11} /> {perms.branch_label}
              </span>
            ) : null}
            <span className={`chip ${me.is_active ? 'chip-ok' : 'chip-off'}`}>
              {me.is_active ? 'Đang hoạt động' : 'Đã vô hiệu hoá'}
            </span>
            {me.unit_name ? <span className="chip">{me.unit_name}</span> : null}
            {me.clearance ? (
              <span className="chip chip-mat">
                <Icon name="lock" size={11} /> Quyền xem MẬT
              </span>
            ) : null}
          </div>
        </div>
      </div>

      <div className="profile-cards">
        <form onSubmit={handleProfileSubmit} className="entity-form">
          <div className="card-head">
            <h2>
              <Icon name="user" size={16} /> Thông tin cá nhân
            </h2>
            <p>Họ tên hiển thị cho các tài khoản khác trên toàn hệ thống.</p>
          </div>
          <Field label="Họ tên" required req={nameReq} name="fullName">
            <input
              type="text"
              maxLength={100}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              onBlur={(e) => nameReq.mark('fullName', e.target.value)}
              required
            />
          </Field>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={savingProfile || !profileDirty}>
              {savingProfile ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>
          {profileMsg ? <p className="form-note form-success">{profileMsg}</p> : null}
          {error ? (
            <p role="alert" className="form-note form-error">
              {error}
            </p>
          ) : null}
        </form>

        <form onSubmit={handlePasswordSubmit} className="entity-form">
          <div className="card-head">
            <h2>
              <Icon name="lock" size={16} /> Bảo mật
            </h2>
            <p>Đổi mật khẩu đăng nhập. Mật khẩu mới tối thiểu 6 ký tự.</p>
          </div>
          <Field label="Mật khẩu hiện tại" required req={pwReq} name="currentPassword">
            <PasswordInput
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              onBlur={(e) => pwReq.mark('currentPassword', e.target.value)}
              required
            />
          </Field>
          <Field label="Mật khẩu mới" required req={pwReq} name="newPassword">
            <PasswordInput
              minLength={6}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onBlur={(e) => pwReq.mark('newPassword', e.target.value)}
              required
            />
          </Field>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={savingPassword}>
              {savingPassword ? 'Đang xử lý...' : 'Đổi mật khẩu'}
            </button>
          </div>
          {passwordMsg ? <p className="form-note form-success">{passwordMsg}</p> : null}
          {passwordErr ? (
            <p role="alert" className="form-note form-error">
              {passwordErr}
            </p>
          ) : null}
        </form>

        {perms?.permissions ? (
          <div className="entity-form profile-permissions-card md:col-span-2">
            <div className="card-head">
              <h2>
                <Icon name="shield" size={16} /> Ma trận thẩm quyền quân sự (RBAC)
              </h2>
              <p>
                Phân định thẩm quyền theo Cương vị và Khối cơ quan chuyên trách ({perms.branch_label}).
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-1">
              {Object.entries(PERMISSION_LABELS).map(([key, meta]) => {
                const granted = Boolean(perms.permissions[key])
                return (
                  <div
                    key={key}
                    className={`flex items-center justify-between p-2 rounded border ${
                      granted
                        ? 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-200/80 dark:border-emerald-900/40 text-slate-800 dark:text-slate-200'
                        : 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] uppercase font-bold text-slate-500">[{meta.group}]</span>
                      <span>{meta.label}</span>
                    </div>
                    {granted ? (
                      <span className="text-emerald-600 font-bold flex items-center gap-0.5">
                        <Icon name="check" size={13} />
                        <span>Cho phép</span>
                      </span>
                    ) : (
                      <span className="text-slate-400 font-medium">Không</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  )
}
