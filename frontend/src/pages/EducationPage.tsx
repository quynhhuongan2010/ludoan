import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { educationMaterialsApi } from '../api/educationMaterials'
import { useAuth } from '../context/AuthContext'
import {
  EDUCATION_CATEGORY_LABELS,
  type EducationCategory,
  type EducationMaterial,
  type EducationMaterialCreate,
} from '../types/educationMaterial'

const categories = Object.keys(EDUCATION_CATEGORY_LABELS) as EducationCategory[]
const emptyForm: EducationMaterialCreate = {
  title: '',
  category: 'hoc_tap_chinh_tri_quan_su',
  period_label: '',
  content: '',
  attachment_url: '',
}

export function EducationPage() {
  const { canEditContent, isCommander, userId } = useAuth()

  const [materials, setMaterials] = useState<EducationMaterial[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState<EducationCategory | ''>('')

  const [form, setForm] = useState<EducationMaterialCreate>(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)

  function loadMaterials() {
    setLoading(true)
    educationMaterialsApi
      .list(filterCategory ? { category: filterCategory } : undefined)
      .then(setMaterials)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Không thể tải nội dung'))
      .finally(() => setLoading(false))
  }

  useEffect(loadMaterials, [filterCategory])

  function canManage(material: EducationMaterial) {
    return isCommander || material.author_id === userId
  }

  function startCreate() {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  function startEdit(material: EducationMaterial) {
    setEditingId(material.id)
    setForm({
      title: material.title,
      category: material.category,
      period_label: material.period_label ?? '',
      content: material.content,
      attachment_url: material.attachment_url ?? '',
    })
    setShowForm(true)
  }

  function cancelForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload: EducationMaterialCreate = {
        ...form,
        period_label: form.period_label || null,
        attachment_url: form.attachment_url || null,
      }
      if (editingId !== null) {
        const updated = await educationMaterialsApi.update(editingId, payload)
        setMaterials((prev) => prev.map((m) => (m.id === editingId ? updated : m)))
      } else {
        const created = await educationMaterialsApi.create(payload)
        setMaterials((prev) => [created, ...prev])
      }
      cancelForm()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu nội dung')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    setError(null)
    try {
      await educationMaterialsApi.remove(id)
      setMaterials((prev) => prev.filter((m) => m.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá nội dung')
    }
  }

  return (
    <section>
      <h1>Giáo dục chính trị</h1>

      <div className="post-toolbar">
        <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value as EducationCategory | '')}>
          <option value="">Tất cả danh mục</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {EDUCATION_CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>

        {canEditContent && !showForm ? (
          <button type="button" onClick={startCreate}>
            Đăng nội dung mới
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
            Tài liệu đính kèm (URL)
            <input
              type="text"
              value={form.attachment_url ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, attachment_url: e.target.value }))}
              placeholder="https://..."
            />
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
              {editingId !== null ? 'Cập nhật' : 'Đăng'}
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
      ) : materials.length === 0 ? (
        <p>Chưa có nội dung nào.</p>
      ) : (
        <div className="post-list">
          {materials.map((material) => (
            <article key={material.id} className="post-card">
              <div className="post-card-body">
                <span className="post-category">{EDUCATION_CATEGORY_LABELS[material.category]}</span>
                {material.period_label ? <span className="post-period">{material.period_label}</span> : null}
                <h2>{material.title}</h2>
                <p className="post-meta">
                  Đăng bởi {material.author_full_name} · {new Date(material.created_at).toLocaleDateString('vi-VN')}
                </p>
                <p>{material.content}</p>
                {material.attachment_url ? (
                  <p>
                    <a href={material.attachment_url} target="_blank" rel="noreferrer">
                      Tài liệu đính kèm
                    </a>
                  </p>
                ) : null}
                {canManage(material) ? (
                  <div className="row-actions">
                    <button type="button" onClick={() => startEdit(material)}>
                      Sửa
                    </button>
                    <button type="button" onClick={() => handleDelete(material.id)}>
                      Xoá
                    </button>
                  </div>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
