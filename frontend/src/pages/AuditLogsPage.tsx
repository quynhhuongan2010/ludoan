import { useEffect, useState } from 'react'
import { auditLogsApi } from '../api/auditLogs'
import { ApiError } from '../api/client'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { AUDIT_ACTION_LABELS, type AuditLogItem } from '../types/auditLog'
import { roleLabel, type Role } from '../types/user'

const ACTION_OPTIONS = [
  { value: '', label: '— Tất cả hành động —' },
  { value: 'LOGIN_SUCCESS', label: 'Đăng nhập thành công' },
  { value: 'LOGIN_FAILED', label: 'Đăng nhập thất bại' },
  { value: 'DISPATCH_DOWNLOAD', label: 'Tải công văn mật' },
  { value: 'USER_ACTIVATE', label: 'Kích hoạt tài khoản' },
  { value: 'USER_DEACTIVATE', label: 'Khóa tài khoản' },
  { value: 'ROLE_CHANGE', label: 'Thay đổi vai trò' },
  { value: 'CLEARANCE_CHANGE', label: 'Cấp/Thu hồi cơ mật' },
  { value: 'DIRECTIVE_CHANNEL_ACCESS', label: 'Quyền Kênh chỉ đạo' },
  { value: 'COMMAND_CHANNEL_ACCESS', label: 'Quyền Kênh chỉ huy' },
  { value: 'PASSWORD_RESET', label: 'Đặt lại mật khẩu' },
]

const TARGET_TYPE_OPTIONS = [
  { value: '', label: '— Tất cả đối tượng —' },
  { value: 'auth', label: 'Xác thực / Đăng nhập' },
  { value: 'user', label: 'Tài khoản người dùng' },
  { value: 'dispatch', label: 'Công văn tài liệu' },
  { value: 'command_thread', label: 'Kênh chỉ huy' },
]

