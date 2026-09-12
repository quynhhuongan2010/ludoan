import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { homeApi } from '../api/home'
import { Icon } from '../components/Icon'
import { PublicLayout } from '../components/PublicLayout'
import { ANNOUNCEMENT_PRIORITY_LABELS } from '../types/announcement'
import { DOCUMENT_CATEGORY_LABELS } from '../types/document'
import { POST_CATEGORY_LABELS } from '../types/post'
import type { PublicHome } from '../types/home'
import { stripHtml } from '../utils/richContent'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function excerpt(html: string, max = 200): string {
  const clean = stripHtml(html).replace(/\s+/g, ' ').trim()
  return clean.length > max ? `${clean.slice(0, max)}…` : clean
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN')
}

function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function PublicHomePage() {
  const [data, setData] = useState<PublicHome | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    homeApi
      .publicSummary(8)
      .then(setData)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải thông tin công khai'),
      )
      .finally(() => setLoading(false))
  }, [])

  const [hero, ...rest] = data?.featured_posts ?? []

  return (
    <PublicLayout>
      {loading ? (
        <p className="state-note">Đang tải thông tin...</p>
      ) : error ? (
        <p className="state-note form-error">{error}</p>
      ) : (
        <div className="layout-grid">
          <section className="main-column">
            <div className="block-section">
              <div className="block-title">
                <span>
                  <Icon name="newspaper" size={15} /> Tin nổi bật của đơn vị
                </span>
              </div>
              {hero ? (
                <>
                  <div className="hero-news">
                    {hero.cover_image_url ? (
                      <img
                        src={
                          hero.cover_image_url.startsWith('/static')
                            ? `${API_BASE}${hero.cover_image_url}`
                            : hero.cover_image_url
                        }
                        alt=""
                        className="hero-img"
                      />
                    ) : (
                      <div className="hero-img img-placeholder" aria-hidden="true">
                        <Icon name="newspaper" size={44} />
                      </div>
                    )}
                    <div className="hero-info">
                      <span className="post-category">{POST_CATEGORY_LABELS[hero.category]}</span>
                      <h2>{hero.title}</h2>
                      <p className="post-meta">
                        {hero.author_full_name} · {formatDate(hero.created_at)}
                      </p>
                      <p>{excerpt(hero.content)}</p>
                    </div>
                  </div>
                  {rest.length > 0 ? (
                    <ul className="widget-list">
                      {rest.map((p) => (
                        <li key={p.id}>
                          <Icon name="caret-right" size={12} />
                          <span className="widget-item">
                            <strong>{p.title}</strong>
                            <span className="widget-sub">
                              {POST_CATEGORY_LABELS[p.category]} · {formatDate(p.created_at)}
                            </span>
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </>
              ) : (
                <p className="state-note">Chưa có tin nổi bật công khai.</p>
              )}
              <p className="login-hint">
                <Icon name="lock" size={12} /> Xem đầy đủ tin tức, hoạt động đơn vị:{' '}
                <Link to="/login">đăng nhập</Link>.
              </p>
            </div>

            <div className="block-section">
              <div className="block-title">
                <span>
                  <Icon name="file" size={15} /> Văn bản – Biểu mẫu công khai
                </span>
              </div>
              {data && data.public_documents.length > 0 ? (
                <ul className="widget-list">
                  {data.public_documents.map((d) => (
                    <li key={d.id}>
                      <Icon name="download" size={13} />
                      <span className="widget-item">
                        <a href={`${API_BASE}/documents/${d.id}/download`} target="_blank" rel="noreferrer">
                          {d.title}
                        </a>
                        <span className="widget-sub">
                          {DOCUMENT_CATEGORY_LABELS[d.category]} · {fileSize(d.file_size)}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="state-note">Chưa có văn bản công khai.</p>
              )}
            </div>
          </section>

          <aside className="sidebar-column">
            <div className="block-section">
              <div className="block-title">
                <span>
                  <Icon name="bullhorn" size={15} /> Thông báo công khai
                </span>
              </div>
              {data && data.public_announcements.length > 0 ? (
                <ul className="widget-list">
                  {data.public_announcements.map((a) => (
                    <li key={a.id}>
                      <Icon name="caret-right" size={12} />
                      <span className="widget-item">
                        <strong>{a.title}</strong>
                        <span className="widget-sub">
                          {a.is_pinned ? <span className="tag-inline">Ghim</span> : null}
                          <span className={`priority-${a.priority}`}>
                            {ANNOUNCEMENT_PRIORITY_LABELS[a.priority]}
                          </span>
                          · {formatDate(a.created_at)}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="state-note">Chưa có thông báo công khai.</p>
              )}
            </div>

            <div className="block-section public-join">
              <Icon name="shield" size={28} />
              <p>Cán bộ, chiến sĩ đơn vị đăng ký tài khoản để truy cập nội dung nội bộ.</p>
              <Link to="/register" className="btn-solid">
                Đăng ký tài khoản
              </Link>
            </div>
          </aside>
        </div>
      )}
    </PublicLayout>
  )
}
