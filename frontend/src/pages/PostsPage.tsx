import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { postsApi } from '../api/posts'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { useAuth } from '../context/AuthContext'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import {
  POST_CATEGORY_LABELS,
  POST_STATUS_LABELS,
  type Post,
  type PostCategory,
  type PostCreate,
} from '../types/post'

const categories = Object.keys(POST_CATEGORY_LABELS) as PostCategory[]
const emptyForm: PostCreate = {
  title: '',
  category: 'huan_luyen',
  content: '',
  cover_image_url: '',
  classification: 'noi_bo',
  is_featured: false,
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function imgSrc(url: string): string {
  return url.startsWith('/static') ? `${API_BASE}${url}` : url
}

export function PostsPage() {
  const { canEditContent, isCommander, hasClearance, userId } = useAuth()

  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState<PostCategory | ''>('')
  const [filterClass, setFilterClass] = useState<Classification | ''>('')

  const [form, setForm] = useState<PostCreate>(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [reviewNote, setReviewNote] = useState('')

  // Bac phan loai user duoc phep chon khi dang bai
  const allowedClasses: Classification[] = CLASSIFICATION_ORDER.filter(
    (c) => c !== 'mat' || isCommander || hasClearance,
  )

  function loadPosts() {
    setLoading(true)
    const params: { category?: PostCategory; classification?: Classification } = {}
    if (filterCategory) params.category = filterCategory
    if (filterClass) params.classification = filterClass
    postsApi
      .list(Object.keys(params).length ? params : undefined)
      .then(setPosts)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Không thể tải tin tức'))
      .finally(() => setLoading(false))
  }

  useEffect(loadPosts, [filterCategory, filterClass])

  function canManage(post: Post) {
    return isCommander || post.author_id === userId
  }

  function startCreate() {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  function startEdit(post: Post) {
    setEditingId(post.id)
    setForm({
      title: post.title,
      category: post.category,
      content: post.content,
      cover_image_url: post.cover_image_url ?? '',
      classification: post.classification,
      is_featured: post.is_featured,
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
      const payload: PostCreate = { ...form, cover_image_url: form.cover_image_url || null }
      if (editingId !== null) {
        const updated = await postsApi.update(editingId, payload)
        setPosts((prev) => prev.map((p) => (p.id === editingId ? updated : p)))
      } else {
        const created = await postsApi.create(payload)
        setPosts((prev) => [created, ...prev])
      }
      cancelForm()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu bài viết')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    setError(null)
    try {
      await postsApi.remove(id)
      setPosts((prev) => prev.filter((p) => p.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá bài viết')
    }
  }

  async function handleReview(id: number, status: 'da_duyet' | 'tra_lai') {
    setError(null)
    try {
      const updated = await postsApi.review(id, {
        status,
        review_note: status === 'tra_lai' ? reviewNote || null : null,
      })
      setPosts((prev) => prev.map((p) => (p.id === id ? updated : p)))
      setReviewNote('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể duyệt bài')
    }
  }

  async function handleThumbnail(id: number, file: File) {
    setError(null)
    try {
      const updated = await postsApi.uploadThumbnail(id, file)
      setPosts((prev) => prev.map((p) => (p.id === id ? updated : p)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể tải ảnh lên')
    }
  }

  return (
    <section>
      <h1>Tin tức – Hoạt động đơn vị</h1>

      <div className="post-toolbar">
        <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value as PostCategory | '')}>
          <option value="">Tất cả danh mục</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {POST_CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>

        <select
          value={filterClass}
          onChange={(e) => setFilterClass(e.target.value as Classification | '')}
          title="Lọc theo bậc phân loại"
        >
          <option value="">Tất cả bậc phân loại</option>
          {allowedClasses.map((c) => (
            <option key={c} value={c}>
              {CLASSIFICATION_LABELS[c]}
            </option>
          ))}
        </select>

        {canEditContent && !showForm ? (
          <button type="button" onClick={startCreate}>
            Đăng bài mới
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
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value as PostCategory }))}
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
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.is_featured}
              onChange={(e) => setForm((f) => ({ ...f, is_featured: e.target.checked }))}
            />
            Nổi bật (hiển thị ở trang công khai — chỉ có tác dụng với bài Công khai đã duyệt)
          </label>
          <label>
            Ảnh bìa (URL)
            <input
              type="text"
              value={form.cover_image_url ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, cover_image_url: e.target.value }))}
              placeholder="https://... hoặc để trống rồi tải ảnh sau khi lưu"
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
              {editingId !== null ? 'Cập nhật' : 'Đăng bài'}
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
      ) : posts.length === 0 ? (
        <p>Chưa có tin nào.</p>
      ) : (
        <div className="post-list">
          {posts.map((post) => (
            <article key={post.id} className="post-card">
              {post.cover_image_url ? <img src={imgSrc(post.cover_image_url)} alt="" /> : null}
              <div className="post-card-body">
                <div className="badge-row">
                  <span className="post-category">{POST_CATEGORY_LABELS[post.category]}</span>
                  <ClassificationBadge value={post.classification} />
                  <span className={`status-badge status-${post.status}`}>
                    {POST_STATUS_LABELS[post.status]}
                  </span>
                  {post.is_featured ? <span className="tag-inline">★ Nổi bật</span> : null}
                </div>
                <h2>{post.title}</h2>
                <p className="post-meta">
                  Đăng bởi {post.author_full_name} · {new Date(post.created_at).toLocaleDateString('vi-VN')}
                </p>
                {post.status === 'tra_lai' && post.review_note ? (
                  <p className="form-error">Chỉ huy trả lại: {post.review_note}</p>
                ) : null}
                <p style={{ whiteSpace: 'pre-wrap' }}>{post.content}</p>

                {canManage(post) ? (
                  <div className="row-actions">
                    <button type="button" onClick={() => startEdit(post)}>
                      Sửa
                    </button>
                    <label className="btn-file">
                      Đổi ảnh bìa
                      <input
                        type="file"
                        accept="image/*"
                        hidden
                        onChange={(e) => {
                          const f = e.target.files?.[0]
                          if (f) handleThumbnail(post.id, f)
                          e.target.value = ''
                        }}
                      />
                    </label>
                    <button type="button" onClick={() => handleDelete(post.id)}>
                      Xoá
                    </button>
                  </div>
                ) : null}

                {isCommander && post.status !== 'da_duyet' ? (
                  <div className="review-bar">
                    <input
                      type="text"
                      placeholder="Lý do trả lại (nếu có)"
                      value={reviewNote}
                      onChange={(e) => setReviewNote(e.target.value)}
                    />
                    <button type="button" onClick={() => handleReview(post.id, 'da_duyet')}>
                      Duyệt đăng
                    </button>
                    <button type="button" onClick={() => handleReview(post.id, 'tra_lai')}>
                      Trả lại
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