export function AuditLogsPage() {
  const { isCommander, isAdmin } = useAuth()
  const canAccess = isCommander || isAdmin

  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Bộ lọc
  const [search, setSearch] = useState('')
  const [action, setAction] = useState('')
  const [targetType, setTargetType] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'failed'>('all')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const pageCount = Math.max(1, Math.ceil(total / pageSize))

  function loadLogs() {
    if (!canAccess) return
    setLoading(true)
    setError(null)

    const is_success =
      statusFilter === 'all' ? undefined : statusFilter === 'success'

    auditLogsApi
      .getLogs({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        action: action || undefined,
        target_type: targetType || undefined,
        is_success,
        from_date: fromDate ? `${fromDate}T00:00:00` : undefined,
        to_date: toDate ? `${toDate}T23:59:59` : undefined,
      })
      .then((res) => {
        setLogs(res.items)
        setTotal(res.total)
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : 'Không thể tải nhật ký an ninh.')
      })
      .finally(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    loadLogs()
  }, [page, pageSize, action, targetType, statusFilter])

  function handleFilterSubmit(e: React.FormEvent) {
    e.preventDefault()
    setPage(1)
    loadLogs()
  }

  function handleResetFilters() {
    setSearch('')
    setAction('')
    setTargetType('')
    setStatusFilter('all')
    setFromDate('')
    setToDate('')
    setPage(1)
  }

  function formatDateTime(iso: string) {
    try {
      const d = new Date(iso)
      const day = String(d.getDate()).padStart(2, '0')
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const year = d.getFullYear()
      const hours = String(d.getHours()).padStart(2, '0')
      const minutes = String(d.getMinutes()).padStart(2, '0')
      const seconds = String(d.getSeconds()).padStart(2, '0')
      return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`
    } catch {
      return iso
    }
  }

  if (!canAccess) {
    return (
      <section className="container" style={{ padding: '30px 0' }}>
        <div className="block-section pending-box" style={{ borderColor: '#ef4444' }}>
          <div className="block-title" style={{ color: '#b91c1c' }}>
            <span>
              <Icon name="alert-triangle" size={18} /> Từ chối truy cập
            </span>
          </div>
          <p style={{ marginTop: '10px' }}>
            Chỉ Ban Chỉ huy và Quản trị hệ thống mới có thẩm quyền kiểm tra Sổ nhật ký an ninh mạng.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Icon name="shield" size={24} /> Nhật ký an ninh mạng (Audit Trail)
        </h1>
        <p className="state-note" style={{ marginTop: '6px' }}>
          Ghi nhận và truy vết tự động các sự kiện an ninh, phiên đăng nhập, thay đổi quyền hạn và
          thao tác với dữ liệu mật trong toàn hệ thống Cổng thông tin.
        </p>
      </div>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {/* Thanh bộ lọc */}
      <form
        onSubmit={handleFilterSubmit}
        className="block-section"
        style={{
          marginBottom: '20px',
          padding: '16px',
          background: 'var(--bg-surface, #fff)',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
            alignItems: 'end',
          }}
        >
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
              Từ khóa tìm kiếm
            </label>
            <input
              type="text"
              placeholder="IP, Họ tên, chi tiết..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
              Loại hành động
            </label>
            <select
              value={action}
              onChange={(e) => {
                setAction(e.target.value)
                setPage(1)
              }}
              style={{ width: '100%' }}
            >
              {ACTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
              Đối tượng
            </label>
            <select
              value={targetType}
              onChange={(e) => {
                setTargetType(e.target.value)
                setPage(1)
              }}
              style={{ width: '100%' }}
            >
              {TARGET_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
              Kết quả
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as 'all' | 'success' | 'failed')
                setPage(1)
              }}
              style={{ width: '100%' }}
            >
              <option value="all">— Tất cả kết quả —</option>
              <option value="success">Thành công</option>
              <option value="failed">Thất bại / Bị chặn</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
              Từ ngày
            </label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value)
                setPage(1)
              }}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
              Đến ngày
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value)
                setPage(1)
              }}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="submit"
              className="btn-create"
              style={{
                flex: 1,
                padding: '8px 12px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <Icon name="search" size={15} /> Tìm
            </button>
            <button
              type="button"
              className="icon-btn"
              onClick={handleResetFilters}
              title="Đặt lại bộ lọc"
              style={{ padding: '8px' }}
            >
              <Icon name="undo" size={15} />
            </button>
          </div>
        </div>
      </form>

      {/* Bảng danh sách log */}
      {loading ? (
        <p className="state-note">Đang tải nhật ký an ninh...</p>
      ) : logs.length === 0 ? (
        <p className="state-note">Không có bản ghi nhật ký nào phù hợp với điều kiện tìm kiếm.</p>
      ) : (
        <div style={{ overflowX: 'auto', background: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <table>
            <thead>
              <tr>
                <th style={{ width: '150px' }}>Thời gian</th>
                <th style={{ width: '180px' }}>Người thực hiện</th>
                <th style={{ width: '180px' }}>Hành động</th>
                <th style={{ width: '150px' }}>Đối tượng</th>
                <th style={{ width: '130px' }}>Địa chỉ IP</th>
                <th style={{ width: '110px' }}>Kết quả</th>
                <th>Chi tiết thao tác</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((item) => {
                const actionMeta = AUDIT_ACTION_LABELS[item.action] || {
                  label: item.action,
                  color: 'gray',
                }
                return (
                  <tr key={item.id}>
                    <td style={{ fontSize: '13px', whiteSpace: 'nowrap', color: '#64748b' }}>
                      {formatDateTime(item.created_at)}
                    </td>
                    <td>
                      {item.actor_username ? (
                        <div>
                          <strong>{item.actor_full_name || item.actor_username}</strong>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            @{item.actor_username}{' '}
                            {item.actor_role !== null ? (
                              <span style={{ fontSize: '11px', color: '#0f766e' }}>
                                ({roleLabel(item.actor_role as Role)})
                              </span>
                            ) : null}
                          </div>
                        </div>
                      ) : (
                        <span style={{ fontStyle: 'italic', color: '#94a3b8' }}>Hệ thống / Vô danh</span>
                      )}
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 600,
                          backgroundColor:
                            actionMeta.color === 'red'
                              ? '#fee2e2'
                              : actionMeta.color === 'green'
                              ? '#dcfce7'
                              : actionMeta.color === 'blue'
                              ? '#dbeafe'
                              : actionMeta.color === 'purple'
                              ? '#f3e8ff'
                              : actionMeta.color === 'amber'
                              ? '#fef3c7'
                              : '#f1f5f9',
                          color:
                            actionMeta.color === 'red'
                              ? '#991b1b'
                              : actionMeta.color === 'green'
                              ? '#166534'
                              : actionMeta.color === 'blue'
                              ? '#1e40af'
                              : actionMeta.color === 'purple'
                              ? '#6b21a8'
                              : actionMeta.color === 'amber'
                              ? '#92400e'
                              : '#334155',
                        }}
                      >
                        {actionMeta.label}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px' }}>
                      {item.target_name ? (
                        <div>
                          <span>{item.target_name}</span>
                          {item.target_type ? (
                            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                              [{item.target_type}]
                            </div>
                          ) : null}
                        </div>
                      ) : item.target_type ? (
                        <span style={{ color: '#64748b' }}>[{item.target_type}]</span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td style={{ fontSize: '13px', fontFamily: 'monospace' }}>
                      {item.ip_address || '—'}
                    </td>
                    <td>
                      <span className={item.is_success ? 'ack-done' : 'ack-todo'}>
                        {item.is_success ? 'Thành công' : 'Thất bại'}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px', color: '#334155' }}>
                      {item.details || '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Phân trang */}
      {!loading && total > 0 ? (
        <div className="pager" style={{ marginTop: '16px' }}>
          <span>
            Tổng <strong>{total}</strong> bản ghi — Trang {page}/{pageCount}
          </span>
          <label className="pager-size">
            Hiển thị
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1)
              }}
            >
              {[10, 20, 50, 100].map((n) => (
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
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <Icon name="chevron-right" size={15} className="flip-x" />
          </button>
          <button
            type="button"
            className="icon-btn"
            title="Trang sau"
            aria-label="Trang sau"
            disabled={page >= pageCount}
            onClick={() => setPage((p) => p + 1)}
          >
            <Icon name="chevron-right" size={15} />
          </button>
        </div>
      ) : null}
    </section>
  )
}
