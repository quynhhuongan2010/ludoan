import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { directivesApi } from '../api/directives'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import { useRequiredFields } from '../hooks/useRequiredFields'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import {
  DIRECTIVE_STATUS_LABELS,
  type DirectiveCreate,
  type DirectiveStatus,
} from '../types/directive'

const statuses = Object.keys(DIRECTIVE_STATUS_LABELS) as DirectiveStatus[]
const emptyForm: DirectiveCreate = { title: '', content: '', status: 'nhap', classification: 'noi_bo' }

const LIST_PATH = '/chi-thi-nhiem-vu'

export function DirectiveFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const editingId = id ? Number(id) : null

  const [form, setForm] = useState<DirectiveCreate>(emptyForm)
  const [loading, setLoading] = useState(editingId !== null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const req = useRequiredFields(['title', 'content'] as const)

  const { clearDraft } = useDraftAutosave(
    `directive:${editingId !== null ? `edit:${editingId}` : 'new'}`,
    form,
    setForm,
    { isEmpty: (f) => !f.title.trim() && !f.content.trim() },
  )

  useEffect(() => {
    if (editingId === null) return
    setLoading(true)
    directivesApi
      .get(editingId)
      .then((d) =>
        setForm({
          title: d.title,
          content: d.content,
          status: d.status,
          classification: d.classification,
        }),
      )
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải chỉ thị'),
      )
      .finally(() => setLoading(false))
  }, [editingId])

  function goBack() {
    navigate(LIST_PATH)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ title: form.title, content: form.content })) return
    setSubmitting(true)
    try {
      if (editingId !== null) {
        await directivesApi.update(editingId, form)
      } else {
        await directivesApi.create(form)
      }
      clearDraft()
      goBack()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu chỉ thị')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section>
      <div className="page-head">
        <h1>{editingId !== null ? 'Sửa chỉ thị – nhiệm vụ' : 'Ban hành chỉ thị mới'}</h1>
        <button type="button" className="btn-back" onClick={goBack}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
      </div>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <form onSubmit={handleSubmit} className="entity-form">
          <Field label="Tiêu đề" required req={req} name="title">
            <input
              type="text"
              maxLength={255}
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              onBlur={(e) => req.mark('title', e.target.value)}
              required
            />
          </Field>
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
          <Field label="Nội dung" required req={req} name="content">
            <textarea
              rows={6}
              value={form.content}
              onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
              onBlur={(e) => req.mark('content', e.target.value)}
              required
            />
          </Field>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={submitting}>
              {submitting ? 'Đang lưu...' : editingId !== null ? 'Cập nhật' : 'Ban hành'}
            </button>
            <button type="button" className="btn-cancel" onClick={goBack}>
              Huỷ
            </button>
          </div>
        </form>
      )}
    </section>
  )
}
