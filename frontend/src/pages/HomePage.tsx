import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { homeApi } from '../api/home'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { Icon } from '../components/Icon'
import { ANNOUNCEMENT_PRIORITY_LABELS } from '../types/announcement'
import { DIRECTIVE_STATUS_LABELS } from '../types/directive'
import { EDUCATION_CATEGORY_LABELS } from '../types/educationMaterial'
import { POST_CATEGORY_LABELS, type Post } from '../types/post'
import type { HomeSummary } from '../types/home'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function imgSrc(url: string): string {
  return url.startsWith('/static') ? `${API_BASE}${url}` : url
}

function excerpt(text: string, max = 180): string {
  const clean = text.replace(/\s+/g, ' ').trim()
  return clean.length > max ? `${clean.slice(0, max)}…` : clean
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN')
}

function HeroPost({ post }: { post: Post }) {
  return (
    <div className="hero-news">
      {post.cover_image_url ? (
        <img src={imgSrc(post.cover_image_url)} alt="" className="hero-img" />
      ) : (
        <div className="hero-img img-placeholder" aria-hidden="true">
          <Icon name="newspaper" size={44} />
        </div>
      )}
      <div className="hero-info">
        <div className="badge-row">
          <span className="post-category">{POST_CATEGORY_LABELS[post.category]}</span>
          <ClassificationBadge value={post.classification} />
        </div>
        <h2>
          <Link to="/tin-tuc">{post.title}</Link>
        </h2>
        <p className="post-meta">
          {post.author_full_name} · {formatDate(post.created_at)}
        </p>
        <p>{excerpt(post.content)}</p>
      </div>
    </div>
  )
}

export function HomePage() {
  const [data, setData] = useState<HomeSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    homeApi
      .summary(6)
      .then(setData)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải dữ liệu trang chủ'),
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="state-note">Đang tải dữ liệu trang chủ...</p>
  if (error) return <p className="state-note form-error">{error}</p>
  if (!data) return null

  const [heroPost, ...restPosts] = data.latest_posts
  const subPosts = restPosts.slice(0, 4)
  const [heroEdu, ...restEdu] = data.latest_education_materials

  return (
    <div className="layout-grid">
      <section className="main-column">
        <div className="block-section">
          <div className="block-title">
            <span>
              <Icon name="newspaper" size={15} /> Tin tức – Hoạt động đơn vị
            </span>
            <Link to="/tin-tuc" className="see-all">
              Xem tất cả <Icon name="chevron-right" size={12} />
            </Link>
          </div>

          {heroPost ? (
            <>
              <HeroPost post={heroPost} />
              {subPosts.length > 0 ? (
                <div className="sub-grid">
                  {subPosts.map((post) => (
                    <article key={post.id} className="sub-card">
                      {post.cover_image_url ? (
                        <img src={imgSrc(post.cover_image_url)} alt="" />
                      ) : (
                        <div className="sub-thumb img-placeholder" aria-hidden="true">
                          <Icon name="newspaper" size={22} />
                        </div>
                      )}
                      <h3>
                        <Link to="/tin-tuc">{post.title}</Link>
                      </h3>
                    </article>
                  ))}
                </div>
              ) : null}
            </>
          ) : (
            <p className="state-note">Chưa có tin tức nào được đăng.</p>
          )}
        </div>

        <div className="block-section">
          <div className="block-title">
            <span>
              <Icon name="book" size={15} /> Giáo dục chính trị
            </span>
            <Link to="/giao-duc-chinh-tri" className="see-all">
              Xem tất cả <Icon name="chevron-right" size={12} />
            </Link>
          </div>

          {heroEdu ? (
            <>
              <div className="hero-news">
                <div className="hero-img img-placeholder" aria-hidden="true">
                  <Icon name="book" size={44} />
                </div>
                <div className="hero-info">
                  <span className="post-category">{EDUCATION_CATEGORY_LABELS[heroEdu.category]}</span>
                  <h2>
                    <Link to="/giao-duc-chinh-tri">{heroEdu.title}</Link>
                  </h2>
                  <p className="post-meta">
                    {heroEdu.period_label ? `${heroEdu.period_label} · ` : ''}
                    {heroEdu.author_full_name} · {formatDate(heroEdu.created_at)}
                  </p>
                  <p>{excerpt(heroEdu.content)}</p>
                </div>
              </div>
              {restEdu.length > 0 ? (
                <ul className="widget-list">
                  {restEdu.slice(0, 4).map((item) => (
                    <li key={item.id}>
                      <Icon name="caret-right" size={12} />
                      <Link to="/giao-duc-chinh-tri">
                        {item.title}
                        {item.period_label ? <span className="tag-inline"> {item.period_label}</span> : null}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : (
            <p className="state-note">Chưa có tài liệu giáo dục chính trị.</p>
          )}
        </div>
      </section>

      <aside className="sidebar-column">
        <div className="block-section">
          <div className="block-title">
            <span>
              <Icon name="bullhorn" size={15} /> Thông báo nội bộ
            </span>
          </div>
          {data.latest_announcements.length > 0 ? (
            <ul className="widget-list">
              {data.latest_announcements.map((a) => (
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
            <p className="state-note">Chưa có thông báo.</p>
          )}
        </div>

        <div className="block-section">
          <div className="block-title">
            <span>
              <Icon name="clipboard" size={15} /> Chỉ thị – Nhiệm vụ mới
            </span>
            <Link to="/chi-thi-nhiem-vu" className="see-all">
              Xem tất cả <Icon name="chevron-right" size={12} />
            </Link>
          </div>
          {data.latest_directives.length > 0 ? (
            <ul className="widget-list">
              {data.latest_directives.map((d) => (
                <li key={d.id}>
                  <Icon name="caret-right" size={12} />
                  <span className="widget-item">
                    <Link to="/chi-thi-nhiem-vu">{d.title}</Link>
                    <span className="widget-sub">
                      <span className={`status-badge status-${d.status}`}>
                        {DIRECTIVE_STATUS_LABELS[d.status]}
                      </span>
                      <ClassificationBadge value={d.classification} />
                      {' '}
                      {d.status === 'da_ban_hanh' ? (
                        <span className={d.acknowledged_by_me ? 'ack-done' : 'ack-todo'}>
                          {d.acknowledged_by_me ? 'Bạn đã tiếp thu' : 'Chưa tiếp thu'} ·{' '}
                          {d.acknowledged_count}/{d.recipient_count} quán triệt
                        </span>
                      ) : null}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="state-note">Chưa có chỉ thị – nhiệm vụ nào.</p>
          )}
        </div>

        <div className="block-section">
          <div className="block-title">
            <span>
              <Icon name="file" size={15} /> Tài liệu mới cập nhật
            </span>
          </div>
          {data.latest_education_materials.length > 0 ? (
            <ul className="widget-list">
              {data.latest_education_materials.map((item) => (
                <li key={item.id}>
                  <Icon name="file" size={13} />
                  {item.attachment_url ? (
                    <a href={item.attachment_url} target="_blank" rel="noreferrer">
                      {item.title}
                    </a>
                  ) : (
                    <Link to="/giao-duc-chinh-tri">{item.title}</Link>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="state-note">Chưa có tài liệu.</p>
          )}
        </div>
      </aside>
    </div>
  )
}
