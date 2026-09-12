import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { announcementsApi } from '../api/announcements'
import { EmptyState } from '../components/EmptyState'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { usePagination } from '../hooks/usePagination'
import { useRequiredFields } from '../hooks/useRequiredFields'
import {
  ANNOUNCEMENT_PRIORITY_LABELS,
  type Announcement,
  type AnnouncementCreate,
  type AnnouncementPriority,
} from '../types/announcement'

const priorities = Object.keys(ANNOUNCEMENT_PRIORITY_LABELS) as AnnouncementPriority[]

const emptyAnnouncement: AnnouncementCreate = {
  title: '',
  content: '',
  priority: 'binh_thuong',
  is_pinned: false,
  is_public: false,
  starts_at: null,
  ends_at: null,
}

/** ISO -> gia tri cho <input type="datetime-local"> (yyyy-MM-ddTHH:mm). */
function toLocalInput(iso: string | null | undefined): string {
  return iso ? iso.slice(0, 16) : ''
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN')
}

function formatDateTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('vi-VN') : '—'
}

export function AnnouncementsPage() {
  const { canEditContent, isCommander, userId } = useAuth()
  const confirm = useConfirm()

  const [items, setItems] = useState<Announcement[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterPriority, setFilterPriority] = useState<AnnouncementPriority | ''>('')

  const {
    page,
    pageSize,
    pageCount,
    total,
    pageItems,
    setPageIndex,
    setPageSize,
    showPagination,
  } = usePagination(items, 15, filterPriority)

  const [form, setForm] = useState<AnnouncementCreate>(emptyAnnouncement)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const req = useRequiredFields(['title', 'content'] as const)

  function loadAnnouncements() {
    setLoading(true)
    announcementsApi
      .list(filterPriority ? { priority: filterPriority } : undefined)
      .then(setItems)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải thông báo'),
      )
      .finally(() => setLoading(false))
  }

  useEffect(loadAnnouncements, [filterPriority])

  function canManage(item: { author_id: number }) {
    return isCommander || item.author_id === userId
  }

  function startCreate() {
    setEditingId(null)
    setForm(emptyAnnouncement)
    setShowForm(true)
  }

  function startEdit(item: Announcement) {
    setEditingId(item.id)
    setForm({
      title: item.title,
      content: item.content,
      priority: item.priority,
      is_pinned: item.is_pinned,
      is_public: item.is_public,
      starts_at: item.starts_at,
      ends_at: item.ends_at,
    })
    setShowForm(true)
  }

  function cancelForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyAnnouncement)
    req.reset()
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ title: form.title, content: form.content })) return
    setSubmitting(true)
    try {
      const payload: AnnouncementCreate = {
        ...form,
        starts_at: form.starts_at || null,
        ends_at: form.ends_at || null,
      }
      if (editingId !== null) {
        const updated = await announcementsApi.update(editingId, payload)
        setItems((prev) => prev.map((a) => (a.id === editingId ? updated : a)))
      } else {
        const created = await announcementsApi.create(payload)
        setItems((prev) => [created, ...prev])
      }
      cancelForm()
      loadAnnouncements()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu thông báo')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    const item = items.find((a) => a.id === id)
    const ok = await confirm({
      message: (
        <>
          Xoá thông báo <strong>{item?.title ?? `#${id}`}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await announcementsApi.remove(id)
      setItems((prev) => prev.filter((a) => a.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá thông báo')
    }
  }

  return (
    <section>
      <h1>Thông báo nội bộ</h1>
      <p className="state-note">
        Lịch trực kíp đã chuyển sang trang riêng: <strong>Lịch trực – Kíp trực</strong> trong menu
        Bản tin.
      </p>

      <div className="post-toolbar">
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value as AnnouncementPriority | '')}
        >
          <option value="">Tất cả mức độ</option>
          {priorities.map((p) => (
            <option key={p} value={p}>
              {ANNOUNCEMENT_PRIORITY_LABELS[p]}
            </option>
          ))}
        </select>

        {canEditContent && !showForm ? (
          <button type="button" onClick={startCreate}>
            Đăng thông báo mới
          </button>
        ) : null}
      </div>

      {showForm ? (
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
            Mức độ ưu tiên
            <select
              value={form.priority}
              onChange={(e) =>
                setForm((f) => ({ ...f, priority: e.target.value as AnnouncementPriority }))
              }
            >
              {priorities.map((p) => (
                <option key={p} value={p}>
                  {ANNOUNCEMENT_PRIORITY_LABELS[p]}
                </option>
              ))}
            </select>
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.is_pinned}
              onChange={(e) => setForm((f) => ({ ...f, is_pinned: e.target.checked }))}
            />
            Ghim lên đầu danh sách
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.is_public}
              onChange={(e) => setForm((f) => ({ ...f, is_public: e.target.checked }))}
            />
            Công khai (khách chưa đăng nhập xem được)
          </label>
          <div className="datetime-row">
            <label>
              Bắt đầu hiển thị
              <input
                type="datetime-local"
                value={toLocalInput(form.starts_at)}
                onChange={(e) => setForm((f) => ({ ...f, starts_at: e.target.value || null }))}
              />
            </label>
            <label>
              Kết thúc hiển thị
              <input
                type="datetime-local"
                value={toLocalInput(form.ends_at)}
                onChange={(e) => setForm((f) => ({ ...f, ends_at: e.target.value || null }))}
              />
            </label>
          </div>
          <Field label="Nội dung" required req={req} name="content">
            <textarea
              rows={6}
              value={form.content}
              onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
              onBlur={(e) => req.mark('content', e.target.value)}
              required
            />
          </Field>
          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {editingId !== null ? 'Cập nhật' : 'Đăng thông báo'}
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
      ) : items.length === 0 ? (
        <EmptyState icon="bullhorn" message="Chưa có thông báo nào." />
      ) : (
        <>
        <div className="post-list">
          {pageItems.map((item) => (
            <article key={item.id} className="post-card">
              <div className="post-card-body">
                <div className="badge-row">
                  {item.is_pinned ? <span className="tag-inline">Ghim</span> : null}
                  <span className={`priority-${item.priority}`}>
                    {ANNOUNCEMENT_PRIORITY_LABELS[item.priority]}
                  </span>
                  {item.is_public ? <span className="tag-inline">Công khai</span> : null}
                </div>
                <h2>{item.title}</h2>
                <p className="post-meta">
                  {item.author_full_name} · {formatDate(item.created_at)}
                  {item.starts_at || item.ends_at ? (
                    <>
                      {' '}
                      · Hiển thị {formatDateTime(item.starts_at)} → {formatDateTime(item.ends_at)}
                    </>
                  ) : null}
                </p>
                <p style={{ whiteSpace: 'pre-wrap' }}>{item.content}</p>
                {canManage(item) ? (
                  <div className="row-actions">
                    <button type="button" className="btn-edit" onClick={() => startEdit(item)}>
                      <Icon name="edit" /> Sửa
                    </button>
                    <button type="button" className="btn-delete" onClick={() => handleDelete(item.id)}>
                      <Icon name="trash" /> Xoá
                    </button>
                  </div>
                ) : null}
              </div>
            </article>
          ))}
        </div>
        {showPagination ? (
          <Pagination
            page={page}
            pageCount={pageCount}
            total={total}
            pageSize={pageSize}
            onPage={setPageIndex}
            onPageSize={setPageSize}
            pageSizeOptions={[10, 15, 30, 50]}
            itemLabel="thông báo"
          />
        ) : null}
        </>
      )}
    </section>
  )
}
