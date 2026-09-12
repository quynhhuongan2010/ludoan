import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { educationMaterialsApi } from '../api/educationMaterials'
import { uploadsApi } from '../api/uploads'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { RichContentEditor } from '../components/RichContentEditor'
import { useRequiredFields } from '../hooks/useRequiredFields'
import {
  EDUCATION_CATEGORY_LABELS,
  type EducationCategory,
  type EducationMaterialCreate,
} from '../types/educationMaterial'
import { stripHtml } from '../utils/richContent'

const categories = Object.keys(EDUCATION_CATEGORY_LABELS) as EducationCategory[]
const emptyForm: EducationMaterialCreate = {
  title: '',
  category: 'hoc_tap_chinh_tri_quan_su',
  period_label: '',
  content: '',
  attachment_url: '',
}

const LIST_PATH = '/giao-duc-chinh-tri'

// Mang LAN noi bo, khong the dan URL ngoai internet -> bat buoc tai file truc tiep.
const ATTACHMENT_ACCEPT = '.jpg,.jpeg,.png,.pdf,.doc,.docx'
const ATTACHMENT_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
const MAX_ATTACHMENT_MB = 20

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileNameFromUrl(url: string): string {
  const parts = url.split('/')
  return parts[parts.length - 1] || url
}

export function EducationFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const editingId = id ? Number(id) : null

  const [form, setForm] = useState<EducationMaterialCreate>(emptyForm)
  const [loading, setLoading] = useState(editingId !== null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const req = useRequiredFields(['title', 'content'] as const)

  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [selectedFileSize, setSelectedFileSize] = useState<number | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editingId === null) return
    setLoading(true)
    educationMaterialsApi
      .get(editingId)
      .then((m) => {
        setForm({
          title: m.title,
          category: m.category,
          period_label: m.period_label ?? '',
          content: m.content,
          attachment_url: m.attachment_url ?? '',
        })
        setSelectedFileName(m.attachment_url ? fileNameFromUrl(m.attachment_url) : null)
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải nội dung'),
      )
      .finally(() => setLoading(false))
  }, [editingId])

  function goBack() {
    navigate(LIST_PATH)
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    event.target.value = ''
    if (!file) return

    setUploadError(null)
    const ext = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`
    if (!ATTACHMENT_EXTENSIONS.includes(ext)) {
      setUploadError(
        `Định dạng '${ext}' không được phép. Chỉ chấp nhận: ${ATTACHMENT_EXTENSIONS.join(', ')}`,
      )
      return
    }
    if (file.size > MAX_ATTACHMENT_MB * 1024 * 1024) {
      setUploadError(`File vượt quá giới hạn ${MAX_ATTACHMENT_MB} MB (file hiện tại: ${formatFileSize(file.size)})`)
      return
    }

    setSelectedFileName(file.name)
    setSelectedFileSize(file.size)
    setUploading(true)
    try {
      const result = await uploadsApi.upload(file)
      setForm((f) => ({ ...f, attachment_url: result.url }))
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : 'Tải file lên thất bại')
      setSelectedFileName(null)
      setSelectedFileSize(null)
    } finally {
      setUploading(false)
    }
  }

  function handleRemoveAttachment() {
    setForm((f) => ({ ...f, attachment_url: '' }))
    setSelectedFileName(null)
    setSelectedFileSize(null)
    setUploadError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ title: form.title, content: stripHtml(form.content).trim() })) return
    setSubmitting(true)
    try {
      const payload: EducationMaterialCreate = {
        ...form,
        period_label: form.period_label || null,
        attachment_url: form.attachment_url || null,
      }
      if (editingId !== null) {
        await educationMaterialsApi.update(editingId, payload)
      } else {
        await educationMaterialsApi.create(payload)
      }
      goBack()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu nội dung')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section>
      <div className="page-head">
        <h1>{editingId !== null ? 'Sửa nội dung giáo dục chính trị' : 'Đăng nội dung mới'}</h1>
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
            Danh mục
            <select
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value as EducationCategory }))}
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {EDUCATION_CATEGORY_LABELS[c]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Kỳ áp dụng (tuần/tháng)
            <input
              type="text"
              maxLength={50}
              value={form.period_label ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, period_label: e.target.value }))}
              placeholder="VD: Tuần 35/2026 hoặc Tháng 8/2026"
            />
          </label>
          <label>
            Tài liệu đính kèm
            <div className="file-upload-field">
              <button
                type="button"
                className="btn-cancel file-upload-pick"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <Icon name="upload" size={15} /> Chọn tệp từ máy tính
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept={ATTACHMENT_ACCEPT}
                onChange={handleFileChange}
                hidden
              />
              {uploading ? (
                <span className="file-upload-status">
                  <span className="spinner" aria-hidden="true" /> Đang tải lên...
                </span>
              ) : selectedFileName ? (
                <span className="file-upload-status">
                  <Icon name="file" size={15} />
                  {selectedFileName}
                  {selectedFileSize !== null ? ` (${formatFileSize(selectedFileSize)})` : ''}
                  <button
                    type="button"
                    className="file-upload-remove"
                    onClick={handleRemoveAttachment}
                    title="Xoá tệp đã chọn"
                  >
                    <Icon name="x" size={13} />
                  </button>
                </span>
              ) : (
                <span className="file-upload-status file-upload-empty">Chưa chọn tệp nào</span>
              )}
            </div>
            <input
              type="text"
              className="file-upload-url"
              value={form.attachment_url ?? ''}
              readOnly
              placeholder="Đường dẫn nội bộ sẽ hiện ra sau khi tải lên thành công"
            />
            <span className="state-note">
              Cho phép ảnh (.jpg, .jpeg, .png) và tài liệu (.pdf, .doc, .docx), tối đa {MAX_ATTACHMENT_MB} MB.
            </span>
            {uploadError ? (
              <span role="alert" className="form-note form-error">
                {uploadError}
              </span>
            ) : null}
          </label>
          <Field label="Nội dung" required req={req} name="content">
            <RichContentEditor
              value={form.content}
              onChange={(html) => {
                setForm((f) => ({ ...f, content: html }))
                req.mark('content', stripHtml(html).trim())
              }}
              placeholder="Nội dung giáo dục chính trị..."
            />
          </Field>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={submitting || uploading}>
              {submitting ? 'Đang lưu...' : editingId !== null ? 'Cập nhật' : 'Đăng'}
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
