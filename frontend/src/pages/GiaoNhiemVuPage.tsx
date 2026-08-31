import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { directiveAssignmentsApi } from '../api/directiveAssignments'
import { unitsApi } from '../api/units'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
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

function fmtDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString('vi-VN') : '—'
}
function fmtDateTime(iso: string | null): string {
  return iso
    ? new Date(iso).toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''
}

export function GiaoNhiemVuPage() {
  const { isCommander, userId, unitId } = useAuth()

  const [list, setList] = useState<DirectiveAssignment[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<DirectiveAssignmentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // create form (commander)
  const [cTitle, setCTitle] = useState('')
  const [cDesc, setCDesc] = useState('')
  const [cDue, setCDue] = useState('')
  const [cUnits, setCUnits] = useState<number[]>([])
  const [creating, setCreating] = useState(false)

  // Tu dong luu ban nhap "giao nhiem vu moi" (tranh mat noi dung khi tai lai
  // trang / mat dien, mat mang LAN dot ngot truoc khi giao xong).
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
      directiveAssignmentsApi.list(),
      isCommander ? unitsApi.list({ active: true }) : Promise.resolve([]),
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
    directiveAssignmentsApi
      .get(id)
      .then(setDetail)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không mở được nhiệm vụ'),
      )
  }

  function refreshDetail() {
    if (activeId != null) openDetail(activeId)
    reload()
  }

  function isMine(t: AssignmentTarget): boolean {
    if (t.assignee_id != null) return t.assignee_id === userId
    return t.unit_id === unitId
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const created = await directiveAssignmentsApi.create({
        title: cTitle,
        description: cDesc || null,
        due_date: cDue || null,
        targets: cUnits.map((u) => ({ unit_id: u })),
      })
      setCTitle('')
      setCDesc('')
      setCDue('')
      setCUnits([])
      clearCreateDraft()
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
    if (!detail || !window.confirm(`Huỷ nhiệm vụ "${detail.title}"?`)) return
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
    <section className="giao-nv-page">
      <h1>Giao nhiệm vụ &amp; Báo cáo tiến độ</h1>
      <p className="state-note">
        <Icon name="lock" size={12} /> Chỉ Ban chỉ huy giao / sửa / huỷ nhiệm vụ và duyệt báo cáo.
        Đơn vị được giao nộp báo cáo tiến độ kèm tệp minh chứng.
      </p>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {isCommander ? (
        <form onSubmit={handleCreate} className="entity-form">
          <h2>Giao nhiệm vụ mới</h2>
          <label>
            Tiêu đề
            <input
              type="text"
              maxLength={255}
              value={cTitle}
              onChange={(e) => setCTitle(e.target.value)}
              required
            />
          </label>
          <label>
            Mô tả / yêu cầu
            <textarea rows={2} value={cDesc} onChange={(e) => setCDesc(e.target.value)} />
          </label>
          <label>
            Hạn nộp
            <input type="date" value={cDue} onChange={(e) => setCDue(e.target.value)} />
          </label>
          <fieldset className="unit-picker">
            <legend>Giao cho đơn vị</legend>
            {units.map((u) => (
              <label key={u.id} className="switch-cell">
                <input
                  type="checkbox"
                  checked={cUnits.includes(u.id)}
                  onChange={(e) =>
                    setCUnits((prev) =>
                      e.target.checked ? [...prev, u.id] : prev.filter((x) => x !== u.id),
                    )
                  }
                />
                {u.name}
              </label>
            ))}
          </fieldset>
          <div className="form-actions">
            <button type="submit" disabled={creating || cUnits.length === 0}>
              Giao nhiệm vụ
            </button>
          </div>
        </form>
      ) : null}

      <div className="chi-dao-grid">
        <aside className="thread-list">
          {loading ? (
            <p>Đang tải...</p>
          ) : list.length === 0 ? (
            <p className="state-note">Chưa có nhiệm vụ nào.</p>
          ) : (
            <ul>
              {list.map((a) => (
                <li key={a.id}>
                  <button
                    type="button"
                    className={a.id === activeId ? 'thread-item active' : 'thread-item'}
                    onClick={() => openDetail(a.id)}
                  >
                    <span className="thread-title">{a.title}</span>
                    <span className="thread-meta">
                      <span className={`status-chip st-${a.status}`}>
                        {ASSIGNMENT_STATUS_LABELS[a.status]}
                      </span>{' '}
                      · {a.approved_count}/{a.target_count} duyệt · hạn {fmtDate(a.due_date)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="thread-view">
          {!detail ? (
            <p className="state-note">Chọn một nhiệm vụ để xem chi tiết.</p>
          ) : (
            <AssignmentDetailView
              detail={detail}
              isCommander={isCommander}
              isMine={isMine}
              onChanged={refreshDetail}
              onDelete={handleDelete}
              setError={setError}
            />
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

  return (
    <>
      <div className="thread-view-head">
        <div>
          <h2>{detail.title}</h2>
          <p className="thread-meta">
            <span className={`status-chip st-${detail.status}`}>
              {ASSIGNMENT_STATUS_LABELS[detail.status]}
            </span>{' '}
            · hạn nộp {fmtDate(detail.due_date)} · giao bởi {detail.created_by_full_name}
            {detail.directive_title ? ` · Chỉ thị: ${detail.directive_title}` : ''}
          </p>
          {detail.description ? <p className="msg-body">{detail.description}</p> : null}
        </div>
        {isCommander ? (
          <button type="button" onClick={onDelete}>
            Huỷ nhiệm vụ
          </button>
        ) : null}
      </div>

      <div className="message-scroll">
        <table className="users-table">
          <thead>
            <tr>
              <th>Đơn vị</th>
              <th>Phụ trách</th>
              <th>Trạng thái</th>
              <th>Lần nộp</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {detail.targets.map((t) => (
              <TargetRow
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
            ))}
          </tbody>
        </table>
        {detail.targets.length === 0 ? (
          <p className="state-note">Chưa giao cho đơn vị nào.</p>
        ) : null}
      </div>
    </>
  )
}

function TargetRow({
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

  // Tu dong luu ban nhap bao cao tien do theo tung dau muc giao nhiem vu.
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

  return (
    <>
      <tr>
        <td>{target.unit_name}</td>
        <td>{target.assignee_full_name ?? '— cả đơn vị —'}</td>
        <td>
          <span className={`status-chip st-${target.status}`}>
            {TARGET_STATUS_LABELS[target.status]}
          </span>
        </td>
        <td>{target.submission_count}</td>
        <td className="row-actions">
          <button type="button" onClick={onToggle}>
            {expanded ? 'Ẩn' : 'Xem'}
          </button>
          {isCommander && target.status === 'cho_duyet' ? (
            <button type="button" onClick={() => setReviewOpen((v) => !v)}>
              Duyệt
            </button>
          ) : null}
        </td>
      </tr>

      {reviewOpen ? (
        <tr>
          <td colSpan={5}>
            <form onSubmit={doReview} className="review-box">
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
              <input
                type="text"
                placeholder="Ghi chú duyệt / lý do trả lại"
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                maxLength={500}
              />
              <button type="submit" disabled={busy}>
                Xác nhận
              </button>
            </form>
          </td>
        </tr>
      ) : null}

      {expanded ? (
        <tr>
          <td colSpan={5}>
            <div className="submission-history">
              {target.submissions.length === 0 ? (
                <p className="state-note">Chưa có báo cáo.</p>
              ) : (
                target.submissions.map((s) => (
                  <div key={s.id} className="submission-item">
                    <div className="msg-head">
                      <strong>{s.submitted_by_full_name}</strong>{' '}
                      <span>{fmtDateTime(s.created_at)}</span>
                      {s.review_result ? (
                        <span className={`status-chip st-${s.review_result}`}>
                          {s.review_result === 'da_duyet' ? 'Đã duyệt' : 'Trả lại'}
                        </span>
                      ) : null}
                    </div>
                    <p className="msg-body">{s.content}</p>
                    {s.attachment_url ? (
                      <a href={fileUrl(s.attachment_url)} target="_blank" rel="noreferrer">
                        <Icon name="clipboard" size={12} /> Tệp minh chứng
                      </a>
                    ) : null}
                    {s.review_note ? (
                      <p className="review-note">Chỉ huy: {s.review_note}</p>
                    ) : null}
                  </div>
                ))
              )}

              {mine && target.status !== 'da_duyet' ? (
                <form onSubmit={submit} className="message-compose">
                  <textarea
                    rows={2}
                    placeholder="Nội dung báo cáo tiến độ..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                  <div className="compose-actions">
                    <input
                      type="file"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    />
                    <button type="submit" disabled={busy || !content.trim()}>
                      Nộp báo cáo
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          </td>
        </tr>
      ) : null}
    </>
  )
}
