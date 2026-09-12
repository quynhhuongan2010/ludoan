import { useEffect, useState, type FormEvent } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { documentsApi } from '../api/documents'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { REQUIRED_MESSAGE, useRequiredFields } from '../hooks/useRequiredFields'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import {
  DOCUMENT_CATEGORY_LABELS,
  type DocumentCategory,
  type DocumentFormData,
} from '../types/document'

const categories = Object.keys(DOCUMENT_CATEGORY_LABELS) as DocumentCategory[]
const emptyForm: DocumentFormData = {
  title: '',
  category: 'bieu_mau',
  description: '',
  classification: 'noi_bo',
}

const LIST_PATH = '/van-ban'

export function DocumentFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const editingId = id ? Number(id) : null
  const { role, isCommander, hasClearance } = useAuth()

  // Trang Văn bản: chỉ role 0, 1, 2 mới được tải lên / sửa tài liệu.
  const canEdit = role !== null && role <= 2

  const allowedClasses: Classification[] = CLASSIFICATION_ORDER.filter(
    (c) => c !== 'mat' || isCommander || hasClearance,
  )

  const [form, setForm] = useState<DocumentFormData>(emptyForm)
  const [file, setFile] = useState<File | null>(null)
  const [currentFileName, setCurrentFileName] = useState<string | null>(null)
  const [loading, setLoading] = useState(editingId !== null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileErr, setFileErr] = useState<string | null>(null)
  const req = useRequiredFields(['title'] as const)

  useEffect(() => {
    if (editingId === null) return
    setLoading(true)
    documentsApi
      .get(editingId)
      .then((d) => {
        setForm({
          title: d.title,
          category: d.category,
          description: d.description ?? '',
          classification: d.classification,
        })
        setCurrentFileName(d.file_name)
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải tài liệu'),
      )
      .finally(() => setLoading(false))
  }, [editingId])

  function goBack() {
    navigate(LIST_PATH)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const okTitle = req.validate({ title: form.title })
    const okFile = editingId !== null || !!file
    if (!okFile) setFileErr(REQUIRED_MESSAGE)
    if (!okTitle || !okFile) return
    setSubmitting(true)
    try {
      if (editingId !== null) {
        await documentsApi.update(editingId, form, file ?? undefined)
      } else {
        await documentsApi.create(form, file as File)
      }
      goBack()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu tài liệu')
    } finally {
      setSubmitting(false)
    }
  }

  if (!canEdit) return <Navigate to={LIST_PATH} replace />

  return (
    <section>
      <div className="page-head">
        <h1>{editingId !== null ? 'Sửa thông tin tài liệu' : 'Tải lên tài liệu'}</h1>
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
            Loại văn bản
            <select
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value as DocumentCategory }))}
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {DOCUMENT_CATEGORY_LABELS[c]}
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
              {allowedClasses.map((c) => (
                <option key={c} value={c}>
                  {CLASSIFICATION_LABELS[c]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Mô tả
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            />
          </label>
          {editingId === null ? (
            <Field
              label="Tệp đính kèm (.pdf, .doc/.docx, .xls/.xlsx, .ppt/.pptx)"
              required
              error={fileErr}
            >
              <input
                type="file"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null)
                  setFileErr(null)
                }}
                required
              />
            </Field>
          ) : (
            <>
              <label>
                Thay tệp đính kèm (.pdf, .doc/.docx, .xls/.xlsx, .ppt/.pptx)
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
              </label>
              <p className="state-note">
                {currentFileName ? (
                  <>
                    Tệp hiện tại: <strong>{currentFileName}</strong>.{' '}
                  </>
                ) : null}
                {file ? `Sẽ thay bằng: ${file.name}` : 'Bỏ trống nếu giữ nguyên tệp gốc.'}
              </p>
            </>
          )}
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={submitting}>
              {submitting ? 'Đang lưu...' : editingId !== null ? 'Cập nhật' : 'Tải lên'}
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
