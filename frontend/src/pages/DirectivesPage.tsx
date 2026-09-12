import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { directivesApi } from '../api/directives'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { EmptyState } from '../components/EmptyState'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { CLASSIFICATION_LABELS, type Classification } from '../types/common'
import { roleLabel } from '../types/user'
import {
  DIRECTIVE_STATUS_LABELS,
  type Directive,
  type DirectiveAckReport,
  type DirectiveStatus,
} from '../types/directive'

const STATUSES = Object.keys(DIRECTIVE_STATUS_LABELS) as DirectiveStatus[]
const CLASSES = Object.keys(CLASSIFICATION_LABELS) as Classification[]
const PAGE_SIZE_OPTIONS = [10, 15, 30, 50]
type SortMode = 'recent' | 'ack'

function fmtDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString('vi-VN') : '—'
}
function fmtDateTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('vi-VN') : '—'
}

function AckMeter({ value, total }: { value: number; total: number }) {
  const pct = total ? Math.round((value / total) * 100) : 0
  return (
    <div
      className="gnv-progress"
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <span className="gnv-progress-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

export function DirectivesPage() {
  const { isCommander } = useAuth()
  const navigate = useNavigate()
  const confirm = useConfirm()

  const [directives, setDirectives] = useState<Directive[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeId, setActiveId] = useState<number | null>(null)
  const [acking, setAcking] = useState(false)

  const [reportOpen, setReportOpen] = useState(false)
  const [report, setReport] = useState<DirectiveAckReport | null>(null)
  const [reportLoading, setReportLoading] = useState(false)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<DirectiveStatus | ''>('')
  const [classFilter, setClassFilter] = useState<Classification | ''>('')
  const [sortMode, setSortMode] = useState<SortMode>('recent')
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(0)

  function loadDirectives() {
    setLoading(true)
    directivesApi
      .list({ limit: 500 })
      .then(setDirectives)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải chỉ thị – nhiệm vụ'),
      )
      .finally(() => setLoading(false))
  }
  useEffect(loadDirectives, [isCommander])

  const detail = useMemo(
    () => directives.find((d) => d.id === activeId) ?? null,
    [directives, activeId],
  )

  // Doi chi thi dang mo -> dong bang danh sach quan triet
  useEffect(() => {
    setReportOpen(false)
    setReport(null)
  }, [activeId])

  const stats = useMemo(() => {
    let published = 0
    let myPending = 0
    for (const d of directives) {
      if (d.status === 'da_ban_hanh') {
        published += 1
        if (!d.acknowledged_by_me) myPending += 1
      }
    }
    return {
      total: directives.length,
      published,
      drafts: directives.length - published,
      myPending,
    }
  }, [directives])

  const visible = useMemo(() => {
    const kw = search.trim().toLowerCase()
    const rows = directives.filter((d) => {
      if (statusFilter && d.status !== statusFilter) return false
      if (classFilter && d.classification !== classFilter) return false
      if (!kw) return true
      return (
        d.title.toLowerCase().includes(kw) ||
        d.content.toLowerCase().includes(kw) ||
        (d.author_full_name ?? '').toLowerCase().includes(kw)
      )
    })
    rows.sort((a, b) => {
      if (sortMode === 'ack') {
        const pa = a.recipient_count ? a.acknowledged_count / a.recipient_count : 1
        const pb = b.recipient_count ? b.acknowledged_count / b.recipient_count : 1
        return pa - pb
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
    return rows
  }, [directives, search, statusFilter, classFilter, sortMode])

  const total = visible.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const pageItems = visible.slice(safePage * pageSize, safePage * pageSize + pageSize)

  useEffect(() => {
    setPage(0)
  }, [search, statusFilter, classFilter, sortMode, pageSize])

  async function handleAcknowledge(id: number) {
    setError(null)
    setAcking(true)
    try {
      const updated = await directivesApi.acknowledge(id)
      setDirectives((prev) => prev.map((d) => (d.id === id ? updated : d)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xác nhận tiếp thu')
    } finally {
      setAcking(false)
    }
  }

  async function handleDelete(id: number) {
    const target = directives.find((d) => d.id === id)
    const ok = await confirm({
      message: (
        <>
          Xoá chỉ thị <strong>{target?.title ?? `#${id}`}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await directivesApi.remove(id)
      setDirectives((prev) => prev.filter((d) => d.id !== id))
      if (activeId === id) setActiveId(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá chỉ thị')
    }
  }

  async function toggleReport() {
    if (!detail) return
    if (reportOpen) {
      setReportOpen(false)
      return
    }
    setReportOpen(true)
    if (report && report.directive_id === detail.id) return
    setReportLoading(true)
    try {
      const r = await directivesApi.acknowledgements(detail.id)
      setReport(r)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách quán triệt')
      setReportOpen(false)
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <section className="dir-page">
      <div className="crumb-bar">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Điều hành – Nhiệm vụ</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">Chỉ thị – Nhiệm vụ</span>
        </nav>
      </div>

      <header className="cdb-head">
        <div>
          <h1>
            <Icon name="clipboard" size={22} /> Chỉ thị – Nhiệm vụ
            {stats.myPending > 0 ? <span className="badge-unread">{stats.myPending}</span> : null}
          </h1>
          <p className="state-note">
            <Icon name="lock" size={12} /> Mọi tài khoản thấy chỉ thị đã ban hành và bấm “đã tiếp
            thu”. Ban chỉ huy thấy thêm bản nháp và theo dõi mức độ quán triệt.
          </p>
        </div>
        <div className="cdb-head-actions">
          <button type="button" className="btn-cancel" onClick={loadDirectives} disabled={loading}>
            <Icon name="undo" size={14} /> Làm mới
          </button>
          {isCommander ? (
            <button
              type="button"
              className="btn-create"
              onClick={() => navigate('/chi-thi-nhiem-vu/moi')}
            >
              <Icon name="plus" size={16} /> Ban hành chỉ thị mới
            </button>
          ) : null}
        </div>
      </header>

      <div className="cdb-stats">
        <div className="cdb-stat">
          <span className="cdb-stat-value">{stats.total}</span>
          <span className="cdb-stat-label">Tổng số</span>
        </div>
        <div className="cdb-stat cdb-stat-done">
          <span className="cdb-stat-value">{stats.published}</span>
          <span className="cdb-stat-label">Đã ban hành</span>
        </div>
        <div className="cdb-stat cdb-stat-closed">
          <span className="cdb-stat-value">{stats.drafts}</span>
          <span className="cdb-stat-label">Bản nháp</span>
        </div>
        <div className="cdb-stat cdb-stat-unread">
          <span className="cdb-stat-value">{stats.myPending}</span>
          <span className="cdb-stat-label">Tôi chưa tiếp thu</span>
        </div>
      </div>

      {error ? (
        <p role="alert" className="form-error cdb-alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      <div className="cdb-grid">
        <aside className="cdb-sidebar">
          <div className="cdb-toolbar">
            <div className="cdb-search">
              <Icon name="search" size={14} />
              <input
                type="search"
                placeholder="Tìm theo tiêu đề, nội dung, người ban hành..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="cdb-toolbar-row">
              {isCommander ? (
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as DirectiveStatus | '')}
                  aria-label="Lọc theo trạng thái"
                >
                  <option value="">Mọi trạng thái</option>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {DIRECTIVE_STATUS_LABELS[s]}
                    </option>
                  ))}
                </select>
              ) : null}
              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value as Classification | '')}
                aria-label="Lọc theo độ mật"
              >
                <option value="">Mọi độ mật</option>
                {CLASSES.map((c) => (
                  <option key={c} value={c}>
                    {CLASSIFICATION_LABELS[c]}
                  </option>
                ))}
              </select>
              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as SortMode)}
                aria-label="Sắp xếp"
              >
                <option value="recent">Mới nhất</option>
                <option value="ack">Quán triệt thấp trước</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="cdb-skeleton-list">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="cdb-skeleton-row" />
              ))}
            </div>
          ) : directives.length === 0 ? (
            <EmptyState icon="clipboard" message="Chưa có chỉ thị – nhiệm vụ nào." />
          ) : total === 0 ? (
            <EmptyState icon="search" message="Không có chỉ thị nào khớp bộ lọc / từ khoá." />
          ) : (
            <>
              <ul className="cdb-thread-list">
                {pageItems.map((d) => {
                  const unacked = d.status === 'da_ban_hanh' && !d.acknowledged_by_me
                  return (
                    <li key={d.id}>
                      <button
                        type="button"
                        className={d.id === activeId ? 'cdb-thread active' : 'cdb-thread'}
                        onClick={() => setActiveId(d.id)}
                      >
                        <span className="cdb-thread-top">
                          <span className="cdb-thread-title">
                            {unacked ? <span className="dir-dot" aria-hidden="true" /> : null}
                            {d.title}
                          </span>
                        </span>
                        <span className="cdb-thread-tags">
                          <span className={`status-badge status-${d.status}`}>
                            {DIRECTIVE_STATUS_LABELS[d.status]}
                          </span>
                          <ClassificationBadge value={d.classification} />
                          {d.acknowledged_by_me ? (
                            <span className="chip chip-ok">
                              <Icon name="check" size={11} /> Đã tiếp thu
                            </span>
                          ) : null}
                        </span>
                        {d.status === 'da_ban_hanh' ? (
                          <>
                            <AckMeter value={d.acknowledged_count} total={d.recipient_count} />
                            <span className="cdb-thread-meta">
                              <Icon name="users" size={11} /> {d.acknowledged_count}/
                              {d.recipient_count} đã quán triệt
                            </span>
                          </>
                        ) : null}
                        <span className="cdb-thread-meta">
                          <Icon name="user" size={11} /> {d.author_full_name} · {fmtDate(d.created_at)}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
              <Pagination
                page={safePage}
                pageCount={pageCount}
                total={total}
                pageSize={pageSize}
                onPage={setPage}
                onPageSize={setPageSize}
                pageSizeOptions={PAGE_SIZE_OPTIONS}
                itemLabel="chỉ thị"
              />
            </>
          )}
        </aside>

        <div className="cdb-conversation dir-detail">
          {!detail ? (
            <div className="cdb-conv-empty">
              <Icon name="clipboard" size={44} />
              <p>Chọn một chỉ thị ở danh sách bên trái để xem toàn văn và theo dõi quán triệt.</p>
            </div>
          ) : (
            <>
              <div className="cdb-conv-head">
                <div className="cdb-conv-title">
                  <h2>{detail.title}</h2>
                  <div className="cdb-conv-sub">
                    <span className={`status-badge status-${detail.status}`}>
                      {DIRECTIVE_STATUS_LABELS[detail.status]}
                    </span>
                    <ClassificationBadge value={detail.classification} />
                    <span className="cdb-conv-by">
                      <Icon name="user" size={11} /> {detail.author_full_name} ·{' '}
                      {fmtDateTime(detail.created_at)}
                    </span>
                  </div>
                </div>
                {isCommander ? (
                  <div className="cdb-conv-actions">
                    <button
                      type="button"
                      className="btn-edit"
                      onClick={() => navigate(`/chi-thi-nhiem-vu/${detail.id}/sua`)}
                    >
                      <Icon name="edit" size={13} /> Sửa
                    </button>
                    <button
                      type="button"
                      className="btn-delete"
                      onClick={() => handleDelete(detail.id)}
                    >
                      <Icon name="trash" size={13} /> Xoá
                    </button>
                  </div>
                ) : null}
              </div>

              <div className="dir-body">
                <article className="dir-content">{detail.content}</article>

                {detail.status === 'da_ban_hanh' ? (
                  <div className="dir-ack">
                    <div className="dir-ack-head">
                      <strong>Mức độ quán triệt</strong>
                      <span>
                        {detail.acknowledged_count}/{detail.recipient_count} người
                      </span>
                    </div>
                    <AckMeter
                      value={detail.acknowledged_count}
                      total={detail.recipient_count}
                    />
                    <div className="dir-ack-actions">
                      <button
                        type="button"
                        className={detail.acknowledged_by_me ? 'btn-cancel' : 'btn-submit'}
                        disabled={detail.acknowledged_by_me || acking}
                        onClick={() => handleAcknowledge(detail.id)}
                      >
                        <Icon name="check" size={14} />{' '}
                        {detail.acknowledged_by_me
                          ? 'Bạn đã tiếp thu'
                          : acking
                            ? 'Đang ghi nhận...'
                            : 'Xác nhận đã tiếp thu'}
                      </button>
                      {isCommander ? (
                        <button type="button" className="btn-view" onClick={toggleReport}>
                          <Icon name={reportOpen ? 'eye-off' : 'eye'} size={13} />{' '}
                          {reportOpen ? 'Ẩn danh sách quán triệt' : 'Danh sách quán triệt'}
                        </button>
                      ) : null}
                    </div>

                    {isCommander && reportOpen ? (
                      reportLoading || !report ? (
                        <p className="state-note">Đang tải danh sách...</p>
                      ) : (
                        <div className="dir-report">
                          <div className="dir-report-col">
                            <h4 className="ack-done">
                              <Icon name="check" size={13} /> Đã tiếp thu ({report.acknowledged.length})
                            </h4>
                            {report.acknowledged.length === 0 ? (
                              <p className="state-note">Chưa có ai.</p>
                            ) : (
                              <ul>
                                {report.acknowledged.map((u) => (
                                  <li key={u.user_id}>
                                    <span>{u.full_name}</span>
                                    <em>
                                      {roleLabel(u.role)} · {fmtDateTime(u.acknowledged_at)}
                                    </em>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                          <div className="dir-report-col">
                            <h4 className="ack-todo">
                              <Icon name="clock" size={13} /> Chưa tiếp thu ({report.pending.length})
                            </h4>
                            {report.pending.length === 0 ? (
                              <p className="state-note">Tất cả đã tiếp thu.</p>
                            ) : (
                              <ul>
                                {report.pending.map((u) => (
                                  <li key={u.user_id}>
                                    <span>{u.full_name}</span>
                                    <em>{roleLabel(u.role)}</em>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                      )
                    ) : null}
                  </div>
                ) : (
                  <p className="state-note dir-draft-note">
                    <Icon name="lock" size={13} /> Đây là bản nháp — chưa ban hành nên đơn vị chưa
                    nhìn thấy.
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}
