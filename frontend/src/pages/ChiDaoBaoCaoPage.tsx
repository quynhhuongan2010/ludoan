import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { directiveThreadsApi } from '../api/directiveThreads'
import { unitsApi } from '../api/units'
import { EmptyState } from '../components/EmptyState'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import type { DirectiveThread, DirectiveThreadDetail } from '../types/directiveThread'
import type { Unit } from '../types/unit'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const fileUrl = (url: string | null) =>
  url && url.startsWith('/static') ? `${API_BASE}${url}` : url ?? ''

const PAGE_SIZE_OPTIONS = [8, 15, 30]

const AVATAR_COLORS = [
  '#2c6540',
  '#1d4ed8',
  '#b45309',
  '#7c3aed',
  '#be123c',
  '#0f766e',
  '#4d7c0f',
]

type StatusFilter = '' | 'open' | 'closed'
type SortMode = 'recent' | 'unread' | 'title'

function when(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function relTime(iso: string | null): string {
  if (!iso) return 'chưa có hoạt động'
  const d = new Date(iso).getTime()
  if (Number.isNaN(d)) return ''
  const min = Math.round((Date.now() - d) / 60000)
  if (min < 1) return 'vừa xong'
  if (min < 60) return `${min} phút trước`
  const h = Math.round(min / 60)
  if (h < 24) return `${h} giờ trước`
  const day = Math.round(h / 24)
  if (day < 7) return `${day} ngày trước`
  return new Date(iso).toLocaleDateString('vi-VN')
}

function dayLabel(iso: string): string {
  const d = new Date(iso)
  const today = new Date()
  const yst = new Date()
  yst.setDate(today.getDate() - 1)
  if (d.toDateString() === today.toDateString()) return 'Hôm nay'
  if (d.toDateString() === yst.toDateString()) return 'Hôm qua'
  return d.toLocaleDateString('vi-VN', {
    weekday: 'long',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function timeOnly(iso: string): string {
  return new Date(iso).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[parts.length - 2][0] + parts[parts.length - 1][0]).toUpperCase()
}

function colorFor(seed: string): string {
  let h = 0
  for (let i = 0; i < seed.length; i += 1) h = (h * 31 + seed.charCodeAt(i)) >>> 0
  return AVATAR_COLORS[h % AVATAR_COLORS.length]
}

export function ChiDaoBaoCaoPage() {
  const navigate = useNavigate()
  const { isCommander, userId } = useAuth()

  const [threads, setThreads] = useState<DirectiveThread[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<DirectiveThreadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Tao luong moi
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newUnitId, setNewUnitId] = useState('')
  const [creating, setCreating] = useState(false)

  // Bo loc / sap xep / phan trang danh sach luong (client-side)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('')
  const [unitFilter, setUnitFilter] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('recent')
  const [pageSize, setPageSize] = useState(8)
  const [page, setPage] = useState(0)

  // Soan tin
  const [body, setBody] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [sending, setSending] = useState(false)
  const fileRef = useRef<HTMLInputElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const { clearDraft } = useDraftAutosave(
    activeId != null ? `chidao-msg:${activeId}` : null,
    body,
    setBody,
  )

  const loadThreads = useCallback(() => {
    setLoading(true)
    const jobs: [Promise<DirectiveThread[]>, Promise<Unit[]>] = [
      directiveThreadsApi.list({ limit: 500 }),
      isCommander ? unitsApi.list({ active: true }) : Promise.resolve<Unit[]>([]),
    ]
    Promise.all(jobs)
      .then(([ts, us]) => {
        setThreads(ts)
        setUnits(us)
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không tải được danh sách luồng'),
      )
      .finally(() => setLoading(false))
  }, [isCommander])

  useEffect(loadThreads, [loadThreads])

  const openThread = useCallback((id: number) => {
    setActiveId(id)
    setDetailLoading(true)
    directiveThreadsApi
      .get(id)
      .then((d) => {
        setDetail(d)
        setThreads((prev) => prev.map((t) => (t.id === d.id ? { ...t, unread_count: 0 } : t)))
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không mở được luồng'),
      )
      .finally(() => setDetailLoading(false))
  }, [])

  useEffect(() => {
    if (activeId == null) setDetail(null)
  }, [activeId])

  // Tu cuon xuong tin moi nhat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end' })
  }, [detail?.id, detail?.messages.length])

  // Tu gian chieu cao o soan tin
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [body])

  const stats = useMemo(() => {
    const open = threads.filter((t) => !t.is_closed).length
    const unread = threads.reduce((s, t) => s + t.unread_count, 0)
    return { total: threads.length, open, closed: threads.length - open, unread }
  }, [threads])

  const visibleThreads = useMemo(() => {
    const kw = search.trim().toLowerCase()
    const filtered = threads.filter((t) => {
      if (statusFilter === 'open' && t.is_closed) return false
      if (statusFilter === 'closed' && !t.is_closed) return false
      if (unitFilter && String(t.unit_id) !== unitFilter) return false
      if (!kw) return true
      return (
        t.title.toLowerCase().includes(kw) ||
        (t.unit_name ?? '').toLowerCase().includes(kw) ||
        (t.created_by_full_name ?? '').toLowerCase().includes(kw)
      )
    })
    const byRecent = (a: DirectiveThread, b: DirectiveThread) =>
      new Date(b.last_message_at ?? b.created_at).getTime() -
      new Date(a.last_message_at ?? a.created_at).getTime()
    filtered.sort((a, b) => {
      if (sortMode === 'unread' && b.unread_count !== a.unread_count)
        return b.unread_count - a.unread_count
      if (sortMode === 'title') return a.title.localeCompare(b.title, 'vi')
      return byRecent(a, b)
    })
    return filtered
  }, [threads, search, statusFilter, unitFilter, sortMode])

  const total = visibleThreads.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const pageItems = visibleThreads.slice(safePage * pageSize, safePage * pageSize + pageSize)

  useEffect(() => {
    setPage(0)
  }, [search, statusFilter, unitFilter, sortMode, pageSize])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const created = await directiveThreadsApi.create({
        title: newTitle.trim(),
        unit_id: isCommander ? (newUnitId ? Number(newUnitId) : null) : undefined,
      })
      setThreads((prev) => [created, ...prev])
      setNewTitle('')
      setNewUnitId('')
      setShowCreate(false)
      openThread(created.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tạo được luồng')
    } finally {
      setCreating(false)
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault()
    if (!activeId) return
    if (!body.trim() && !file) return
    setError(null)
    setSending(true)
    try {
      await directiveThreadsApi.postMessage(activeId, body.trim(), file)
      setBody('')
      clearDraft()
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      const d = await directiveThreadsApi.get(activeId)
      setDetail(d)
      setThreads((prev) =>
        prev.map((t) =>
          t.id === d.id
            ? {
                ...t,
                message_count: d.message_count,
                last_message_at: d.last_message_at,
                unread_count: 0,
              }
            : t,
        ),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không gửi được tin')
    } finally {
      setSending(false)
    }
  }

  function onComposerKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      void handleSend(e as unknown as FormEvent)
    }
  }

  async function toggleClose() {
    if (!detail) return
    setError(null)
    try {
      const updated = await directiveThreadsApi.close(detail.id, !detail.is_closed)
      setDetail((d) => (d ? { ...d, is_closed: updated.is_closed } : d))
      setThreads((prev) =>
        prev.map((t) => (t.id === updated.id ? { ...t, is_closed: updated.is_closed } : t)),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không đổi được trạng thái luồng')
    }
  }

  const canSubmitNew = newTitle.trim().length > 0 && (!isCommander || newUnitId !== '')

  return (
    <section className="cdb-page">
      <div className="crumb-bar">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Điều hành – Nhiệm vụ</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">Kênh Chỉ đạo – Báo cáo</span>
        </nav>
      </div>

      <header className="cdb-head">
        <div>
          <h1>
            <Icon name="shield" size={22} /> Kênh Chỉ đạo – Báo cáo
            {stats.unread > 0 ? <span className="badge-unread">{stats.unread}</span> : null}
          </h1>
          <p className="state-note">
            <Icon name="lock" size={12} /> Trao đổi &amp; báo cáo hai chiều giữa Ban chỉ huy Lữ đoàn
            và đơn vị. Chỉ tài khoản được cấp quyền kênh mới truy cập được. Đơn vị cấp dưới chỉ thấy
            luồng của đơn vị mình.
          </p>
        </div>
        <div className="cdb-head-actions">
          <button type="button" className="btn-cancel" onClick={loadThreads} disabled={loading}>
            <Icon name="undo" size={14} /> Làm mới
          </button>
          <button
            type="button"
            className="btn-create"
            onClick={() => setShowCreate((v) => !v)}
          >
            <Icon name="plus" size={16} /> Tạo luồng
          </button>
        </div>
      </header>

      <div className="cdb-stats">
        <div className="cdb-stat">
          <span className="cdb-stat-value">{stats.total}</span>
          <span className="cdb-stat-label">Tổng số luồng</span>
        </div>
        <div className="cdb-stat cdb-stat-open">
          <span className="cdb-stat-value">{stats.open}</span>
          <span className="cdb-stat-label">Đang mở</span>
        </div>
        <div className="cdb-stat cdb-stat-closed">
          <span className="cdb-stat-value">{stats.closed}</span>
          <span className="cdb-stat-label">Đã đóng</span>
        </div>
        <div className="cdb-stat cdb-stat-unread">
          <span className="cdb-stat-value">{stats.unread}</span>
          <span className="cdb-stat-label">Tin chưa đọc</span>
        </div>
      </div>

      {error ? (
        <p role="alert" className="form-error cdb-alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      {showCreate ? (
        <form onSubmit={handleCreate} className="entity-form cdb-create">
          <div className="card-head">
            <h2>
              <Icon name="plus" size={16} /> Tạo luồng trao đổi mới
            </h2>
            <p>
              Đặt tiêu đề rõ ràng theo nội dung / mốc thời gian để dễ tra cứu về sau (VD: “Báo cáo
              SSCĐ tuần 36/2026”).
            </p>
          </div>
          <label>
            Tiêu đề luồng
            <input
              type="text"
              placeholder="VD: Báo cáo SSCĐ tuần 36/2026"
              maxLength={255}
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              required
            />
          </label>
          {isCommander ? (
            <label>
              Đơn vị
              <select value={newUnitId} onChange={(e) => setNewUnitId(e.target.value)} required>
                <option value="">— Chọn đơn vị —</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="state-note">
              Luồng sẽ gắn với đơn vị của bạn và hiển thị cho Ban chỉ huy Lữ đoàn.
            </p>
          )}
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={creating || !canSubmitNew}>
              {creating ? 'Đang tạo...' : 'Tạo luồng'}
            </button>
            <button
              type="button"
              className="btn-cancel"
              onClick={() => setShowCreate(false)}
              disabled={creating}
            >
              Huỷ
            </button>
          </div>
        </form>
      ) : null}

      <div className="cdb-grid">
        <aside className="cdb-sidebar">
          <div className="cdb-toolbar">
            <div className="cdb-search">
              <Icon name="search" size={14} />
              <input
                type="search"
                placeholder="Tìm theo tiêu đề, đơn vị, người tạo..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="cdb-toolbar-row">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                aria-label="Lọc theo trạng thái"
              >
                <option value="">Mọi trạng thái</option>
                <option value="open">Đang mở</option>
                <option value="closed">Đã đóng</option>
              </select>
              {isCommander ? (
                <select
                  value={unitFilter}
                  onChange={(e) => setUnitFilter(e.target.value)}
                  aria-label="Lọc theo đơn vị"
                >
                  <option value="">Mọi đơn vị</option>
                  {units.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name}
                    </option>
                  ))}
                </select>
              ) : null}
              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as SortMode)}
                aria-label="Sắp xếp"
              >
                <option value="recent">Mới nhất</option>
                <option value="unread">Chưa đọc nhiều</option>
                <option value="title">Theo tên A→Z</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="cdb-skeleton-list">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="cdb-skeleton-row" />
              ))}
            </div>
          ) : threads.length === 0 ? (
            <EmptyState icon="clipboard" message="Chưa có luồng trao đổi nào." />
          ) : total === 0 ? (
            <EmptyState icon="search" message="Không có luồng nào khớp bộ lọc / từ khoá." />
          ) : (
            <>
              <ul className="cdb-thread-list">
                {pageItems.map((t) => (
                  <li key={t.id}>
                    <button
                      type="button"
                      className={
                        t.id === activeId ? 'cdb-thread active' : 'cdb-thread'
                      }
                      onClick={() => openThread(t.id)}
                    >
                      <span className="cdb-thread-top">
                        <span className="cdb-thread-title">{t.title}</span>
                        {t.unread_count > 0 ? (
                          <span className="badge-unread">{t.unread_count}</span>
                        ) : null}
                      </span>
                      <span className="cdb-thread-tags">
                        <span className="chip chip-role">{t.unit_name}</span>
                        <span className={t.is_closed ? 'chip chip-off' : 'chip chip-ok'}>
                          {t.is_closed ? 'Đã đóng' : 'Đang mở'}
                        </span>
                      </span>
                      <span className="cdb-thread-meta">
                        <Icon name="send" size={11} /> {t.message_count} tin ·{' '}
                        {relTime(t.last_message_at)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
              <Pagination
                page={safePage}
                pageCount={pageCount}
                total={total}
                pageSize={pageSize}
                onPage={setPage}
                onPageSize={setPageSize}
                pageSizeOptions={PAGE_SIZE_OPTIONS}
                itemLabel="luồng"
              />
            </>
          )}
        </aside>

        <div className="cdb-conversation">
          {!activeId ? (
            <div className="cdb-conv-empty">
              <Icon name="clipboard" size={44} />
              <p>Chọn một luồng ở danh sách bên trái để xem nội dung trao đổi.</p>
            </div>
          ) : detailLoading && !detail ? (
            <div className="cdb-conv-empty">
              <p>Đang mở luồng...</p>
            </div>
          ) : detail ? (
            <>
              <div className="cdb-conv-head">
                <div className="cdb-conv-title">
                  <h2>{detail.title}</h2>
                  <div className="cdb-conv-sub">
                    <span className="chip chip-role">{detail.unit_name}</span>
                    <span className={detail.is_closed ? 'chip chip-off' : 'chip chip-ok'}>
                      {detail.is_closed ? 'Đã đóng' : 'Đang mở'}
                    </span>
                    <span className="cdb-conv-by">
                      <Icon name="user" size={11} /> {detail.created_by_full_name} · mở lúc{' '}
                      {when(detail.created_at)}
                    </span>
                  </div>
                </div>
                <div className="cdb-conv-actions">
                  <button
                    type="button"
                    className="btn-cancel"
                    onClick={() => openThread(detail.id)}
                    disabled={detailLoading}
                    title="Tải lại nội dung luồng"
                  >
                    <Icon name="undo" size={14} /> Làm mới
                  </button>
                  {isCommander ? (
                    <button
                      type="button"
                      className={detail.is_closed ? 'btn-submit' : 'btn-cancel'}
                      onClick={toggleClose}
                    >
                      {detail.is_closed ? (
                        <>
                          <Icon name="undo" size={14} /> Mở lại luồng
                        </>
                      ) : (
                        <>
                          <Icon name="lock" size={14} /> Đóng luồng
                        </>
                      )}
                    </button>
                  ) : null}
                </div>
              </div>

              <div className="cdb-messages">
                {detail.messages.length === 0 ? (
                  <p className="state-note cdb-msg-empty">
                    Chưa có tin nhắn. Hãy gửi nội dung trao đổi / báo cáo đầu tiên.
                  </p>
                ) : (
                  detail.messages.map((m, idx) => {
                    const prev = detail.messages[idx - 1]
                    const showDay =
                      !prev ||
                      new Date(prev.created_at).toDateString() !==
                        new Date(m.created_at).toDateString()
                    const own = m.sender_id === userId
                    return (
                      <div key={m.id}>
                        {showDay ? (
                          <div className="cdb-day-sep">
                            <span>{dayLabel(m.created_at)}</span>
                          </div>
                        ) : null}
                        <div className={own ? 'cdb-msg own' : 'cdb-msg'}>
                          {!own ? (
                            <span
                              className="cdb-avatar"
                              style={{ background: colorFor(m.sender_full_name) }}
                            >
                              {initials(m.sender_full_name)}
                            </span>
                          ) : null}
                          <div className="cdb-bubble">
                            <div className="cdb-bubble-head">
                              <strong>{own ? 'Bạn' : m.sender_full_name}</strong>
                              <span>{timeOnly(m.created_at)}</span>
                            </div>
                            {m.body ? <p className="cdb-bubble-body">{m.body}</p> : null}
                            {m.attachment_url ? (
                              <a
                                className="cdb-attach"
                                href={fileUrl(m.attachment_url)}
                                target="_blank"
                                rel="noreferrer"
                              >
                                <Icon name="file" size={14} /> Tệp đính kèm
                                <Icon name="download" size={12} />
                              </a>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    )
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {detail.is_closed ? (
                <p className="state-note cdb-closed-note">
                  <Icon name="lock" size={13} /> Luồng đã đóng — không thể gửi thêm tin.
                  {isCommander ? ' Bấm “Mở lại luồng” nếu cần tiếp tục trao đổi.' : ''}
                </p>
              ) : (
                <form onSubmit={handleSend} className="cdb-composer">
                  <textarea
                    ref={textareaRef}
                    rows={1}
                    maxLength={5000}
                    placeholder="Nhập nội dung trao đổi / báo cáo...  (Ctrl + Enter để gửi)"
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    onKeyDown={onComposerKey}
                  />
                  {file ? (
                    <div className="cdb-file-chip">
                      <Icon name="file" size={13} /> <span>{file.name}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setFile(null)
                          if (fileRef.current) fileRef.current.value = ''
                        }}
                        aria-label="Bỏ tệp đính kèm"
                      >
                        <Icon name="x" size={12} />
                      </button>
                    </div>
                  ) : null}
                  <div className="cdb-composer-bar">
                    <label className="cdb-attach-btn">
                      <Icon name="upload" size={15} /> Đính kèm tệp
                      <input
                        ref={fileRef}
                        type="file"
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                      />
                    </label>
                    <span className="cdb-char">{body.length}/5000</span>
                    <button
                      type="submit"
                      className="btn-submit"
                      disabled={sending || (!body.trim() && !file)}
                    >
                      <Icon name="send" size={14} /> {sending ? 'Đang gửi...' : 'Gửi'}
                    </button>
                  </div>
                </form>
              )}
            </>
          ) : (
            <div className="cdb-conv-empty">
              <p>Không mở được luồng.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
