import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ComponentProps,
  type FormEvent,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { directiveAssignmentsApi } from '../api/directiveAssignments'
import { unitsApi } from '../api/units'
import { EmptyState } from '../components/EmptyState'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import { useRequiredFields } from '../hooks/useRequiredFields'
import {
  ASSIGNMENT_STATUS_LABELS,
  TARGET_STATUS_LABELS,
  type AssignmentTarget,
  type DirectiveAssignment,
  type DirectiveAssignmentDetail,
  type ReviewResult,
} from '../types/directiveAssignment'
import type { Unit } from '../types/unit'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const fileUrl = (url: string | null) =>
  url && url.startsWith('/static') ? `${API_BASE}${url}` : url ?? ''

const PAGE_SIZE_OPTIONS = [8, 15, 30]
type SortMode = 'recent' | 'due' | 'progress'

function fmtDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString('vi-VN') : '—'
}
function fmtDateTime(iso: string | null): string {
  return iso
    ? new Date(iso).toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''
}
/** So ngay con lai (am = da qua han). Null neu khong co han. */
function daysLeft(iso: string | null): number | null {
  if (!iso) return null
  const due = new Date(iso)
  due.setHours(23, 59, 59, 999)
  return Math.ceil((due.getTime() - Date.now()) / 86400000)
}

