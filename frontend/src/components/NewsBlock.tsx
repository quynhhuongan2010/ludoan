import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Icon, type IconName } from './Icon'
import { SafeImage } from './SafeImage'

export interface NewsItem {
  id: number | string
  /** Đường dẫn nội bộ khi bấm vào tin. */
  to: string
  /** Nhãn chuyên mục (đã dịch sẵn). */
  category?: string | null
  title: string
  /** Tác giả / cơ quan đăng. */
  author?: string | null
  /** Ngày đăng dạng ISO. */
  date?: string | null
  /** Nhãn kỳ (VD "Tuần 36/2026") — dùng cho Giáo dục chính trị. */
  periodLabel?: string | null
  /** Ảnh đại diện (có thể null → SafeImage tự dựng khung biểu trưng). */
  imageUrl?: string | null
  /** Đoạn tóm tắt ngắn (sa-pô). */
  excerpt?: string
}

interface NewsBlockProps {
  title: string
  icon: IconName
  /** Link "Xem tất cả"; bỏ trống thì ẩn. */
  seeAllTo?: string
  items: NewsItem[]
  emptyText: string
  /** Tiêu đề khối kiểu thanh xanh đặc (như "tên báo"). */
  headingBar?: boolean
  /** Nút hành động phụ ở góc phải tiêu đề (nếu có). */
  action?: ReactNode
  /** Số ô ảnh nhỏ "tin liên quan" tối đa dưới bài tiêu điểm. */
  maxThumbs?: number
}

function formatDate(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('vi-VN')
}

function MetaLine({ item }: { item: NewsItem }) {
  const date = formatDate(item.date)
  if (!item.author && !date && !item.periodLabel) return null
  return (
    <p className="news-meta">
      {item.periodLabel ? <span className="news-meta__period">{item.periodLabel}</span> : null}
      {item.author ? (
        <span>
          <Icon name="user" size={13} />
          {item.author}
        </span>
      ) : null}
      {date ? (
        <span>
          <Icon name="calendar" size={13} />
          {date}
        </span>
      ) : null}
    </p>
  )
}

/** Tin tiêu điểm — `solo` (chỉ 1 tin: ảnh trái / chữ phải) hoặc `lead` (ảnh lớn trên cùng). */
function FeaturedCard({ item, variant }: { item: NewsItem; variant: 'solo' | 'lead' }) {
  // Khong co anh -> bo khung anh (truoc day render o trong cao ~560px voi bieu
  // trung, pha bo cuc). Chi hien tit + meta + sa-po.
  const hasImage = Boolean(item.imageUrl)
  return (
    <article
      className={`news-featured news-featured--${variant}${hasImage ? '' : ' news-featured--noimg'}`}
    >
      {hasImage ? (
        <Link to={item.to} className="news-featured__media" tabIndex={-1} aria-hidden="true">
          <SafeImage
            src={item.imageUrl}
            className="news-featured__img"
            emblemSize={variant === 'solo' ? 60 : 72}
          />
          {item.category ? <span className="news-featured__label">{item.category}</span> : null}
        </Link>
      ) : null}
      <div className="news-featured__body">
        {!hasImage && item.category ? (
          <span className="news-kicker">{item.category}</span>
        ) : null}
        <h3 className="news-featured__title">
          <Link to={item.to}>{item.title}</Link>
        </h3>
        <MetaLine item={item} />
        {item.excerpt ? <p className="news-featured__excerpt">{item.excerpt}</p> : null}
      </div>
    </article>
  )
}

/** Ô ảnh nhỏ trong dải "tin liên quan": chỉ ảnh + tiêu đề 2 dòng. */
function ThumbCard({ item }: { item: NewsItem }) {
  return (
    <div className="news-thumb">
      <Link to={item.to} className="news-thumb__media" tabIndex={-1} aria-hidden="true">
        <SafeImage src={item.imageUrl} className="news-thumb__img" emblemSize={26} />
      </Link>
      <p className="news-thumb__title">
        <Link to={item.to}>{item.title}</Link>
      </p>
    </div>
  )
}

/**
 * Khối Tin tức / Bản tin dựng theo KHUNG KIỂU TRANG BÁO, thích ứng số lượng bài:
 *  - 0 bài  → dòng trạng thái "chưa có nội dung".
 *  - 1 bài  → ảnh trái ~44%, nội dung phải ~56%.
 *  - ≥2 bài → 1 bài tiêu điểm ảnh lớn + tít + sa-pô ở trên,
 *             các bài còn lại xếp thành dải ảnh nhỏ 4 ô bên dưới.
 */
export function NewsBlock({
  title,
  icon,
  seeAllTo,
  items,
  emptyText,
  headingBar = false,
  action,
  maxThumbs = 4,
}: NewsBlockProps) {
  const [lead, ...rest] = items
  const thumbs = rest.slice(0, maxThumbs)
  // Khong tin nao co anh (vd Giao duc chinh tri) -> khung anh lon chi la o trong
  // voi bieu trung, rat pha bo cuc. Chuyen sang danh sach gon giong widget.
  const noImages = items.length > 0 && items.every((it) => !it.imageUrl)

  return (
    <div className="block-section">
      <div className={`block-title${headingBar ? ' block-title--bar' : ''}`}>
        <span>
          <Icon name={icon} size={15} /> {title}
        </span>
        {action ??
          (seeAllTo ? (
            <Link to={seeAllTo} className="see-all">
              Xem tất cả <Icon name="chevron-right" size={12} />
            </Link>
          ) : null)}
      </div>

      {!lead ? (
        <p className="state-note">{emptyText}</p>
      ) : noImages ? (
        <ul className="widget-list news-textlist">
          {items.map((item) => (
            <li key={item.id}>
              <Icon name="caret-right" size={12} />
              <span className="widget-item">
                <Link to={item.to}>{item.title}</Link>
                <span className="widget-sub">
                  {item.periodLabel ? (
                    <span className="news-meta__period">{item.periodLabel}</span>
                  ) : null}
                  {item.category ? <span>{item.category}</span> : null}
                  {formatDate(item.date) ? <span>· {formatDate(item.date)}</span> : null}
                </span>
              </span>
            </li>
          ))}
        </ul>
      ) : rest.length === 0 ? (
        <FeaturedCard item={lead} variant="solo" />
      ) : (
        <div className="news-stack">
          <FeaturedCard item={lead} variant="lead" />
          <div className="news-thumbs">
            {thumbs.map((item) => (
              <ThumbCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
