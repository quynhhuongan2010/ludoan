import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { unitsApi } from '../api/units'
import { usersApi } from '../api/users'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import type { Unit } from '../types/unit'
import type { User, UserCreate } from '../types/user'

const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị hệ thống',
  commander: 'Chỉ huy (Ban chỉ huy)',
  officer: 'Cán bộ / Nhân viên',
  soldier: 'Chiến sĩ / Nội bộ',
}

const emptyForm: UserCreate = {
  username: '',
  password: '',
  full_name: '',
  role: 'soldier',
  unit_id: null,
  directive_channel_access: false,
  command_channel_access: false,
}

export function UsersPage() {
  const { userId, isAdmin } = useAuth()
  const roleOptions = isAdmin
    ? ['soldier', 'officer', 'commander', 'admin']
    : ['soldier', 'officer', 'commander']

  const [users, setUsers] = useState<User[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<UserCreate>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  function loadUsers() {
    setLoading(true)
    Promise.all([usersApi.list(), unitsApi.list()])
      .then(([us, un]) => {
        setUsers(us)
        setUnits(un)
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách'))
      .finally(() => setLoading(false))
  }

  useEffect(loadUsers, [])

  function unitName(id: number | null): string {
    if (id == null) return '—'
    return units.find((u) => u.id === id)?.name ?? `#${id}`
  }

  function replaceUser(u: User) {
    setUsers((prev) => prev.map((x) => (x.id === u.id ? u : x)))
  }

  async function runOn(id: number, fn: () => Promise<User>) {
    setError(null)
    setBusyId(id)
    try {
      replaceUser(await fn())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Thao tác không thành công')
    } finally {
      setBusyId(null)
    }
  }

  async function handleResetPassword(u: User) {
    const pw = window.prompt(`Mật khẩu mới cho "${u.username}" (≥ 8 ký tự, có cả chữ và số):`)
    if (!pw) return
    setError(null)
    setBusyId(u.id)
    try {
      await usersApi.resetPassword(u.id, pw)
      window.alert('Đã cấp lại mật khẩu. Người dùng sẽ phải đổi mật khẩu ở lần đăng nhập kế tiếp.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không cấp lại được mật khẩu')
    } finally {
      setBusyId(null)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const created = await usersApi.create({
        ...form,
        unit_id: form.unit_id || null,
      })
      setUsers((prev) => [created, ...prev])
      setForm(emptyForm)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể tạo tài khoản')
    } finally {
      setSubmitting(false)
    }
  }

  const pending = users.filter((u) => !u.is_active)

  return (
    <section>
      <h1>Quản lý người dùng</h1>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      <p className="state-note">
        <Icon name="lock" size={12} /> <strong>Vai trò</strong> quyết định quyền nội dung:{' '}
        <em>Cán bộ / Nhân viên</em> được đăng &amp; sửa Tin tức + Giáo dục chính trị (bài gửi lên ở
        trạng thái <em>chờ duyệt</em>); <em>Chỉ huy</em> đăng là đăng thẳng, được{' '}
        <strong>duyệt / trả lại</strong> bài của mọi người và ban hành Chỉ thị – Nhiệm vụ;{' '}
        <em>Chiến sĩ</em> chỉ xem.{' '}
        <strong>Quyền xem MẬT</strong> cho phép xem &amp; tạo nội dung phân loại “MẬT” và truy cập{' '}
        <em>Kênh chỉ huy (MẬT)</em>. Cột <strong>Kênh Chỉ đạo</strong> mở quyền vào Kênh Chỉ đạo –
        Báo cáo (chỉ admin cấp được). Tài khoản mới tạo sẽ phải đổi mật khẩu ở lần đăng nhập đầu.
      </p>

      {pending.length > 0 ? (
        <div className="block-section pending-box">
          <div className="block-title">
            <span>
              <Icon name="user" size={15} /> Tài khoản chờ duyệt ({pending.length})
            </span>
          </div>
          <table>
            <thead>
              <tr>
                <th>Họ tên</th>
                <th>Tên đăng nhập</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {pending.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td>{u.username}</td>
                  <td className="right">
                    <button
                      type="button"
                      disabled={busyId === u.id}
                      onClick={() => runOn(u.id, () => usersApi.activate(u.id))}
                    >
                      Kích hoạt
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="entity-form">
        <h2>Tạo tài khoản trực tiếp</h2>
        <label>
          Tên đăng nhập
          <input
            type="text"
            maxLength={50}
            value={form.username}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            required
          />
        </label>
        <label>
          Mật khẩu
          <input
            type="password"
            minLength={8}
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            required
          />
        </label>
        <label>
          Họ tên
          <input
            type="text"
            maxLength={100}
            value={form.full_name}
            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            required
          />
        </label>
        <label>
          Vai trò
          <select value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
            {roleOptions.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Đơn vị
          <select
            value={form.unit_id ?? ''}
            onChange={(e) =>
              setForm((f) => ({ ...f, unit_id: e.target.value ? Number(e.target.value) : null }))
            }
          >
            <option value="">— Chưa gán —</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </label>
        {isAdmin ? (
          <label className="switch-cell">
            <input
              type="checkbox"
              checked={form.directive_channel_access ?? false}
              onChange={(e) =>
                setForm((f) => ({ ...f, directive_channel_access: e.target.checked }))
              }
            />
            Cấp quyền vào Kênh Chỉ đạo – Báo cáo
          </label>
        ) : null}
        <div className="form-actions">
          <button type="submit" disabled={submitting}>
            Tạo tài khoản
          </button>
        </div>
      </form>

      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên đăng nhập</th>
              <th>Họ tên</th>
              <th>Vai trò</th>
              <th>Đơn vị</th>
              <th>Trạng thái</th>
              <th>Xem MẬT</th>
              <th>Kênh Chỉ đạo</th>
              <th>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = u.id === userId
              const locked = u.is_system
              return (
                <tr key={u.id}>
                  <td>
                    {u.id}
                    {locked ? (
                      <>
                        {' '}
                        <Icon name="lock" size={11} />
                      </>
                    ) : null}
                  </td>
                  <td>{u.username}</td>
                  <td>{u.full_name}</td>
                  <td>
                    <select
                      value={u.role}
                      disabled={busyId === u.id || isSelf || locked}
                      onChange={(e) => runOn(u.id, () => usersApi.setRole(u.id, e.target.value))}
                    >
                      {[...new Set([...roleOptions, u.role])].map((r) => (
                        <option key={r} value={r}>
                          {ROLE_LABELS[r] ?? r}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      value={u.unit_id ?? ''}
                      disabled={busyId === u.id || locked}
                      onChange={(e) =>
                        runOn(u.id, () =>
                          usersApi.setUnit(u.id, e.target.value ? Number(e.target.value) : null),
                        )
                      }
                      title={unitName(u.unit_id)}
                    >
                      <option value="">— Chưa gán —</option>
                      {units.map((un) => (
                        <option key={un.id} value={un.id}>
                          {un.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <span className={u.is_active ? 'ack-done' : 'ack-todo'}>
                      {u.is_active ? 'Hoạt động' : 'Chờ / khoá'}
                    </span>
                  </td>
                  <td>
                    <label className="switch-cell">
                      <input
                        type="checkbox"
                        checked={u.clearance}
                        disabled={busyId === u.id || u.role === 'commander' || u.role === 'admin'}
                        onChange={(e) => runOn(u.id, () => usersApi.setClearance(u.id, e.target.checked))}
                      />
                      {u.role === 'commander' || u.role === 'admin'
                        ? 'Toàn quyền'
                        : u.clearance
                          ? 'Được cấp'
                          : 'Không'}
                    </label>
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      checked={u.directive_channel_access}
                      disabled={busyId === u.id || !isAdmin || u.role === 'commander' || u.role === 'admin'}
                      onChange={(e) =>
                        runOn(u.id, () =>
                          usersApi.setChannelAccess(u.id, { directive_channel_access: e.target.checked }),
                        )
                      }
                    />
                  </td>
                  <td className="row-actions">
                    {u.is_active ? (
                      <button
                        type="button"
                        disabled={busyId === u.id || isSelf || locked}
                        onClick={() => runOn(u.id, () => usersApi.deactivate(u.id))}
                      >
                        Khoá
                      </button>
                    ) : (
                      <button
                        type="button"
                        disabled={busyId === u.id}
                        onClick={() => runOn(u.id, () => usersApi.activate(u.id))}
                      >
                        Kích hoạt
                      </button>
                    )}
                    {isAdmin ? (
                      <button
                        type="button"
                        disabled={busyId === u.id}
                        onClick={() => handleResetPassword(u)}
                      >
                        Cấp lại MK
                      </button>
                    ) : null}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </section>
  )
}
