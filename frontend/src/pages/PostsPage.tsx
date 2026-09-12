import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { postsApi } from '../api/posts'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { EmptyState } from '../components/EmptyState'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { RichContent } from '../components/RichContent'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { usePagination } from '../hooks/usePagination'
import { CLASSIFICATION_LABELS, CLASSIFICATION_ORDER, type Classification } from '../types/common'
import { excerptFromHtml } from '../utils/richContent'
import {
  POST_CATEGORY_LABELS,
  POST_STATUS_LABELS,
  type Post,
  type PostCategory,
} from '../types/post'

const categories = Object.keys(POST_CATEGORY_LABELS) as PostCategory[]
const PAGE_SIZE_OPTIONS = [6, 9, 12, 24]

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function imgSrc(url: string): string {
  return url.startsWith('/static') ? `${API_BASE}${url}` : url
}

export function PostsPage() {
  const navigate = useNavigate()
  const { canEditContent, isCommander, hasClearance, userId } = useAuth()
  const confirm = useConfirm()

  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState<PostCategory | ''>('')
  const [filterClass, setFilterClass] = useState<Classification | ''>('')
  const [openId, setOpenId] = useState<number | null>(null)
  const [reviewNote, setReviewNote] = useState('')

  const {
    page,
    pageSize,
    pageCount,
    total,
    pageItems,
    setPageIndex,
    setPageSize,
    showPagination,
  } = usePagination(posts, 9, `${filterCategory}|${filterClass}`)

  // Bac phan loai user duoc phep loc khi xem danh sach
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

  async function handleSubmitForReview(id: number) {
    setError(null)
    try {
      const updated = await postsApi.submit(id)
      setPosts((prev) => prev.map((p) => (p.id === id ? updated : p)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể gửi duyệt')
    }
  }

  async function handleDelete(id: number) {
    const post = posts.find((p) => p.id === id)
    const ok = await confirm({
      message: (
        <>
          Xoá bài viết <strong>{post?.title ?? `#${id}`}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
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

        {canEditContent ? (
          <button type="button" className="btn-create" onClick={() => navigate('/tin-tuc/moi')}>
            <Icon name="plus" size={15} /> Đăng bài mới
          </button>
        ) : null}
      </div>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : posts.length === 0 ? (
        <EmptyState icon="newspaper" message="Chưa có tin nào." />
      ) : (
        <>
          <div className="news-board">
            {pageItems.map((post, idx) => {
              const open = openId === post.id
              const isLead = idx === 0 && page === 0 && !filterCategory
              const excerpt = post.summary?.trim() || excerptFromHtml(post.content, isLead ? 320 : 150)
              return (
                <article
                  key={post.id}
                  className={`news-article${isLead ? ' news-lead' : ''}${open ? ' is-open' : ''}`}
                >
                  <div className="news-thumb">
                    {post.cover_image_url ? (
                      <img src={imgSrc(post.cover_image_url)} alt="" />
                    ) : (
                      <div className="news-thumb-ph" aria-hidden="true">
                        <Icon name="newspaper" size={isLead ? 40 : 24} />
                      </div>
                    )}
                  </div>
                  <div className="news-body">
                    <div className="news-kicker-row">
                      <span className="news-kicker">{POST_CATEGORY_LABELS[post.category]}</span>
                      <ClassificationBadge value={post.classification} />
                      <span className={`status-badge status-${post.status}`}>
                        {POST_STATUS_LABELS[post.status]}
                      </span>
                      {post.is_featured ? <span className="tag-inline">★ Nổi bật</span> : null}
                    </div>
                    <h2 className="news-headline">
                      <button type="button" onClick={() => setOpenId(open ? null : post.id)}>
                        {post.title}
                      </button>
                    </h2>
                    <p className="news-meta">
                      Đăng bởi {post.author_full_name} ·{' '}
                      {new Date(post.created_at).toLocaleDateString('vi-VN')}
                    </p>
                    {post.status === 'tra_lai' && post.review_note ? (
                      <p className="form-error">Chỉ huy trả lại: {post.review_note}</p>
                    ) : null}

                    {open ? (
                      <>
                        <RichContent html={post.content} />
                        {post.tags.length ? (
                          <p className="cms-preview-tags">
                            {post.tags.map((t) => (
                              <span key={t} className="tag-inline">
                                #{t}
                              </span>
                            ))}
                          </p>
                        ) : null}
                        <button type="button" className="news-more" onClick={() => setOpenId(null)}>
                          Thu gọn ▲
                        </button>
                      </>
                    ) : (
                      <>
                        <p className="news-excerpt">{excerpt}</p>
                        <button
                          type="button"
                          className="news-more"
                          onClick={() => setOpenId(post.id)}
                        >
                          Đọc tiếp →
                        </button>
                      </>
                    )}

                    {canManage(post) ? (
                      <div className="row-actions news-actions">
                        <button
                          type="button"
                          className="btn-edit"
                          onClick={() => navigate(`/tin-tuc/${post.id}/sua`)}
                        >
                          <Icon name="edit" /> Sửa
                        </button>
                        {post.status === 'nhap' || post.status === 'tra_lai' ? (
                          <button
                            type="button"
                            className="btn-approve"
                            onClick={() => handleSubmitForReview(post.id)}
                          >
                            <Icon name="send" /> Gửi duyệt
                          </button>
                        ) : null}
                        <label className="btn-file">
                          <Icon name="upload" size={14} /> Đổi ảnh bìa
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
                        <button type="button" className="btn-delete" onClick={() => handleDelete(post.id)}>
                          <Icon name="trash" /> Xoá
                        </button>
                      </div>
                    ) : null}

                    {isCommander && post.status !== 'da_duyet' && post.status !== 'nhap' ? (
                      <div className="review-bar">
                        <input
                          type="text"
                          placeholder="Lý do trả lại (nếu có)"
                          value={reviewNote}
                          onChange={(e) => setReviewNote(e.target.value)}
                        />
                        <button type="button" className="btn-approve" onClick={() => handleReview(post.id, 'da_duyet')}>
                          <Icon name="check" /> Duyệt đăng
                        </button>
                        <button type="button" className="btn-reject" onClick={() => handleReview(post.id, 'tra_lai')}>
                          <Icon name="undo" /> Trả lại
                        </button>
                      </div>
                    ) : null}
                  </div>
                </article>
              )
            })}
          </div>
          {showPagination ? (
            <Pagination
              page={page}
              pageCount={pageCount}
              total={total}
              pageSize={pageSize}
              onPage={setPageIndex}
              onPageSize={setPageSize}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              itemLabel="bài viết"
            />
          ) : null}
        </>
      )}
    </section>
  )
}
