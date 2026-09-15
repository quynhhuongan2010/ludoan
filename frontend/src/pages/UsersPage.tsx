import { Fragment, useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { unitsApi } from '../api/units'
import { usersApi } from '../api/users'
import { Icon } from '../components/Icon'
import { Modal } from '../components/Modal'
import { PasswordInput } from '../components/PasswordInput'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { useAlert, usePrompt } from '../context/PromptContext'
import type { Unit } from '../types/unit'
import { roleLabel, type Role, type User, type UserCreate, type UserImportResult } from '../types/user'

function getMilitaryEchelonRank(u: User, unitList: Unit[]): number {
  if (u.role === 0 || u.username === 'admin' || u.is_system) return 0 // Quản trị kỹ thuật tách biệt hoàn toàn
  const unit = unitList.find((un) => un.id === u.unit_id)
  const uName = (unit?.name ?? u.unit_name ?? '').toLowerCase()
  const pos = (u.position ?? '').toLowerCase()
  if (u.role === 1 || u.role === 2 || uName.includes('ban chỉ huy') || pos.includes('lữ trưởng') || pos.includes('chính uỷ') || pos.includes('chính ủy')) return 1 // Ban Chỉ huy Lữ đoàn
  if (uName.includes('tham mưu') || uName.includes('chính trị') || uName.includes('hậu cần') || unit?.unit_kind === 'phong_ban') return 2 // Cơ quan Phòng ban chức năng
  if (uName.includes('tiểu đoàn') || unit?.unit_kind === 'tieu_doan') return 3 // Các Tiểu đoàn thông tin
  if (uName.includes('đại đội') || unit?.unit_kind === 'dai_doi') return 4 // Đại đội trực thuộc
  if (uName.includes('trung tâm')) return 5 // Trung tâm trực thuộc
  if (uName.includes('trạm') || unit?.unit_kind === 'tram') return 6 // Các Trạm TTLL
  return 7 // Khác
}

function getEchelonLabel(rank: number): string {
  switch (rank) {
    case 0: return '🛡️ I. KHỐI QUẢN TRỊ KỸ THUẬT HỆ THỐNG (TÁCH BIỆT HOÀN TOÀN KHỎI BIÊN CHẾ QUÂN SỰ)'
    case 1: return '⭐ II. BAN CHỈ HUY LỮ ĐOÀN (LỮ TRƯỞNG, CHÍNH UỶ, PHÓ LỮ TRƯỞNG, PHÓ CHÍNH UỶ)'
    case 2: return '🏢 III. CƠ QUAN PHÒNG BAN CHỨC NĂNG (THAM MƯU, CHÍNH TRỊ, HẬU CẦN - KỸ THUẬT)'
    case 3: return '🚩 IV. CÁC TIỂU ĐOÀN THÔNG TIN TÁC CHIẾN (TIỂU ĐOÀN 1, TIỂU ĐOÀN 2)'
    case 4: return '🎖️ V. ĐẠI ĐỘI TRỰC THUỘC (ĐẠI ĐỘI 5)'
    case 5: return '📡 VI. TRUNG TÂM TRỰC THUỘC (TRUNG TÂM 2)'
    case 6: return '📻 VII. CÁC TRẠM THÔNG TIN LIÊN LẠC (TRẠM KIỂM SOÁT, TRẠM BẢO ĐẢM KỸ THUẬT)'
    default: return '👥 VIII. QUÂN NHÂN CÁC ĐƠN VỊ KHÁC'
  }
}

const emptyCreate: UserCreate = {
  username: '',
  password: '',
  full_name: '',
  role: 4,
  rank: '',
  position: '',
  unit_id: 0,
  directive_channel_access: false,
  command_channel_access: false,
}

export function UsersPage() {
  const { userId, isAdmin, role: myRole } = useAuth()
  const confirm = useConfirm()
  const prompt = usePrompt()
  const alert = useAlert()
  // Chỉ admin (role 0) mới được đặt vai trò 0; các cấp chỉ huy khác đặt 1..5.
  const roleOptions: Role[] = isAdmin ? [0, 1, 2, 3, 4, 5] : [1, 2, 3, 4, 5]
  // Xoá hẳn tài khoản: chỉ Quản trị hệ thống (0), Lữ trưởng - Chính uỷ (1),
  // Lữ phó - Phó chính uỷ (2). Chỉ huy đơn vị (3) chỉ được khoá.
  const canDeleteUsers = myRole !== null && myRole <= 2

  const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

  const [users, setUsers] = useState<User[]>([])
  const [pending, setPending] = useState<User[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState<UserCreate>(emptyCreate)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  // State nhap tu file Excel / Word
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<UserImportResult | null>(null)
  const [importError, setImportError] = useState<string | null>(null)

  // State don dep toan bo tai khoan test
  const [showPurgeModal, setShowPurgeModal] = useState(false)
  const [purgeInput, setPurgeInput] = useState('')
  const [purging, setPurging] = useState(false)

  const pageCount = Math.max(1, Math.ceil(total / pageSize))

  function loadUsers() {
    setLoading(true)
    Promise.all([
      usersApi.list({ skip: page * pageSize, limit: pageSize }),
      usersApi.list({ active: false, limit: 500 }),
      unitsApi.list(),
    ])
      .then(([pageRes, pendingRes, un]) => {
        setUsers(pageRes.items)
        setTotal(pageRes.total)
        setPending(pendingRes.items)
        setUnits(un)
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách'))
      .finally(() => setLoading(false))
  }

  useEffect(loadUsers, [page, pageSize])

  function unitName(id: number | null): string {
    if (id == null) return '—'
    return units.find((u) => u.id === id)?.name ?? `#${id}`
  }

  async function runOn(id: number, fn: () => Promise<User>) {
    setError(null)
    setBusyId(id)
    try {
      const updated = await fn()
      setUsers((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))
      // Tai lai de dong bo hop "cho duyet", tong so va phan trang
      loadUsers()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Thao tác không thành công')
    } finally {
      setBusyId(null)
    }
  }

  async function handleResetPassword(u: User) {
    const res = await prompt({
      title: 'Cấp lại mật khẩu',
      message: `Đặt mật khẩu mới cho tài khoản "${u.username}".`,
      fields: [
        {
          name: 'password',
          label: 'Mật khẩu mới (≥ 8 ký tự, có cả chữ và số)',
          type: 'password',
          maxLength: 128,
        },
      ],
      confirmText: 'Cấp lại',
    })
    if (!res) return
    setError(null)
    setBusyId(u.id)
    try {
      await usersApi.resetPassword(u.id, res.password)
      await alert({
        title: 'Đã cấp lại mật khẩu',
        message: 'Người dùng sẽ phải đổi mật khẩu ở lần đăng nhập kế tiếp.',
        tone: 'success',
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không cấp lại được mật khẩu')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(u: User) {
    const ok = await confirm({
      title: 'Xoá tài khoản',
      message: (
        <>
          Xoá hẳn tài khoản <strong>{u.username}</strong> ({u.full_name})? Thao tác không thể
          hoàn tác. Nếu tài khoản đã từng đăng nội dung / hoạt động, hãy khoá thay vì xoá.
        </>
      ),
      confirmText: 'Xoá tài khoản',
    })
    if (!ok) return
    setError(null)
    setBusyId(u.id)
    try {
      await usersApi.remove(u.id)
      loadUsers()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không xoá được tài khoản')
    } finally {
      setBusyId(null)
    }
  }

  function openCreate() {
    setCreateForm(emptyCreate)
    setCreateError(null)
    setShowCreate(true)
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setCreating(true)
    setCreateError(null)
    try {
      await usersApi.create({
        ...createForm,
        unit_id: Number(createForm.unit_id),
      })
      setShowCreate(false)
      setPage(0)
      loadUsers()
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : 'Không tạo được tài khoản')
    } finally {
      setCreating(false)
    }
  }

  async function handleImportSubmit(e: FormEvent) {
    e.preventDefault()
    if (!importFile) return
    setImporting(true)
    setImportError(null)
    setImportResult(null)
    try {
      const res = await usersApi.importFile(importFile)
      setImportResult(res)
      setPage(0)
      loadUsers()
    } catch (err) {
      setImportError(err instanceof ApiError ? err.message : 'Lỗi khi xử lý file danh sách quân nhân')
    } finally {
      setImporting(false)
    }
  }

  async function handlePurgeConfirm(e: FormEvent) {
    e.preventDefault()
    if (purgeInput.trim() !== 'XAC NHAN XOA') return
    setPurging(true)
    try {
      await usersApi.purgeTestUsers()
      setShowPurgeModal(false)
      setPurgeInput('')
      setPage(0)
      loadUsers()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể dọn dẹp tài khoản thử nghiệm')
    } finally {
      setPurging(false)
    }
  }

  async function handleEditInfo(u: User) {
    const res = await prompt({
      title: 'Sửa Cấp bậc / Chức danh',
      fields: [
        {
          name: 'rank',
          label: 'Cấp bậc quân hàm',
          defaultValue: u.rank ?? '',
          placeholder: 'VD: Thiếu uý',
          maxLength: 100,
        },
        {
          name: 'position',
          label: 'Chức danh công tác',
          defaultValue: u.position ?? '',
          placeholder: 'VD: Trợ lý Tham mưu',
          maxLength: 150,
        },
      ],
      confirmText: 'Lưu',
    })
    if (!res) return
    await runOn(u.id, () => usersApi.setInfo(u.id, { rank: res.rank, position: res.position }))
  }

  const canCreate = units.length > 0

  return (
    <section>
      <h1 style={{ paddingBottom: '20px' }}>Quản lý người dùng</h1>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      <div className="actions-bar" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          type="button"
          className="btn-create"
          onClick={openCreate}
          disabled={!canCreate}
          title={canCreate ? undefined : 'Chưa có đơn vị nào — tạo đơn vị trước ở "Quản lý đơn vị"'}
        >
          <Icon name="plus" size={16} /> Tạo tài khoản trực tiếp
        </button>

        {isAdmin && (
          <>
            <button
              type="button"
              className="btn-file"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: '#14532d',
                color: '#86efac',
                border: '1px solid #16a34a',
                padding: '6px 14px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '13px',
              }}
              onClick={() => {
                setImportFile(null)
                setImportError(null)
                setImportResult(null)
                setShowImportModal(true)
              }}
            >
              <Icon name="upload" size={16} /> Nhập từ file (Excel / Word)
            </button>

            <button
              type="button"
              className="btn-danger"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: '#7f1d1d',
                color: '#fecaca',
                border: '1px solid #dc2626',
                padding: '6px 14px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '13px',
                marginLeft: 'auto',
              }}
              onClick={() => {
                setPurgeInput('')
                setShowPurgeModal(true)
              }}
            >
              <Icon name="trash" size={16} /> Xóa tài khoản
            </button>
          </>
        )}
      </div>

      {pending.length > 0 ? (
        <div className="block-section pending-box">
          <div className="block-title">
            <span>
              <Icon name="user" size={15} /> Tài khoản chờ duyệt ({pending.length})
            </span>
          </div>
          <p className="state-note">
            Chỉ cán bộ / QNCN có biên chế thực tế mới được cấp tài khoản. Bổ sung đủ Cấp bậc,
            Chức danh và Đơn vị công tác trước khi kích hoạt.
          </p>
          <table>
            <thead>
              <tr>
                <th>Họ tên</th>
                <th>Tên đăng nhập</th>
                <th>Cấp bậc</th>
                <th>Chức danh</th>
                <th>Đơn vị</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {pending.map((u) => (
                <PendingRow
                  key={u.id}
                  user={u}
                  units={units}
                  busy={busyId === u.id}
                  onActivated={() => {
                    setError(null)
                    loadUsers()
                  }}
                  onError={setError}
                  setBusy={(busy) => setBusyId(busy ? u.id : null)}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên đăng nhập</th>
              <th>Họ tên</th>
              <th>Cấp bậc</th>
              <th>Chức danh</th>
              <th>Vai trò</th>
              <th>Đơn vị</th>
              <th>Trạng thái</th>
              <th>Xem MẬT</th>
              <th>Kênh Chỉ đạo</th>
              <th>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {(() => {
              const sortedUsers = [...users].sort((a, b) => {
                const rankA = getMilitaryEchelonRank(a, units)
                const rankB = getMilitaryEchelonRank(b, units)
                if (rankA !== rankB) return rankA - rankB
                return a.id - b.id
              })

              let currentEchelon = -1

              return sortedUsers.map((u) => {
                const isSelf = u.id === userId
                const locked = u.is_system
                const uEchelon = getMilitaryEchelonRank(u, units)
                const showEchelonHeader = uEchelon !== currentEchelon
                if (showEchelonHeader) {
                  currentEchelon = uEchelon
                }

                return (
                  <Fragment key={u.id}>
                    {showEchelonHeader && (
                      <tr
                        className={`echelon-header-row echelon-${uEchelon}`}
                        style={{
                          background:
                            uEchelon === 0
                              ? 'linear-gradient(90deg, rgba(220, 38, 38, 0.22) 0%, rgba(153, 27, 27, 0.1) 100%)'
                              : uEchelon === 1
                                ? 'linear-gradient(90deg, rgba(245, 158, 11, 0.22) 0%, rgba(217, 119, 6, 0.08) 100%)'
                                : 'linear-gradient(90deg, rgba(59, 130, 246, 0.16) 0%, rgba(37, 99, 235, 0.05) 100%)',
                          borderTop: '2px solid rgba(255, 255, 255, 0.15)',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                        }}
                      >
                        <td
                          colSpan={11}
                          style={{
                            padding: '10px 16px',
                            fontWeight: 700,
                            fontSize: '13px',
                            letterSpacing: '0.3px',
                            color:
                              uEchelon === 0
                                ? '#ff6b6b'
                                : uEchelon === 1
                                  ? '#302c2c'
                                  : '#7ec8ff',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span>{getEchelonLabel(uEchelon)}</span>
                            {uEchelon === 0 && (
                              <span
                                style={{
                                  fontSize: '11px',
                                  fontWeight: 500,
                                  background: 'rgba(239, 68, 68, 0.35)',
                                  color: '#ffffff',
                                  padding: '3px 10px',
                                  borderRadius: '4px',
                                  border: '1px solid rgba(239, 68, 68, 0.6)',
                                }}
                              >
                                Độc lập kỹ thuật — Toàn quyền hệ thống
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                    <tr
                      style={
                        uEchelon === 0
                          ? { background: 'rgba(239, 68, 68, 0.04)' }
                          : undefined
                      }
                    >
                      <td>
                        {u.id}
                        {locked ? (
                          <>
                            {' '}
                            <Icon name="lock" size={11} />
                          </>
                        ) : null}
                      </td>
                      <td>
                        <strong>{u.username}</strong>
                        {uEchelon === 0 && (
                          <span
                            style={{
                              marginLeft: '6px',
                              fontSize: '10px',
                              background: '#7f1d1d',
                              color: '#fecaca',
                              padding: '1px 5px',
                              borderRadius: '3px',
                              fontWeight: 600,
                            }}
                          >
                            ADMIN HỆ THỐNG
                          </span>
                        )}
                      </td>
                      <td>{u.full_name}</td>
                      <td>{u.rank || '—'}</td>
                      <td>
                        {u.position || '—'}{' '}
                        <button
                          type="button"
                          className="chip-remove"
                          title="Sửa Cấp bậc / Chức danh"
                          aria-label="Sửa Cấp bậc / Chức danh"
                          disabled={busyId === u.id}
                          onClick={() => handleEditInfo(u)}
                        >
                          <Icon name="edit" size={11} />
                        </button>
                      </td>
                      <td>
                        <select
                          value={u.role}
                          disabled={busyId === u.id || isSelf || locked}
                          onChange={(e) =>
                            runOn(u.id, () => usersApi.setRole(u.id, Number(e.target.value) as Role))
                          }
                        >
                          {[...new Set<Role>([...roleOptions, u.role])].map((r) => (
                            <option key={r} value={r}>
                              {roleLabel(r)}
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
                          <option value="">{uEchelon === 0 ? '— Độc lập kỹ thuật —' : '— Chưa gán —'}</option>
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
                            disabled={busyId === u.id || u.role <= 3}
                            onChange={(e) => runOn(u.id, () => usersApi.setClearance(u.id, e.target.checked))}
                          />
                          {u.role <= 3 ? 'Toàn quyền' : u.clearance ? 'Được cấp' : 'Không'}
                        </label>
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          checked={u.directive_channel_access}
                          disabled={busyId === u.id || !isAdmin || u.role <= 3}
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
                            className="icon-btn tint-danger"
                            title="Khoá tài khoản"
                            aria-label="Khoá tài khoản"
                            disabled={busyId === u.id || isSelf || locked}
                            onClick={() => runOn(u.id, () => usersApi.deactivate(u.id))}
                          >
                            <Icon name="lock" size={15} />
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="icon-btn tint-ok"
                            title="Kích hoạt tài khoản"
                            aria-label="Kích hoạt tài khoản"
                            disabled={busyId === u.id}
                            onClick={() => runOn(u.id, () => usersApi.activate(u.id))}
                          >
                            <Icon name="check" size={15} />
                          </button>
                        )}
                        {isAdmin ? (
                          <button
                            type="button"
                            className="icon-btn tint-info"
                            title="Cấp lại mật khẩu"
                            aria-label="Cấp lại mật khẩu"
                            disabled={busyId === u.id}
                            onClick={() => handleResetPassword(u)}
                          >
                            <Icon name="key" size={15} />
                          </button>
                        ) : null}
                        {canDeleteUsers ? (
                          <button
                            type="button"
                            className="icon-btn tint-danger"
                            title={
                              isSelf
                                ? 'Không thể tự xoá tài khoản của mình'
                                : locked && !isAdmin
                                  ? 'Không thể xoá tài khoản hệ thống'
                                  : u.role <= 2 && !isAdmin
                                    ? 'Chỉ Quản trị viên (Admin) mới có quyền xoá tài khoản cấp chỉ huy'
                                    : 'Xoá tài khoản'
                            }
                            aria-label="Xoá tài khoản"
                            disabled={busyId === u.id || isSelf || (locked && !isAdmin) || (u.role <= 2 && !isAdmin)}
                            onClick={() => handleDelete(u)}
                          >
                            <Icon name="trash" size={15} />
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  </Fragment>
                )
              })
            })()}
          </tbody>
        </table>
      )}

      {!loading && total > 0 ? (
        <div className="pager">
          <span>
            Tổng {total} tài khoản — trang {page + 1}/{pageCount}
          </span>
          <label className="pager-size">
            Hiển thị
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(0)
              }}
            >
              {PAGE_SIZE_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n} dòng
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="icon-btn"
            title="Trang trước"
            aria-label="Trang trước"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            <Icon name="chevron-right" size={15} className="flip-x" />
          </button>
          <button
            type="button"
            className="icon-btn"
            title="Trang sau"
            aria-label="Trang sau"
            disabled={page + 1 >= pageCount}
            onClick={() => setPage((p) => p + 1)}
          >
            <Icon name="chevron-right" size={15} />
          </button>
        </div>
      ) : null}

      {showCreate ? (
        <Modal
          title="Tạo tài khoản trực tiếp"
          onClose={() => setShowCreate(false)}
          closeOnOverlayClick={false}
        >
          <form onSubmit={handleCreate} className="entity-form">
            <p className="state-note">
              Chỉ cấp cho cán bộ / QNCN có biên chế thực tế. Tài khoản tạo ở đây sẽ{' '}
              <strong>hoạt động ngay</strong> (không qua bước chờ duyệt) và phải đổi mật khẩu ở
              lần đăng nhập đầu.
            </p>
            <label>
              Tên đăng nhập
              <input
                type="text"
                maxLength={50}
                value={createForm.username}
                onChange={(e) => setCreateForm((f) => ({ ...f, username: e.target.value }))}
                required
                autoFocus
              />
            </label>
            <label>
              Mật khẩu (tối thiểu 6 ký tự)
              <PasswordInput
                minLength={6}
                value={createForm.password}
                onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
                required
              />
            </label>
            <label>
              Họ tên
              <input
                type="text"
                maxLength={100}
                value={createForm.full_name}
                onChange={(e) => setCreateForm((f) => ({ ...f, full_name: e.target.value }))}
                required
              />
            </label>
            <div className="form-row">
              <label>
                Cấp bậc quân hàm
                <input
                  type="text"
                  maxLength={100}
                  placeholder="VD: Thiếu uý"
                  value={createForm.rank}
                  onChange={(e) => setCreateForm((f) => ({ ...f, rank: e.target.value }))}
                  required
                />
              </label>
              <label>
                Chức danh công tác
                <input
                  type="text"
                  maxLength={150}
                  placeholder="VD: Trợ lý Tham mưu"
                  value={createForm.position}
                  onChange={(e) => setCreateForm((f) => ({ ...f, position: e.target.value }))}
                  required
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                Vai trò
                <select
                  value={createForm.role}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, role: Number(e.target.value) as Role }))
                  }
                >
                  {roleOptions.map((r) => (
                    <option key={r} value={r}>
                      {roleLabel(r)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Đơn vị công tác
                <select
                  value={createForm.unit_id || ''}
                  onChange={(e) => setCreateForm((f) => ({ ...f, unit_id: Number(e.target.value) }))}
                  required
                >
                  <option value="">— Chọn đơn vị —</option>
                  {units.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {isAdmin ? (
              <label className="switch-cell">
                <input
                  type="checkbox"
                  checked={createForm.directive_channel_access ?? false}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, directive_channel_access: e.target.checked }))
                  }
                />
                Cấp quyền vào Kênh Chỉ đạo – Báo cáo
              </label>
            ) : null}
            {createError ? (
              <p role="alert" className="form-note form-error">
                {createError}
              </p>
            ) : null}
            <div className="form-actions">
              <button
                type="submit"
                className="btn-submit"
                disabled={creating || !createForm.unit_id}
              >
                {creating ? 'Đang tạo...' : 'Tạo tài khoản'}
              </button>
              <button type="button" className="btn-cancel" onClick={() => setShowCreate(false)}>
                Huỷ
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {showImportModal ? (
        <Modal
          title="Nhập danh sách quân nhân từ File (Excel / Word)"
          onClose={() => {
            setShowImportModal(false)
            setImportResult(null)
            setImportError(null)
          }}
          closeOnOverlayClick={false}
        >
          <div className="entity-form" style={{ maxWidth: '640px' }}>
            <div
              style={{
                background: '#f1f5f9',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '12px 16px',
                marginBottom: '16px',
                fontSize: '13px',
                lineHeight: '1.6',
              }}
            >
              <div style={{ fontWeight: 600, color: '#0369a1', marginBottom: '6px' }}>
                Hướng dẫn định dạng tệp tải lên:
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#334155' }}>
                <li>Hỗ trợ file bảng tính Excel (<strong>.xlsx, .xls</strong>) hoặc văn bản Word (<strong>.docx</strong> có bảng).</li>
                <li>Cột bắt buộc: <strong>STT | Họ và tên | Tên đăng nhập | Mật khẩu | Cấp bậc | Chức danh | Đơn vị | Vai trò</strong>.</li>
                <li>
                  <strong style={{ color: '#b91c1c' }}>Tài khoản Admin đã được tách biệt riêng</strong> về mặt kỹ thuật, không cần nhập trong danh sách này.
                </li>
                <li>Nếu cột Mật khẩu để trống, hệ thống tự động gán mật khẩu mặc định: <code>LuDoan21@2026</code>.</li>
              </ul>
              <div style={{ marginTop: '12px', display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  className="btn-link"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: '#15803d',
                    textDecoration: 'underline',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                  onClick={() => usersApi.downloadTemplate('excel')}
                >
                  <Icon name="download" size={14} /> Tải file mẫu Excel (.xlsx)
                </button>
                <button
                  type="button"
                  className="btn-link"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: '#1d4ed8',
                    textDecoration: 'underline',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                  onClick={() => usersApi.downloadTemplate('word')}
                >
                  <Icon name="download" size={14} /> Tải file mẫu Word (.docx)
                </button>
              </div>
            </div>

            <form onSubmit={handleImportSubmit}>
              <label>
                Chọn tệp danh sách quân nhân (.xlsx, .xls, .docx)
                <input
                  type="file"
                  accept=".xlsx,.xls,.docx"
                  onChange={(e) => {
                    const file = e.target.files?.[0] || null
                    setImportFile(file)
                    setImportError(null)
                    setImportResult(null)
                  }}
                  required
                />
              </label>

              {importError ? (
                <p role="alert" className="form-note form-error">
                  {importError}
                </p>
              ) : null}

              {importResult ? (
                <div
                  style={{
                    marginTop: '14px',
                    padding: '12px',
                    background: importResult.error_count === 0 ? '#f0fdf4' : '#fffbeb',
                    border: `1px solid ${importResult.error_count === 0 ? '#16a34a' : '#d97706'}`,
                    borderRadius: '6px',
                  }}
                >
                  <div style={{ fontWeight: 600, color: importResult.error_count === 0 ? '#15803d' : '#b45309', marginBottom: '4px' }}>
                    Kết quả nhập dữ liệu:
                  </div>
                  <div style={{ fontSize: '13px', color: '#334155' }}>
                    Tổng số dòng: <strong>{importResult.total_rows}</strong> | Nhập thành công: <strong style={{ color: '#15803d' }}>{importResult.success_count}</strong> | Lỗi: <strong style={{ color: '#b91c1c' }}>{importResult.error_count}</strong>
                  </div>

                  {importResult.created_usernames.length > 0 && (
                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#64748b' }}>
                      Các tài khoản đã thêm: {importResult.created_usernames.join(', ')}
                    </div>
                  )}

                  {importResult.errors.length > 0 && (
                    <div style={{ marginTop: '10px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#b91c1c', marginBottom: '4px' }}>
                        Chi tiết dòng lỗi:
                      </div>
                      <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr style={{ background: 'rgba(0,0,0,0.08)', textAlign: 'left' }}>
                            <th style={{ padding: '4px 8px' }}>Dòng</th>
                            <th style={{ padding: '4px 8px' }}>Username</th>
                            <th style={{ padding: '4px 8px' }}>Lý do lỗi</th>
                          </tr>
                        </thead>
                        <tbody>
                          {importResult.errors.map((err, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.08)' }}>
                              <td style={{ padding: '4px 8px' }}>{err.row_index}</td>
                              <td style={{ padding: '4px 8px' }}>{err.username || '—'}</td>
                              <td style={{ padding: '4px 8px', color: '#b91c1c' }}>{err.error}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : null}

              <div className="form-actions" style={{ marginTop: '18px' }}>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={importing || !importFile}
                >
                  {importing ? 'Đang đọc và tạo tài khoản...' : 'Bắt đầu nhập dữ liệu'}
                </button>
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => {
                    setShowImportModal(false)
                    setImportResult(null)
                    setImportError(null)
                  }}
                >
                  Đóng
                </button>
              </div>
            </form>
          </div>
        </Modal>
      ) : null}

      {showPurgeModal ? (
        <Modal
          title="Cảnh báo: Dọn dẹp / Xoá sạch toàn bộ tài khoản thử nghiệm"
          onClose={() => {
            setShowPurgeModal(false)
            setPurgeInput('')
          }}
          closeOnOverlayClick={false}
        >
          <form onSubmit={handlePurgeConfirm} className="entity-form" style={{ maxWidth: '520px' }}>
            <div
              style={{
                background: '#fef2f2',
                border: '1px solid #dc2626',
                borderRadius: '8px',
                padding: '14px',
                marginBottom: '16px',
                fontSize: '13px',
                lineHeight: '1.6',
                color: '#7f1d1d',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '6px', color: '#b91c1c' }}>
                ⚠️ THAO TÁC NGUY HIỂM — KHÔNG THỂ HOÀN TÁC!
              </div>
              <p style={{ margin: '0 0 8px 0' }}>
                Thao tác này sẽ <strong>xoá sạch toàn bộ tất cả tài khoản quân nhân thử nghiệm</strong> hiện có trong cơ sở dữ liệu (bao gồm cả tài khoản cấp chỉ huy thử nghiệm, phòng ban, phân đội) để làm sạch hệ thống.
              </p>
              <p style={{ margin: 0, fontWeight: 600, color: '#15803d' }}>
                🛡️ CHỈ DUY NHẤT TÀI KHOẢN ADMIN HỆ THỐNG ĐƯỢC GIỮ LẠI (TÁCH BIỆT AN TOÀN).
              </p>
            </div>

            <label>
              Để xác nhận, vui lòng nhập chính xác cụm từ: <strong>XAC NHAN XOA</strong>
              <input
                type="text"
                value={purgeInput}
                onChange={(e) => setPurgeInput(e.target.value)}
                placeholder="Nhập: XAC NHAN XOA"
                required
                autoFocus
                style={{
                  letterSpacing: '1px',
                  fontWeight: 600,
                  borderColor: purgeInput === 'XAC NHAN XOA' ? '#ef4444' : undefined,
                }}
              />
            </label>

            <div className="form-actions" style={{ marginTop: '20px' }}>
              <button
                type="submit"
                className="btn-danger"
                disabled={purging || purgeInput.trim() !== 'XAC NHAN XOA'}
                style={{
                  background: '#dc2626',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 18px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  cursor: purgeInput.trim() === 'XAC NHAN XOA' ? 'pointer' : 'not-allowed',
                }}
              >
                {purging ? 'Đang dọn dẹp hệ thống...' : 'Xác nhận xoá toàn bộ tài khoản thử nghiệm'}
              </button>
              <button
                type="button"
                className="btn-cancel"
                onClick={() => {
                  setShowPurgeModal(false)
                  setPurgeInput('')
                }}
              >
                Huỷ bỏ
              </button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  )
}

/** Mot dong "tai khoan cho duyet": bo sung Cap bac + Chuc danh + Don vi roi kich hoat gop. */
function PendingRow({
  user,
  units,
  busy,
  setBusy,
  onActivated,
  onError,
}: {
  user: User
  units: Unit[]
  busy: boolean
  setBusy: (busy: boolean) => void
  onActivated: () => void
  onError: (msg: string) => void
}) {
  const [rank, setRank] = useState(user.rank ?? '')
  const [position, setPosition] = useState(user.position ?? '')
  const [unitId, setUnitId] = useState(user.unit_id != null ? String(user.unit_id) : '')

  const ready = rank.trim() !== '' && position.trim() !== '' && unitId !== ''

  async function activate() {
    setBusy(true)
    try {
      await usersApi.setInfo(user.id, { rank: rank.trim(), position: position.trim() })
      await usersApi.setUnit(user.id, Number(unitId))
      await usersApi.activate(user.id)
      onActivated()
    } catch (err) {
      onError(err instanceof ApiError ? err.message : 'Không kích hoạt được tài khoản')
    } finally {
      setBusy(false)
    }
  }

  return (
    <tr>
      <td>{user.full_name}</td>
      <td>{user.username}</td>
      <td>
        <input
          type="text"
          placeholder="VD: Thiếu uý"
          maxLength={100}
          value={rank}
          disabled={busy}
          onChange={(e) => setRank(e.target.value)}
        />
      </td>
      <td>
        <input
          type="text"
          placeholder="VD: Trợ lý Tham mưu"
          maxLength={150}
          value={position}
          disabled={busy}
          onChange={(e) => setPosition(e.target.value)}
        />
      </td>
      <td>
        <select value={unitId} disabled={busy} onChange={(e) => setUnitId(e.target.value)}>
          <option value="">— Chọn đơn vị —</option>
          {units.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      </td>
      <td className="right">
        <button type="button" disabled={busy || !ready} onClick={activate} title={!ready ? 'Cần nhập đủ Cấp bậc, Chức danh, Đơn vị' : undefined}>
          Bổ sung & Kích hoạt
        </button>
      </td>
    </tr>
  )
}
