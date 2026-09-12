import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { homeApi } from '../api/home'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { Icon } from '../components/Icon'
import { NewsBlock, type NewsItem } from '../components/NewsBlock'
import { ANNOUNCEMENT_PRIORITY_LABELS } from '../types/announcement'
import { DIRECTIVE_STATUS_LABELS } from '../types/directive'
import { EDUCATION_CATEGORY_LABELS } from '../types/educationMaterial'
import { POST_CATEGORY_LABELS } from '../types/post'
import type { HomeSummary } from '../types/home'
import { absolutizeStaticUrl, excerptFromHtml } from '../utils/richContent'

function imgSrc(url: string | null): string | null {
  return url ? absolutizeStaticUrl(url) : null
}

const excerpt = (html: string, max = 200) => excerptFromHtml(html, max)

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN')
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

  const postItems: NewsItem[] = data.latest_posts.map((post) => ({
    id: post.id,
    to: '/tin-tuc',
    category: POST_CATEGORY_LABELS[post.category],
    title: post.title,
    author: post.author_full_name,
    date: post.created_at,
    imageUrl: imgSrc(post.cover_image_url),
    excerpt: post.summary?.trim() || excerpt(post.content),
  }))

  const eduItems: NewsItem[] = data.latest_education_materials.map((item) => ({
    id: item.id,
    to: '/giao-duc-chinh-tri',
    category: EDUCATION_CATEGORY_LABELS[item.category],
    title: item.title,
    author: item.author_full_name,
    date: item.created_at,
    periodLabel: item.period_label,
    imageUrl: null,
    excerpt: excerpt(item.content),
  }))

  return (
    <div className="layout-grid">
      <section className="main-column">
        <NewsBlock
          title="Tin tức – Hoạt động đơn vị"
          icon="newspaper"
          seeAllTo="/tin-tuc"
          items={postItems}
          emptyText="Chưa có tin tức nào được đăng."
          headingBar
        />

        <NewsBlock
          title="Giáo dục chính trị"
          icon="book"
          seeAllTo="/giao-duc-chinh-tri"
          items={eduItems}
          emptyText="Chưa có tài liệu giáo dục chính trị."
          headingBar
        />
      </section>

      <aside className="sidebar-column">
        <div className="block-section">
          <div className="block-title block-title--bar">
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
          <div className="block-title block-title--bar">
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
          <div className="block-title block-title--bar">
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
