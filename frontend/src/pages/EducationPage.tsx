import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { educationMaterialsApi } from '../api/educationMaterials'
import { EmptyState } from '../components/EmptyState'
import { Icon, type IconName } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { RichContent } from '../components/RichContent'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import {
  EDUCATION_CATEGORY_LABELS,
  type EducationCategory,
  type EducationMaterial,
} from '../types/educationMaterial'
import { absolutizeStaticUrl, excerptFromHtml } from '../utils/richContent'

const CATEGORIES = Object.keys(EDUCATION_CATEGORY_LABELS) as EducationCategory[]
const PAGE_SIZE_OPTIONS = [6, 9, 12, 24]
type SortMode = 'recent' | 'oldest' | 'period'

/** Mo ta chuyen muc: icon + mau nhan dien (theo phong cach cong TT don vi). */
const CATEGORY_META: Record<EducationCategory, { icon: IconName; tone: string }> = {
  hoc_tap_chinh_tri_quan_su: { icon: 'book-open', tone: 'green' },
  tuyen_truyen: { icon: 'bullhorn', tone: 'red' },
  phap_luat_bien_gioi: { icon: 'scale', tone: 'blue' },
  lich_su_truyen_thong: { icon: 'landmark', tone: 'gold' },
}

const IMAGE_RE = /\.(jpe?g|png|webp|gif)(\?.*)?$/i
const VIDEO_RE = /\.(mp4|webm|ogg)(\?.*)?$/i

function attachmentKind(url: string): 'image' | 'video' | 'file' {
  if (IMAGE_RE.test(url)) return 'image'
  if (VIDEO_RE.test(url)) return 'video'
  return 'file'
}

function AttachmentBlock({ url }: { url: string }) {
  const src = absolutizeStaticUrl(url)
  const kind = attachmentKind(url)
  if (kind === 'image') {
    return (
      <figure className="rich-content edu-attach-fig">
        <img src={src} alt="Tài liệu đính kèm" />
        <figcaption>
          <Icon name="image" size={12} /> Tài liệu đính kèm
        </figcaption>
      </figure>
    )
  }
  if (kind === 'video') {
    return (
      <figure className="rich-content edu-attach-fig">
        <video controls preload="metadata" src={src} />
        <figcaption>
          <Icon name="video" size={12} /> Video đính kèm
        </figcaption>
      </figure>
    )
  }
  return (
    <a className="edu-attach-file" href={src} target="_blank" rel="noreferrer">
      <Icon name="paperclip" size={15} />
      <span>Tài liệu học tập đính kèm</span>
      <Icon name="download" size={13} />
    </a>
  )
}

