import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { directivesApi } from '../api/directives'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { useAuth } from '../context/AuthContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import {
  DIRECTIVE_STATUS_LABELS,
  type Directive,
  type DirectiveAckReport,
  type DirectiveCreate,
  type DirectiveStatus,
} from '../types/directive'

const statuses = Object.keys(DIRECTIVE_STATUS_LABELS) as DirectiveStatus[]
const emptyForm: DirectiveCreate = { title: '', content: '', status: 'nhap', classification: 'noi_bo' }

const ROLE_LABELS: Record<string, string> = {
  commander: 'Chỉ huy',
  officer: 'Cán bộ',
  soldier: 'Chiến sĩ',
}

function formatDateTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('vi-VN') : '—'
}

export function DirectivesPage() {
  const { isCommander } = useAuth()

  const [directives, setDirectives] = useState<Directive[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<DirectiveStatus | ''>('')

  const [form, setForm] = useState<DirectiveCreate>(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)

  const [ackingId, setAckingId] = useState<number | null>(null)
  const [reports, setReports] = useState<Record<number, DirectiveAckReport>>({})
  const [openReportId, setOpenReportId] = useState<number | null>(null)

  // Tu dong luu ban nhap chi thi dang soan (tranh mat noi dung khi tai lai
  // trang / mat dien, mat mang LAN dot ngot truoc khi ban hanh).
  const { clearDraft } = useDraftAutosave(
    showForm ? `directive:${editingId !== null ? `edit:${editingId}` : 'new'}` : null,
    form,
    setForm,
    { isEmpty: (f) => !f.title.trim() && !f.content.trim() },
  )

  function loadDirectives() {
    setLoading(true)
    directivesApi
      .list(isCommander && filterStatus ? { status: filterStatus } : undefined)
      .then(setDirectives)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải chỉ thị – nhiệm vụ'),
      )
      .finally(() => setLoading(false))
  }

  useEffect(loadDirectives, [filterStatus, isCommander])

  function startCreate() {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  function startEdit(directive: Directive) {
    setEditingId(directive.id)
    setForm({
      title: directive.title,
      content: directive.content,
      status: directive.status,
      classification: directive.classification,
    })
    setShowForm(true)
  }

  function cancelForm() {
    clearDraft()
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (editingId !== null) {
        const updated = await directivesApi.update(editingId, form)
        setDirectives((prev) => prev.map((d) => (d.id === editingId ? updated : d)))
      } else {
        const created = await directivesApi.create(form)
        setDirectives((prev) => [created, ...prev])
      }
      cancelForm()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu chỉ thị')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    setError(null)
    try {
      await directivesApi.remove(id)
      setDirectives((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá chỉ thị')
    }
  }

  async function handleAcknowledge(id: number) {
    setError(null)
    setAckingId(id)
    try {
      const updated = await directivesApi.acknowledge(id)
      setDirectives((prev) => prev.map((d) => (d.id === id ? updated : d)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xác nhận tiếp thu')
    } finally {
      setAckingId(null)
    }
  }

  async function toggleReport(id: number) {
    if (openReportId === id) {
      setOpenReportId(null)
      return
    }
    setOpenReportId(id)
    if (!reports[id]) {
      try {
        const report = await directivesApi.acknowledgements(id)
        setReports((prev) => ({ ...prev, [id]: report }))
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách quán triệt')
        setOpenReportId(null)
      }
    }
  }

  return (
    <section>
      <h1>Chỉ thị – Nhiệm vụ</h1>

      <div className="post-toolbar">
        {isCommander ? (
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as DirectiveStatus | '')}
          >
            <option value="">Tất cả trạng thái</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {DIRECTIVE_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        ) : (
          <span />
        )}

        {isCommander && !showForm ? (
          <button type="button" onClick={startCreate}>
            Ban hành chỉ thị mới
          </button>
        ) : null}
      </div>

      {showForm ? (
        <form onSubmit={handleSubmit} className="entity-form">
          <label>
            Tiêu đề
            <input
              type="text"
              maxLength={255}
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              required
            />
          </label>
          <label>
            Trạng thái
            <select
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as DirectiveStatus }))}
            >
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {DIRECTIVE_STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Bậc truy cập
            <select
              value={form.classification}
              onChange={(e) =>
                setForm((f) => ({ ...f, classification: e.target.value as Classification }))
              }
            >
              {CLASSIFICATION_ORDER.map((c) => (
                <option key={c} value={c}>
                  {CLASSIFICATION_LABELS[c]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nội dung
            <textarea
              rows={6}
              value={form.content}
              onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
              required
            />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {editingId !== null ? 'Cập nhật' : 'Ban hành'}
            </button>
            <button type="button" onClick={cancelForm}>
              Huỷ
            </button>
          </div>
        </form>
      ) : null}

      {error ? <p role="alert" className="form-error">{error}</p> : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : directives.length === 0 ? (
        <p>Chưa có chỉ thị – nhiệm vụ nào.</p>
      ) : (
        <div className="post-list">
          {directives.map((directive) => {
            const report = reports[directive.id]
            return (
              <article key={directive.id} className="post-card">
                <div className="post-card-body">
                  <div className="badge-row">
                    <span className={`status-badge status-${directive.status}`}>
                      {DIRECTIVE_STATUS_LABELS[directive.status]}
                    </span>
                    <ClassificationBadge value={directive.classification} />
                  </div>
                  <h2>{directive.title}</h2>
                  <p className="post-meta">
                    Ban hành bởi {directive.author_full_name} ·{' '}
                    {new Date(directive.created_at).toLocaleDateString('vi-VN')}
                  </p>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{directive.content}</p>

                  {directive.status === 'da_ban_hanh' ? (
                    <div className="directive-ack-bar">
                      <button
                        type="button"
                        disabled={directive.acknowledged_by_me || ackingId === directive.id}
                        onClick={() => handleAcknowledge(directive.id)}
                      >
                        {directive.acknowledged_by_me ? 'Đã tiếp thu' : 'Xác nhận đã tiếp thu'}
                      </button>
                      <span>
                        {directive.acknowledged_count}/{directive.recipient_count} đã quán triệt
                      </span>
                    </div>
                  ) : null}

                  {isCommander ? (
                    <div className="row-actions">
                      <button type="button" onClick={() => startEdit(directive)}>
                        Sửa
                      </button>
                      <button type="button" onClick={() => handleDelete(directive.id)}>
                        Xoá
                      </button>
                      {directive.status === 'da_ban_hanh' ? (
                        <button type="button" onClick={() => toggleReport(directive.id)}>
                          {openReportId === directive.id ? 'Ẩn danh sách quán triệt' : 'Danh sách quán triệt'}
                        </button>
                      ) : null}
                    </div>
                  ) : null}

                  {isCommander && openReportId === directive.id ? (
                    !report ? (
                      <p className="state-note">Đang tải danh sách...</p>
                    ) : (
                      <div className="ack-report">
                        <p className="post-meta">
                          Đã tiếp thu {report.acknowledged_count}/{report.recipient_count}
                        </p>
                        <div className="ack-columns">
                          <div>
                            <h4 className="ack-done">Đã tiếp thu ({report.acknowledged.length})</h4>
                            {report.acknowledged.length === 0 ? (
                              <p className="state-note">Chưa có ai.</p>
                            ) : (
                              <ul>
                                {report.acknowledged.map((u) => (
                                  <li key={u.user_id}>
                                    {u.full_name} · {ROLE_LABELS[u.role] ?? u.role} ·{' '}
                                    {formatDateTime(u.acknowledged_at)}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                          <div>
                            <h4 className="ack-todo">Chưa tiếp thu ({report.pending.length})</h4>
                            {report.pending.length === 0 ? (
                              <p className="state-note">Tất cả đã tiếp thu.</p>
                            ) : (
                              <ul>
                                {report.pending.map((u) => (
                                  <li key={u.user_id}>
                                    {u.full_name} · {ROLE_LABELS[u.role] ?? u.role}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  ) : null}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
