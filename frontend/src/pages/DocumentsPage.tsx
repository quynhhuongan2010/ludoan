import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { documentsApi } from '../api/documents'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import {
  DOCUMENT_CATEGORY_LABELS,
  type DocumentCategory,
  type DocumentFormData,
  type DocumentItem,
} from '../types/document'

const categories = Object.keys(DOCUMENT_CATEGORY_LABELS) as DocumentCategory[]

const emptyForm: DocumentFormData = {
  title: '',
  category: 'bieu_mau',
  description: '',
  classification: 'noi_bo',
}

function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN')
}

export function DocumentsPage() {
  const { canEditContent, isCommander, hasClearance, userId } = useAuth()

  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState<DocumentCategory | ''>('')

  const [form, setForm] = useState<DocumentFormData>(emptyForm)
  const [file, setFile] = useState<File | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  // Bac phan loai user duoc phep chon khi dang tai lieu (an MAT neu khong du quyen)
  const allowedClasses: Classification[] = CLASSIFICATION_ORDER.filter(
    (c) => c !== 'mat' || isCommander || hasClearance,
  )

  function loadDocs() {
    setLoading(true)
    documentsApi
      .list(filterCategory ? { category: filterCategory } : undefined)
      .then(setDocs)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách tài liệu'),
      )
      .finally(() => setLoading(false))
  }

  useEffect(loadDocs, [filterCategory])

  function canManage(doc: DocumentItem) {
    return isCommander || doc.uploaded_by_id === userId
  }

  function startCreate() {
    setEditingId(null)
    setForm(emptyForm)
    setFile(null)
    setShowForm(true)
  }

  function startEdit(doc: DocumentItem) {
    setEditingId(doc.id)
    setForm({
      title: doc.title,
      category: doc.category,
      description: doc.description ?? '',
      classification: doc.classification,
    })
    setFile(null)
    setShowForm(true)
  }

  function cancelForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
    setFile(null)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (editingId !== null) {
        const updated = await documentsApi.update(editingId, form)
        setDocs((prev) => prev.map((d) => (d.id === editingId ? updated : d)))
      } else {
        if (!file) {
          setError('Vui lòng chọn tệp để tải lên.')
          setSubmitting(false)
          return
        }
        const created = await documentsApi.create(form, file)
        setDocs((prev) => [created, ...prev])
      }
      cancelForm()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu tài liệu')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    setError(null)
    try {
      await documentsApi.remove(id)
      setDocs((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá tài liệu')
    }
  }

  async function handleDownload(doc: DocumentItem) {
    setError(null)
    setDownloadingId(doc.id)
    try {
      const blob = await documentsApi.download(doc.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.file_name
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể tải tệp về')
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <section>
      <h1>Văn bản – Tài liệu – Biểu mẫu</h1>

      <div className="post-toolbar">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value as DocumentCategory | '')}
        >
          <option value="">Tất cả loại văn bản</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {DOCUMENT_CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>

        {canEditContent && !showForm ? (
          <button type="button" onClick={startCreate}>
            Tải lên tài liệu
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
            <label>
              Tệp đính kèm (.pdf, .doc/.docx, .xls/.xlsx, .ppt/.pptx)
              <input
                type="file"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
            </label>
          ) : (
            <p className="state-note">Sửa thông tin mô tả — tệp gốc được giữ nguyên.</p>
          )}
          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {editingId !== null ? 'Cập nhật' : 'Tải lên'}
            </button>
            <button type="button" onClick={cancelForm}>
              Huỷ
            </button>
          </div>
        </form>
      ) : null}

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : docs.length === 0 ? (
        <p>Chưa có tài liệu nào.</p>
      ) : (
        <div className="post-list">
          {docs.map((doc) => (
            <article key={doc.id} className="post-card">
              <div className="post-card-body">
                <div className="badge-row">
                  <span className="post-category">{DOCUMENT_CATEGORY_LABELS[doc.category]}</span>
                  <ClassificationBadge value={doc.classification} />
                </div>
                <h2>{doc.title}</h2>
                <p className="post-meta">
                  {doc.uploaded_by_full_name} · {formatDate(doc.created_at)} · {doc.file_name} ·{' '}
                  {fileSize(doc.file_size)}
                </p>
                {doc.description ? <p style={{ whiteSpace: 'pre-wrap' }}>{doc.description}</p> : null}
                <div className="row-actions">
                  <button
                    type="button"
                    onClick={() => handleDownload(doc)}
                    disabled={downloadingId === doc.id}
                  >
                    <Icon name="download" size={13} />{' '}
                    {downloadingId === doc.id ? 'Đang tải...' : 'Tải về'}
                  </button>
                  {canManage(doc) ? (
                    <>
                      <button type="button" onClick={() => startEdit(doc)}>
                        Sửa
                      </button>
                      <button type="button" onClick={() => handleDelete(doc.id)}>
                        Xoá
                      </button>
                    </>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