export function EducationPage() {
  const { canEditContent, isCommander, userId } = useAuth()
  const navigate = useNavigate()
  const confirm = useConfirm()

  const [materials, setMaterials] = useState<EducationMaterial[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeId, setActiveId] = useState<number | null>(null)
  const [category, setCategory] = useState<EducationCategory | ''>('')
  const [period, setPeriod] = useState('')
  const [search, setSearch] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('recent')
  const [pageSize, setPageSize] = useState(9)
  const [page, setPage] = useState(0)

  function loadMaterials() {
    setLoading(true)
    educationMaterialsApi
      .list({ limit: 500 })
      .then(setMaterials)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải nội dung'),
      )
      .finally(() => setLoading(false))
  }
  useEffect(loadMaterials, [])

  const detail = useMemo(
    () => materials.find((m) => m.id === activeId) ?? null,
    [materials, activeId],
  )

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const m of materials) c[m.category] = (c[m.category] ?? 0) + 1
    return c
  }, [materials])

  const periods = useMemo(() => {
    const set = new Set<string>()
    for (const m of materials) if (m.period_label) set.add(m.period_label)
    return Array.from(set).sort((a, b) => b.localeCompare(a, 'vi', { numeric: true }))
  }, [materials])

  const stats = useMemo(
    () => ({
      total: materials.length,
      withAttachment: materials.filter((m) => m.attachment_url).length,
      periodic: materials.filter((m) => m.period_label).length,
    }),
    [materials],
  )

  const visible = useMemo(() => {
    const kw = search.trim().toLowerCase()
    const rows = materials.filter((m) => {
      if (category && m.category !== category) return false
      if (period && m.period_label !== period) return false
      if (!kw) return true
      return (
        m.title.toLowerCase().includes(kw) ||
        (m.author_full_name ?? '').toLowerCase().includes(kw) ||
        (m.period_label ?? '').toLowerCase().includes(kw) ||
        m.content.toLowerCase().includes(kw)
      )
    })
    rows.sort((a, b) => {
      if (sortMode === 'oldest')
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      if (sortMode === 'period')
        return (b.period_label ?? '').localeCompare(a.period_label ?? '', 'vi', { numeric: true })
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
    return rows
  }, [materials, category, period, search, sortMode])

  const total = visible.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const pageItems = visible.slice(safePage * pageSize, safePage * pageSize + pageSize)

  useEffect(() => {
    setPage(0)
  }, [category, period, search, sortMode, pageSize])

  function canManage(m: EducationMaterial) {
    return isCommander || m.author_id === userId
  }

  async function handleDelete(id: number) {
    const m = materials.find((x) => x.id === id)
    const ok = await confirm({
      message: (
        <>
          Xoá nội dung <strong>{m?.title ?? `#${id}`}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await educationMaterialsApi.remove(id)
      setMaterials((prev) => prev.filter((x) => x.id !== id))
      if (activeId === id) setActiveId(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá nội dung')
    }
  }

  return (
    <section className="edu-page">
      <div className="crumb-bar">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Cổng thông tin</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">Giáo dục chính trị</span>
        </nav>
      </div>

      <header className="cdb-head">
        <div>
          <h1>
            <Icon name="book-open" size={22} /> Giáo dục chính trị
          </h1>
          <p className="state-note">
            Tài liệu, nội dung sinh hoạt chính trị – tư tưởng, tuyên truyền chủ trương, pháp luật
            biên giới và lịch sử – truyền thống đơn vị. Nội dung định kỳ được gắn nhãn tuần/tháng.
          </p>
        </div>
        <div className="cdb-head-actions">
          <button type="button" className="btn-cancel" onClick={loadMaterials} disabled={loading}>
            <Icon name="undo" size={14} /> Làm mới
          </button>
          {canEditContent ? (
            <button
              type="button"
              className="btn-create"
              onClick={() => navigate('/giao-duc-chinh-tri/moi')}
            >
              <Icon name="plus" size={16} /> Đăng nội dung mới
            </button>
          ) : null}
        </div>
      </header>

      <div className="cdb-stats">
        <div className="cdb-stat">
          <span className="cdb-stat-value">{stats.total}</span>
          <span className="cdb-stat-label">Tổng nội dung</span>
        </div>
        <div className="cdb-stat cdb-stat-open">
          <span className="cdb-stat-value">{CATEGORIES.length}</span>
          <span className="cdb-stat-label">Chuyên mục</span>
        </div>
        <div className="cdb-stat cdb-stat-done">
          <span className="cdb-stat-value">{stats.periodic}</span>
          <span className="cdb-stat-label">Nội dung định kỳ</span>
        </div>
        <div className="cdb-stat cdb-stat-closed">
          <span className="cdb-stat-value">{stats.withAttachment}</span>
          <span className="cdb-stat-label">Có tài liệu đính kèm</span>
        </div>
      </div>

      <div className="edu-cats" role="tablist" aria-label="Chuyên mục">
        <button
          type="button"
          role="tab"
          aria-selected={category === ''}
          className={category === '' ? 'edu-cat active' : 'edu-cat'}
          onClick={() => setCategory('')}
        >
          <Icon name="layers" size={16} />
          <span>Tất cả</span>
          <em>{materials.length}</em>
        </button>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            type="button"
            role="tab"
            aria-selected={category === c}
            className={
              category === c
                ? `edu-cat active tone-${CATEGORY_META[c].tone}`
                : `edu-cat tone-${CATEGORY_META[c].tone}`
            }
            onClick={() => setCategory(c)}
          >
            <Icon name={CATEGORY_META[c].icon} size={16} />
            <span>{EDUCATION_CATEGORY_LABELS[c]}</span>
            <em>{categoryCounts[c] ?? 0}</em>
          </button>
        ))}
      </div>

      {error ? (
        <p role="alert" className="form-error cdb-alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      <div className="cdb-grid">
        <aside className="cdb-sidebar">
          <div className="cdb-toolbar">
            <div className="cdb-search">
              <Icon name="search" size={14} />
              <input
                type="search"
                placeholder="Tìm theo tiêu đề, kỳ, người đăng, nội dung..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="cdb-toolbar-row">
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                aria-label="Lọc theo kỳ"
              >
                <option value="">Mọi kỳ / đợt</option>
                {periods.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as SortMode)}
                aria-label="Sắp xếp"
              >
                <option value="recent">Mới nhất</option>
                <option value="oldest">Cũ nhất</option>
                <option value="period">Theo kỳ</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="cdb-skeleton-list">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="cdb-skeleton-row" />
              ))}
            </div>
          ) : materials.length === 0 ? (
            <EmptyState icon="book" message="Chưa có nội dung nào." />
          ) : total === 0 ? (
            <EmptyState icon="search" message="Không có nội dung nào khớp bộ lọc / từ khoá." />
          ) : (
            <>
              <ul className="edu-list">
                {pageItems.map((m) => {
                  const meta = CATEGORY_META[m.category]
                  return (
                    <li key={m.id}>
                      <button
                        type="button"
                        className={m.id === activeId ? 'edu-item active' : 'edu-item'}
                        onClick={() => setActiveId(m.id)}
                      >
                        <span className={`edu-item-icon tone-${meta.tone}`}>
                          <Icon name={meta.icon} size={16} />
                        </span>
                        <span className="edu-item-main">
                          <span className="edu-item-kicker">
                            {EDUCATION_CATEGORY_LABELS[m.category]}
                          </span>
                          <span className="edu-item-title">{m.title}</span>
                          <span className="edu-item-excerpt">
                            {excerptFromHtml(m.content, 120)}
                          </span>
                          <span className="edu-item-meta">
                            {m.period_label ? (
                              <span className="chip chip-role">
                                <Icon name="calendar" size={11} /> {m.period_label}
                              </span>
                            ) : null}
                            <span>
                              <Icon name="user" size={11} /> {m.author_full_name}
                            </span>
                            <span>
                              <Icon name="clock" size={11} />{' '}
                              {new Date(m.created_at).toLocaleDateString('vi-VN')}
                            </span>
                            {m.attachment_url ? <Icon name="paperclip" size={11} /> : null}
                          </span>
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
              <Pagination
                page={safePage}
                pageCount={pageCount}
                total={total}
                pageSize={pageSize}
                onPage={setPage}
                onPageSize={setPageSize}
                pageSizeOptions={PAGE_SIZE_OPTIONS}
                itemLabel="nội dung"
              />
            </>
          )}
        </aside>

        <div className="cdb-conversation edu-reader">
          {!detail ? (
            <div className="cdb-conv-empty">
              <Icon name="book-open" size={44} />
              <p>Chọn một nội dung ở danh sách bên trái để đọc toàn văn.</p>
            </div>
          ) : (
            <>
              <div className="cdb-conv-head">
                <div className="cdb-conv-title">
                  <div className="edu-reader-kicker">
                    <span className={`edu-item-icon tone-${CATEGORY_META[detail.category].tone}`}>
                      <Icon name={CATEGORY_META[detail.category].icon} size={14} />
                    </span>
                    {EDUCATION_CATEGORY_LABELS[detail.category]}
                    {detail.period_label ? (
                      <span className="chip chip-role">
                        <Icon name="calendar" size={11} /> {detail.period_label}
                      </span>
                    ) : null}
                  </div>
                  <h2>{detail.title}</h2>
                  <div className="cdb-conv-sub">
                    <span className="cdb-conv-by">
                      <Icon name="user" size={11} /> {detail.author_full_name} ·{' '}
                      {new Date(detail.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                </div>
                {canManage(detail) ? (
                  <div className="cdb-conv-actions">
                    <button
                      type="button"
                      className="btn-edit"
                      onClick={() => navigate(`/giao-duc-chinh-tri/${detail.id}/sua`)}
                    >
                      <Icon name="edit" size={13} /> Sửa
                    </button>
                    <button
                      type="button"
                      className="btn-delete"
                      onClick={() => handleDelete(detail.id)}
                    >
                      <Icon name="trash" size={13} /> Xoá
                    </button>
                  </div>
                ) : null}
              </div>

              <div className="edu-reader-body">
                <RichContent html={detail.content} />
                {detail.attachment_url ? <AttachmentBlock url={detail.attachment_url} /> : null}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}
