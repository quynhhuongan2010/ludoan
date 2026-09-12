import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { postsApi } from '../api/posts'
import { uploadsApi } from '../api/uploads'
import { Icon } from '../components/Icon'
import { RichContentEditor } from '../components/RichContentEditor'
import { useAuth } from '../context/AuthContext'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import { firstContentImage, stripHtml } from '../utils/richContent'
import { slugify } from '../utils/slug'
import {
  POST_CATEGORY_LABELS,
  POST_STATUS_LABELS,
  type Post,
  type PostCategory,
  type PostCreate,
} from '../types/post'

const categories = Object.keys(POST_CATEGORY_LABELS) as PostCategory[]
const MAX_TAGS = 20
const LIST_PATH = '/tin-tuc'

const emptyForm: PostCreate = {
  title: '',
  summary: '',
  slug: '',
  category: 'huan_luyen',
  content: '',
  tags: [],
  cover_image_url: '',
  classification: 'noi_bo',
  is_featured: false,
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function imgSrc(url: string): string {
  return url.startsWith('/static') ? `${API_BASE}${url}` : url
}

export function PostFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const editingId = id ? Number(id) : null

  const { canEditContent, isCommander, hasClearance } = useAuth()

  const [form, setForm] = useState<PostCreate>(emptyForm)
  const [editing, setEditing] = useState<Post | null>(null)
  const [loading, setLoading] = useState(editingId !== null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [slugTouched, setSlugTouched] = useState(false)
  const [tagDraft, setTagDraft] = useState('')
  const [coverBusy, setCoverBusy] = useState(false)
  const [coverDragOver, setCoverDragOver] = useState(false)
  /** Trường bị bỏ trống khi bấm lưu/đăng — để tô đỏ + đưa con trỏ tới đúng ô. */
  const [invalidField, setInvalidField] = useState<'title' | 'content' | null>(null)
  const coverInputRef = useRef<HTMLInputElement>(null)
  const titleInputRef = useRef<HTMLInputElement>(null)
  const contentWrapRef = useRef<HTMLDivElement>(null)

  // Bac phan loai user duoc phep chon khi dang bai
  const allowedClasses: Classification[] = CLASSIFICATION_ORDER.filter(
    (c) => c !== 'mat' || isCommander || hasClearance,
  )

  const autoSlug = useMemo(() => slugify(form.title), [form.title])
  const effectiveSlug = slugTouched && form.slug ? slugify(form.slug) : autoSlug

  useEffect(() => {
    if (editingId === null) return
    setLoading(true)
    postsApi
      .get(editingId)
      .then((post) => {
        setEditing(post)
        setForm({
          title: post.title,
          summary: post.summary ?? '',
          slug: post.slug ?? '',
          category: post.category,
          content: post.content,
          tags: post.tags ?? [],
          cover_image_url: post.cover_image_url ?? '',
          classification: post.classification,
          is_featured: post.is_featured,
        })
        setSlugTouched(Boolean(post.slug))
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải bài viết'),
      )
      .finally(() => setLoading(false))
  }, [editingId])

  function goBack() {
    navigate(LIST_PATH)
  }

  function patch(next: Partial<PostCreate>) {
    // Vừa gõ lại vào ô đang báo lỗi -> bỏ đánh dấu đỏ.
    if (invalidField === 'title' && 'title' in next) setInvalidField(null)
    if (invalidField === 'content' && 'content' in next) setInvalidField(null)
    setForm((f) => ({ ...f, ...next }))
  }

  function addTag(raw: string) {
    const t = raw.trim().replace(/,+$/, '').slice(0, 40)
    if (!t) return
    setForm((f) => {
      if (f.tags.length >= MAX_TAGS) return f
      if (f.tags.some((x) => x.toLowerCase() === t.toLowerCase())) return f
      return { ...f, tags: [...f.tags, t] }
    })
    setTagDraft('')
  }

  function removeTag(t: string) {
    setForm((f) => ({ ...f, tags: f.tags.filter((x) => x !== t) }))
  }

  async function uploadCover(file: File) {
    setError(null)
    setCoverBusy(true)
    try {
      const res = await uploadsApi.upload(file)
      patch({ cover_image_url: res.url })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Tải ảnh bìa thất bại')
    } finally {
      setCoverBusy(false)
    }
  }

  function onCoverDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setCoverDragOver(false)
    const file = e.dataTransfer?.files?.[0]
    if (file && file.type.startsWith('image/')) void uploadCover(file)
  }

  function buildPayload(): PostCreate {
    // Khong dong vao slug -> giu slug cu (khi sua) hoac de backend tu sinh (khi tao).
    const finalSlug = slugTouched ? slugify(form.slug || '') : editing?.slug ?? ''
    return {
      ...form,
      title: form.title.trim(),
      summary: form.summary?.trim() || null,
      slug: finalSlug || null,
      cover_image_url: form.cover_image_url || null,
      tags: form.tags,
    }
  }

  async function save(asDraft: boolean) {
    setError(null)
    setInvalidField(null)
    if (!form.title.trim()) {
      setInvalidField('title')
      setError('Chưa nhập Tiêu đề bài viết — hãy điền vào ô tiêu đề lớn ở đầu trang.')
      titleInputRef.current?.focus()
      titleInputRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
      return
    }
    if (!asDraft && !stripHtml(form.content).trim()) {
      setInvalidField('content')
      setError(
        'Chưa nhập Nội dung bài viết. Hãy gõ nội dung vào khung soạn thảo bên dưới ô tiêu đề, ' +
          'hoặc bấm “Lưu nháp” nếu chỉ muốn lưu tạm.',
      )
      contentWrapRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
      return
    }
    setSubmitting(true)
    try {
      const payload = buildPayload()
      if (editing) {
        await postsApi.update(editing.id, payload, asDraft)
      } else {
        await postsApi.create(payload, asDraft)
      }
      goBack()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu bài viết')
    } finally {
      setSubmitting(false)
    }
  }

  if (!canEditContent) return <Navigate to={LIST_PATH} replace />

  const coverUrl = form.cover_image_url ? imgSrc(form.cover_image_url) : ''
  // Chua chon anh bia rieng -> lay anh dau tien trong noi dung lam anh minh hoa
  // (backend cung suy dien y het khi tra bai ve, day chi la xem truoc).
  const autoCover = form.cover_image_url ? '' : firstContentImage(form.content) ?? ''

  return (
    <section className="cms">
      <div className="cms-topbar">
        <button type="button" className="btn-cancel" onClick={goBack}>
          <Icon name="arrow-left" size={15} /> Quay lại danh sách
        </button>
        <span className="cms-topbar-title">
          {editing ? `Sửa bài: ${editing.title}` : 'Soạn bài viết mới'}
          {editing ? (
            <span className={`status-badge status-${editing.status}`}>
              {POST_STATUS_LABELS[editing.status]}
            </span>
          ) : null}
        </span>
      </div>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <div className="cms-grid">
          <div className="cms-main">
            <input
              ref={titleInputRef}
              className={`cms-title-input${invalidField === 'title' ? ' is-invalid' : ''}`}
              type="text"
              maxLength={255}
              placeholder="Tiêu đề bài viết"
              aria-invalid={invalidField === 'title'}
              value={form.title}
              onChange={(e) => patch({ title: e.target.value })}
              onBlur={() => {
                if (!form.title.trim()) setInvalidField('title')
              }}
            />
            {invalidField === 'title' ? (
              <p className="cms-field-hint">Tiêu đề bài viết là bắt buộc.</p>
            ) : null}
            <textarea
              className="cms-summary-input"
              rows={2}
              maxLength={500}
              placeholder="Tóm tắt ngắn hiển thị ở thẻ tin và đầu bài (không bắt buộc)…"
              value={form.summary ?? ''}
              onChange={(e) => patch({ summary: e.target.value })}
            />
            <div
              ref={contentWrapRef}
              className={`cms-content-wrap${invalidField === 'content' ? ' is-invalid' : ''}`}
            >
              <RichContentEditor
                value={form.content}
                onChange={(html) => patch({ content: html })}
                placeholder="Nội dung bài viết…"
              />
              {invalidField === 'content' ? (
                <p className="cms-field-hint">Khung nội dung đang trống.</p>
              ) : null}
            </div>
          </div>

          <aside className="cms-side">
            <div className="cms-card cms-actions">
              <button
                type="button"
                className="btn-cancel"
                disabled={submitting}
                onClick={() => save(true)}
              >
                <Icon name="file" size={14} /> Lưu nháp
              </button>
              <button
                type="button"
                className="btn-submit"
                disabled={submitting}
                onClick={() => save(false)}
              >
                <Icon name="send" size={14} />{' '}
                {isCommander ? 'Đăng bài' : editing?.status === 'da_duyet' ? 'Cập nhật' : 'Gửi duyệt'}
              </button>
            </div>

            <div className="cms-card">
              <label>
                Danh mục
                <select
                  value={form.category}
                  onChange={(e) => patch({ category: e.target.value as PostCategory })}
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {POST_CATEGORY_LABELS[c]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Bậc truy cập
                <select
                  value={form.classification}
                  onChange={(e) => patch({ classification: e.target.value as Classification })}
                >
                  {allowedClasses.map((c) => (
                    <option key={c} value={c}>
                      {CLASSIFICATION_LABELS[c]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.is_featured}
                  onChange={(e) => patch({ is_featured: e.target.checked })}
                />
                Nổi bật trên trang chủ (chỉ tác dụng với bài Công khai đã duyệt)
              </label>
            </div>

            <div className="cms-card">
              <span className="cms-card-label">Ảnh bìa</span>
              <div
                className={`cms-dropzone${coverDragOver ? ' is-over' : ''}`}
                onClick={() => coverInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault()
                  setCoverDragOver(true)
                }}
                onDragLeave={() => setCoverDragOver(false)}
                onDrop={onCoverDrop}
              >
                {coverUrl ? (
                  <img src={coverUrl} alt="Ảnh bìa" className="cms-cover-preview" />
                ) : autoCover ? (
                  <img src={autoCover} alt="Ảnh minh hoạ tự động" className="cms-cover-preview" />
                ) : (
                  <span className="cms-dropzone-hint">
                    <Icon name="upload" size={18} />
                    Kéo–thả ảnh vào đây hoặc bấm để chọn tệp
                  </span>
                )}
                {coverBusy ? <span className="cms-dropzone-busy">Đang tải…</span> : null}
              </div>
              {!form.cover_image_url && autoCover ? (
                <span className="state-note">
                  Chưa chọn ảnh bìa riêng — hệ thống tự lấy ảnh đầu tiên trong nội dung làm ảnh minh
                  hoạ. Kéo–thả hoặc bấm để chọn ảnh bìa khác.
                </span>
              ) : null}
              <input
                ref={coverInputRef}
                type="file"
                accept="image/*"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  e.target.value = ''
                  if (f) void uploadCover(f)
                }}
              />
              {form.cover_image_url ? (
                <button
                  type="button"
                  className="cms-linkbtn"
                  onClick={() => patch({ cover_image_url: '' })}
                >
                  <Icon name="x" size={12} /> Bỏ ảnh bìa
                </button>
              ) : null}
            </div>

            <div className="cms-card">
              <span className="cms-card-label">Thẻ từ khoá ({form.tags.length}/{MAX_TAGS})</span>
              <div className="cms-tags">
                {form.tags.map((t) => (
                  <span key={t} className="cms-tag">
                    {t}
                    <button type="button" aria-label={`Bỏ thẻ ${t}`} onClick={() => removeTag(t)}>
                      <Icon name="x" size={11} />
                    </button>
                  </span>
                ))}
              </div>
              <input
                type="text"
                placeholder="Nhập thẻ rồi Enter…"
                value={tagDraft}
                maxLength={40}
                onChange={(e) => setTagDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ',') {
                    e.preventDefault()
                    addTag(tagDraft)
                  } else if (e.key === 'Backspace' && !tagDraft && form.tags.length) {
                    removeTag(form.tags[form.tags.length - 1])
                  }
                }}
                onBlur={() => addTag(tagDraft)}
              />
            </div>

            <div className="cms-card">
              <label>
                Slug (đường dẫn SEO)
                <input
                  type="text"
                  value={slugTouched ? form.slug ?? '' : autoSlug}
                  placeholder={autoSlug || 'tu-sinh-tu-tieu-de'}
                  onChange={(e) => {
                    setSlugTouched(true)
                    patch({ slug: e.target.value })
                  }}
                />
              </label>
              <div className="cms-slug-row">
                <code>/{effectiveSlug || 'tu-sinh-tu-tieu-de'}</code>
                {slugTouched ? (
                  <button
                    type="button"
                    className="cms-linkbtn"
                    onClick={() => {
                      setSlugTouched(false)
                      patch({ slug: '' })
                    }}
                  >
                    Tạo lại từ tiêu đề
                  </button>
                ) : null}
              </div>
              <span className="state-note">
                Để trống để hệ thống tự sinh. Nếu trùng, backend tự thêm hậu tố (-2, -3…).
              </span>
            </div>
          </aside>
        </div>
      )}
    </section>
  )
}