function AutoTextarea(props: ComponentProps<'textarea'>) {
  const ref = useRef<HTMLTextAreaElement | null>(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`
  }, [props.value])
  return <textarea ref={ref} {...props} />
}

function Progress({ value, total }: { value: number; total: number }) {
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

function DueBadge({ due, done }: { due: string | null; done: boolean }) {
  if (!due) return <span className="gnv-due">Không có hạn</span>
  const d = daysLeft(due)
  if (done) return <span className="gnv-due">Hạn {fmtDate(due)}</span>
  if (d != null && d < 0)
    return <span className="gnv-due overdue">Quá hạn {Math.abs(d)} ngày</span>
  if (d != null && d <= 2)
    return <span className="gnv-due soon">Còn {d} ngày · {fmtDate(due)}</span>
  return <span className="gnv-due">Hạn {fmtDate(due)}</span>
}

export function GiaoNhiemVuPage() {
  const navigate = useNavigate()
  const { isCommander, userId, unitId } = useAuth()
  const confirm = useConfirm()

  const [list, setList] = useState<DirectiveAssignment[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<DirectiveAssignmentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form giao nhiem vu (chi huy)
  const [showCreate, setShowCreate] = useState(false)
  const [cTitle, setCTitle] = useState('')
  const [cDesc, setCDesc] = useState('')
  const [cDue, setCDue] = useState('')
  const [cUnits, setCUnits] = useState<number[]>([])
  const req = useRequiredFields(['title'] as const)
  const [creating, setCreating] = useState(false)

  // Loc / sap xep / phan trang danh sach (client-side)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('recent')
  const [pageSize, setPageSize] = useState(8)
  const [page, setPage] = useState(0)

  const cDraft = useMemo(() => ({ title: cTitle, desc: cDesc, due: cDue }), [cTitle, cDesc, cDue])
  function setCDraft(v: { title: string; desc: string; due: string }) {
    setCTitle(v.title)
    setCDesc(v.desc)
    setCDue(v.due)
  }
  const { clearDraft: clearCreateDraft } = useDraftAutosave(
    isCommander ? 'giaonv:new' : null,
    cDraft,
    setCDraft,
    { isEmpty: (v) => !v.title.trim() && !v.desc.trim() },
  )

  function reload() {
    setLoading(true)
    Promise.all([
      directiveAssignmentsApi.list({ limit: 500 }),
      isCommander ? unitsApi.list({ active: true }) : Promise.resolve<Unit[]>([]),
    ])
      .then(([ls, us]) => {
        setList(ls)
        setUnits(us)
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không tải được danh sách nhiệm vụ'),
      )
      .finally(() => setLoading(false))
  }
  useEffect(reload, [isCommander])

  function openDetail(id: number) {
    setActiveId(id)
    setDetailLoading(true)
    directiveAssignmentsApi
      .get(id)
      .then(setDetail)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không mở được nhiệm vụ'),
      )
      .finally(() => setDetailLoading(false))
  }

  function refreshDetail() {
    if (activeId != null) openDetail(activeId)
    reload()
  }

  function isMine(t: AssignmentTarget): boolean {
    if (t.assignee_id != null) return t.assignee_id === userId
    return t.unit_id === unitId
  }

  const stats = useMemo(() => {
    const s = { total: list.length, doing: 0, done: 0, overdue: 0 }
    for (const a of list) {
      if (a.status === 'dang_thuc_hien' || a.status === 'chua_giao') s.doing += 1
      else if (a.status === 'hoan_thanh') s.done += 1
      else if (a.status === 'qua_han') s.overdue += 1
    }
    return s
  }, [list])

  const visible = useMemo(() => {
    const kw = search.trim().toLowerCase()
    const rows = list.filter((a) => {
      if (statusFilter && a.status !== statusFilter) return false
      if (!kw) return true
      return (
        a.title.toLowerCase().includes(kw) ||
        (a.directive_title ?? '').toLowerCase().includes(kw) ||
        (a.created_by_full_name ?? '').toLowerCase().includes(kw)
      )
    })
    rows.sort((a, b) => {
      if (sortMode === 'due') {
        const da = a.due_date ? new Date(a.due_date).getTime() : Infinity
        const db = b.due_date ? new Date(b.due_date).getTime() : Infinity
        return da - db
      }
      if (sortMode === 'progress') {
        const pa = a.target_count ? a.approved_count / a.target_count : 0
        const pb = b.target_count ? b.approved_count / b.target_count : 0
        return pa - pb
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
    return rows
  }, [list, search, statusFilter, sortMode])

  const total = visible.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const pageItems = visible.slice(safePage * pageSize, safePage * pageSize + pageSize)

  useEffect(() => {
    setPage(0)
  }, [search, statusFilter, sortMode, pageSize])

  const allUnitsSelected = units.length > 0 && cUnits.length === units.length

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ title: cTitle })) return
    setCreating(true)
    try {
      const created = await directiveAssignmentsApi.create({
        title: cTitle.trim(),
        description: cDesc.trim() || null,
        due_date: cDue || null,
        targets: cUnits.map((u) => ({ unit_id: u })),
      })
      setCTitle('')
      setCDesc('')
      setCDue('')
      setCUnits([])
      clearCreateDraft()
      setShowCreate(false)
      reload()
      setActiveId(created.id)
      setDetail(created)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tạo được nhiệm vụ')
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete() {
    if (!detail) return
    const ok = await confirm({
      title: 'Xác nhận huỷ nhiệm vụ',
      confirmText: 'Huỷ nhiệm vụ',
      cancelText: 'Không',
      message: (
        <>
          Huỷ nhiệm vụ <strong>{detail.title}</strong>? Toàn bộ giao việc và báo cáo liên quan sẽ bị
          xoá.
        </>
      ),
    })
    if (!ok) return
    try {
      await directiveAssignmentsApi.remove(detail.id)
      setActiveId(null)
      setDetail(null)
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không huỷ được nhiệm vụ')
    }
  }

  return (
    <section className="gnv-page">
      <div className="crumb-bar">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Điều hành – Nhiệm vụ</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">Giao nhiệm vụ &amp; Báo cáo tiến độ</span>
        </nav>
      </div>

      <header className="cdb-head">
        <div>
          <h1>
            <Icon name="clipboard" size={22} /> Giao nhiệm vụ &amp; Báo cáo tiến độ
          </h1>
          <p className="state-note">
            <Icon name="lock" size={12} /> Chỉ Ban chỉ huy giao / sửa / huỷ nhiệm vụ và duyệt báo
            cáo. Đơn vị được giao nộp báo cáo tiến độ kèm tệp minh chứng.
          </p>
        </div>
        <div className="cdb-head-actions">
          <button type="button" className="btn-cancel" onClick={reload} disabled={loading}>
            <Icon name="undo" size={14} /> Làm mới
          </button>
          {isCommander ? (
            <button type="button" className="btn-create" onClick={() => setShowCreate((v) => !v)}>
              <Icon name="plus" size={16} /> Giao nhiệm vụ
            </button>
          ) : null}
        </div>
      </header>

      <div className="cdb-stats">
        <div className="cdb-stat">
          <span className="cdb-stat-value">{stats.total}</span>
          <span className="cdb-stat-label">Tổng nhiệm vụ</span>
        </div>
        <div className="cdb-stat cdb-stat-open">
          <span className="cdb-stat-value">{stats.doing}</span>
          <span className="cdb-stat-label">Đang thực hiện</span>
        </div>
        <div className="cdb-stat cdb-stat-done">
          <span className="cdb-stat-value">{stats.done}</span>
          <span className="cdb-stat-label">Hoàn thành</span>
        </div>
        <div className="cdb-stat cdb-stat-unread">
          <span className="cdb-stat-value">{stats.overdue}</span>
          <span className="cdb-stat-label">Quá hạn</span>
        </div>
      </div>

      {error ? (
        <p role="alert" className="form-error cdb-alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      {isCommander && showCreate ? (
        <form onSubmit={handleCreate} className="entity-form cdb-create">
          <div className="card-head">
            <h2>
              <Icon name="plus" size={16} /> Giao nhiệm vụ mới
            </h2>
            <p>Chọn một hoặc nhiều đơn vị nhận nhiệm vụ. Mỗi đơn vị nộp báo cáo tiến độ riêng.</p>
          </div>
          <Field label="Tiêu đề" required req={req} name="title">
            <input
              type="text"
              maxLength={255}
              placeholder="VD: Rà soát, củng cố hệ thống thông tin quý IV"
              value={cTitle}
              onChange={(e) => setCTitle(e.target.value)}
              onBlur={(e) => req.mark('title', e.target.value)}
              required
            />
          </Field>
          <label>
            Mô tả / yêu cầu
            <AutoTextarea
              rows={3}
              placeholder="Nội dung, yêu cầu cụ thể, sản phẩm cần nộp..."
              value={cDesc}
              onChange={(e) => setCDesc(e.target.value)}
            />
          </label>
          <div className="gnv-create-row">
            <label>
              Hạn nộp
              <input type="date" value={cDue} onChange={(e) => setCDue(e.target.value)} />
            </label>
          </div>
          <fieldset className="gnv-unit-picker">
            <legend>
              Giao cho đơn vị
              {cUnits.length > 0 ? <span className="gnv-count">Đã chọn {cUnits.length}</span> : null}
            </legend>
            <div className="gnv-unit-tools">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setCUnits(allUnitsSelected ? [] : units.map((u) => u.id))}
              >
                {allUnitsSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
              </button>
            </div>
            <div className="gnv-unit-grid">
              {units.map((u) => (
                <label key={u.id} className="gnv-unit-cell">
                  <input
                    type="checkbox"
                    checked={cUnits.includes(u.id)}
                    onChange={(e) =>
                      setCUnits((prev) =>
                        e.target.checked ? [...prev, u.id] : prev.filter((x) => x !== u.id),
                      )
                    }
                  />
                  <span>{u.name}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={creating || cUnits.length === 0}>
              {creating ? 'Đang giao...' : 'Giao nhiệm vụ'}
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
                placeholder="Tìm theo tiêu đề, chỉ thị, người giao..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="cdb-toolbar-row">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Lọc theo trạng thái"
              >
                <option value="">Mọi trạng thái</option>
                {(Object.keys(ASSIGNMENT_STATUS_LABELS) as (keyof typeof ASSIGNMENT_STATUS_LABELS)[]).map(
                  (s) => (
                    <option key={s} value={s}>
                      {ASSIGNMENT_STATUS_LABELS[s]}
                    </option>
                  ),
                )}
              </select>
              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as SortMode)}
                aria-label="Sắp xếp"
              >
                <option value="recent">Mới nhất</option>
                <option value="due">Hạn gần nhất</option>
                <option value="progress">Tiến độ thấp trước</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="cdb-skeleton-list">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="cdb-skeleton-row" />
              ))}
            </div>
          ) : list.length === 0 ? (
            <EmptyState icon="clipboard" message="Chưa có nhiệm vụ nào." />
          ) : total === 0 ? (
            <EmptyState icon="search" message="Không có nhiệm vụ nào khớp bộ lọc / từ khoá." />
          ) : (
            <>
              <ul className="cdb-thread-list">
                {pageItems.map((a) => {
                  const done = a.status === 'hoan_thanh'
                  return (
                    <li key={a.id}>
                      <button
                        type="button"
                        className={a.id === activeId ? 'cdb-thread active' : 'cdb-thread'}
                        onClick={() => openDetail(a.id)}
                      >
                        <span className="cdb-thread-top">
                          <span className="cdb-thread-title">{a.title}</span>
                          <span className={`status-chip st-${a.status}`}>
                            {ASSIGNMENT_STATUS_LABELS[a.status]}
                          </span>
                        </span>
                        <Progress value={a.approved_count} total={a.target_count} />
                        <span className="cdb-thread-meta">
                          <Icon name="check" size={11} /> {a.approved_count}/{a.target_count} đơn vị
                          duyệt
                        </span>
                        <span className="cdb-thread-meta">
                          <Icon name="clock" size={11} /> <DueBadge due={a.due_date} done={done} />
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
                itemLabel="nhiệm vụ"
              />
            </>
          )}
        </aside>

        <div className="cdb-conversation gnv-detail">
          {!activeId ? (
            <div className="cdb-conv-empty">
              <Icon name="clipboard" size={44} />
              <p>Chọn một nhiệm vụ ở danh sách bên trái để xem chi tiết và tiến độ.</p>
            </div>
          ) : detailLoading && !detail ? (
            <div className="cdb-conv-empty">
              <p>Đang mở nhiệm vụ...</p>
            </div>
          ) : detail ? (
            <AssignmentDetailView
              detail={detail}
              isCommander={isCommander}
              isMine={isMine}
              onChanged={refreshDetail}
              onDelete={handleDelete}
              setError={setError}
            />
          ) : (
            <div className="cdb-conv-empty">
              <p>Không mở được nhiệm vụ.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

function AssignmentDetailView({
  detail,
  isCommander,
  isMine,
  onChanged,
  onDelete,
  setError,
}: {
  detail: DirectiveAssignmentDetail
  isCommander: boolean
  isMine: (t: AssignmentTarget) => boolean
  onChanged: () => void
  onDelete: () => void
  setError: (m: string | null) => void
}) {
  const [expanded, setExpanded] = useState<number | null>(null)

  const counts = useMemo(() => {
    const c = { approved: 0, pending: 0, returned: 0, notSubmitted: 0 }
    for (const t of detail.targets) {
      if (t.status === 'da_duyet') c.approved += 1
      else if (t.status === 'cho_duyet') c.pending += 1
      else if (t.status === 'tra_lai') c.returned += 1
      else c.notSubmitted += 1
    }
    return c
  }, [detail.targets])

  const done = detail.status === 'hoan_thanh'

  return (
    <>
      <div className="cdb-conv-head gnv-conv-head">
        <div className="cdb-conv-title">
          <h2>{detail.title}</h2>
          <div className="cdb-conv-sub">
            <span className={`status-chip st-${detail.status}`}>
              {ASSIGNMENT_STATUS_LABELS[detail.status]}
            </span>
            <DueBadge due={detail.due_date} done={done} />
            <span className="cdb-conv-by">
              <Icon name="user" size={11} /> {detail.created_by_full_name}
            </span>
            {detail.directive_title ? (
              <span className="cdb-conv-by">
                <Icon name="link" size={11} /> Chỉ thị: {detail.directive_title}
              </span>
            ) : null}
          </div>
        </div>
        {isCommander ? (
          <div className="cdb-conv-actions">
            <button type="button" className="btn-delete" onClick={onDelete}>
              <Icon name="trash" size={13} /> Huỷ nhiệm vụ
            </button>
          </div>
        ) : null}
      </div>

      <div className="gnv-detail-body">
        {detail.description ? <p className="gnv-desc">{detail.description}</p> : null}

        <div className="gnv-summary">
          <div className="gnv-summary-head">
            <strong>Tiến độ duyệt</strong>
            <span>
              {detail.approved_count}/{detail.target_count} đơn vị
            </span>
          </div>
          <Progress value={detail.approved_count} total={detail.target_count} />
          <div className="gnv-summary-chips">
            <span className="chip chip-ok">Đã duyệt {counts.approved}</span>
            <span className="chip chip-mat">Chờ duyệt {counts.pending}</span>
            <span className="chip chip-off">Trả lại {counts.returned}</span>
            <span className="chip">Chưa nộp {counts.notSubmitted}</span>
          </div>
        </div>

        <div className="gnv-targets">
          {detail.targets.length === 0 ? (
            <p className="state-note">Chưa giao cho đơn vị nào.</p>
          ) : (
            detail.targets.map((t) => (
              <TargetCard
                key={t.id}
                assignmentId={detail.id}
                target={t}
                mine={isMine(t)}
                isCommander={isCommander}
                expanded={expanded === t.id}
                onToggle={() => setExpanded((e) => (e === t.id ? null : t.id))}
                onChanged={onChanged}
                setError={setError}
              />
            ))
          )}
        </div>
      </div>
    </>
  )
}

function TargetCard({
  assignmentId,
  target,
  mine,
  isCommander,
  expanded,
  onToggle,
  onChanged,
  setError,
}: {
  assignmentId: number
  target: AssignmentTarget
  mine: boolean
  isCommander: boolean
  expanded: boolean
  onToggle: () => void
  onChanged: () => void
  setError: (m: string | null) => void
}) {
  const [content, setContent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewResult, setReviewResult] = useState<ReviewResult>('da_duyet')
  const [reviewNote, setReviewNote] = useState('')
  const fileRef = useRef<HTMLInputElement | null>(null)

  const { clearDraft } = useDraftAutosave(
    `giaonv:submit:${assignmentId}:${target.id}`,
    content,
    setContent,
  )

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!content.trim()) return
    setBusy(true)
    setError(null)
    try {
      await directiveAssignmentsApi.submit(assignmentId, target.id, content.trim(), file)
      setContent('')
      clearDraft()
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không nộp được báo cáo')
    } finally {
      setBusy(false)
    }
  }

  async function doReview(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await directiveAssignmentsApi.review(assignmentId, target.id, {
        result: reviewResult,
        review_note: reviewNote || null,
      })
      setReviewOpen(false)
      setReviewNote('')
      onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không duyệt được báo cáo')
    } finally {
      setBusy(false)
    }
  }

  const canSubmit = mine && target.status !== 'da_duyet'

  return (
    <div className={`gnv-target${expanded ? ' open' : ''}`}>
      <div className="gnv-target-head">
        <div className="gnv-target-id">
          <span className="gnv-target-unit">{target.unit_name}</span>
          <span className="gnv-target-who">
            {target.assignee_full_name ?? 'Cả đơn vị'}
            {mine ? <span className="chip chip-role">Của tôi</span> : null}
          </span>
        </div>
        <div className="gnv-target-right">
          <span className={`status-chip st-${target.status}`}>
            {TARGET_STATUS_LABELS[target.status]}
          </span>
          <span className="gnv-target-count">
            <Icon name="file" size={11} /> {target.submission_count} lần nộp
          </span>
          <button type="button" className="btn-view" onClick={onToggle}>
            <Icon name={expanded ? 'eye-off' : 'eye'} /> {expanded ? 'Ẩn' : 'Xem'}
          </button>
          {isCommander && target.status === 'cho_duyet' ? (
            <button
              type="button"
              className="btn-approve"
              onClick={() => setReviewOpen((v) => !v)}
            >
              <Icon name="check" /> Duyệt
            </button>
          ) : null}
        </div>
      </div>

      {reviewOpen ? (
        <form onSubmit={doReview} className="gnv-review">
          <div className="gnv-review-opts">
            <label className="switch-cell">
              <input
                type="radio"
                name={`rv-${target.id}`}
                checked={reviewResult === 'da_duyet'}
                onChange={() => setReviewResult('da_duyet')}
              />
              Đã duyệt
            </label>
            <label className="switch-cell">
              <input
                type="radio"
                name={`rv-${target.id}`}
                checked={reviewResult === 'tra_lai'}
                onChange={() => setReviewResult('tra_lai')}
              />
              Trả lại
            </label>
          </div>
          <input
            type="text"
            placeholder="Ghi chú duyệt / lý do trả lại"
            value={reviewNote}
            onChange={(e) => setReviewNote(e.target.value)}
            maxLength={500}
          />
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={busy}>
              Xác nhận
            </button>
            <button type="button" className="btn-cancel" onClick={() => setReviewOpen(false)}>
              Huỷ
            </button>
          </div>
        </form>
      ) : null}

      {expanded ? (
        <div className="gnv-target-body">
          {target.submissions.length === 0 ? (
            <p className="state-note">Chưa có báo cáo nào được nộp.</p>
          ) : (
            <ol className="gnv-timeline">
              {target.submissions.map((s) => (
                <li key={s.id} className="gnv-sub">
                  <div className="gnv-sub-head">
                    <strong>{s.submitted_by_full_name}</strong>
                    <span>{fmtDateTime(s.created_at)}</span>
                    {s.review_result ? (
                      <span className={`status-chip st-${s.review_result}`}>
                        {s.review_result === 'da_duyet' ? 'Đã duyệt' : 'Trả lại'}
                      </span>
                    ) : (
                      <span className="status-chip st-cho_duyet">Chờ duyệt</span>
                    )}
                  </div>
                  <p className="gnv-sub-body">{s.content}</p>
                  {s.attachment_url ? (
                    <a
                      className="cdb-attach"
                      href={fileUrl(s.attachment_url)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Icon name="file" size={14} /> Tệp minh chứng
                      <Icon name="download" size={12} />
                    </a>
                  ) : null}
                  {s.review_note ? (
                    <p className="review-note">
                      <Icon name="shield" size={12} /> Chỉ huy: {s.review_note}
                    </p>
                  ) : null}
                </li>
              ))}
            </ol>
          )}

          {canSubmit ? (
            <form onSubmit={submit} className="gnv-submit-form">
              <AutoTextarea
                rows={2}
                placeholder="Nội dung báo cáo tiến độ..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
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
                    aria-label="Bỏ tệp"
                  >
                    <Icon name="x" size={12} />
                  </button>
                </div>
              ) : null}
              <div className="cdb-composer-bar">
                <label className="cdb-attach-btn">
                  <Icon name="upload" size={15} /> Đính kèm minh chứng
                  <input
                    ref={fileRef}
                    type="file"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  />
                </label>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={busy || !content.trim()}
                >
                  <Icon name="send" size={14} /> {busy ? 'Đang nộp...' : 'Nộp báo cáo'}
                </button>
              </div>
            </form>
          ) : mine && target.status === 'da_duyet' ? (
            <p className="form-success">Báo cáo của đơn vị bạn đã được duyệt.</p>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
