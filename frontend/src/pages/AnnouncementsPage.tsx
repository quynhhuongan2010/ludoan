import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { announcementsApi } from '../api/announcements'
import { dutySchedulesApi } from '../api/dutySchedules'
import { useAuth } from '../context/AuthContext'
import {
  ANNOUNCEMENT_PRIORITY_LABELS,
  type Announcement,
  type AnnouncementCreate,
  type AnnouncementPriority,
} from '../types/announcement'
import type { DutySchedule, DutyScheduleCreate } from '../types/dutySchedule'

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

const emptyDuty: DutyScheduleCreate = {
  duty_date: '',
  shift: '',
  duty_officer: '',
  role_title: '',
  note: '',
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

  // ----- Thong bao noi bo -----
  const [items, setItems] = useState<Announcement[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterPriority, setFilterPriority] = useState<AnnouncementPriority | ''>('')

  const [form, setForm] = useState<AnnouncementCreate>(emptyAnnouncement)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)

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
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
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
    setError(null)
    try {
      await announcementsApi.remove(id)
      setItems((prev) => prev.filter((a) => a.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá thông báo')
    }
  }

  // ----- Lich truc kip -----
  const [duties, setDuties] = useState<DutySchedule[]>([])
  const [dutyLoading, setDutyLoading] = useState(true)
  const [dutyError, setDutyError] = useState<string | null>(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [dutyForm, setDutyForm] = useState<DutyScheduleCreate>(emptyDuty)
  const [dutyEditingId, setDutyEditingId] = useState<number | null>(null)
  const [dutySubmitting, setDutySubmitting] = useState(false)
  const [showDutyForm, setShowDutyForm] = useState(false)

  function loadDuties() {
    setDutyLoading(true)
    dutySchedulesApi
      .list({ dateFrom: dateFrom || undefined, dateTo: dateTo || undefined })
      .then(setDuties)
      .catch((err: unknown) =>
        setDutyError(err instanceof ApiError ? err.message : 'Không thể tải lịch trực'),
      )
      .finally(() => setDutyLoading(false))
  }

  useEffect(loadDuties, [dateFrom, dateTo])

  function startDutyCreate() {
    setDutyEditingId(null)
    setDutyForm(emptyDuty)
    setShowDutyForm(true)
  }

  function startDutyEdit(duty: DutySchedule) {
    setDutyEditingId(duty.id)
    setDutyForm({
      duty_date: duty.duty_date,
      shift: duty.shift,
      duty_officer: duty.duty_officer,
      role_title: duty.role_title,
      note: duty.note ?? '',
    })
    setShowDutyForm(true)
  }

  function cancelDutyForm() {
    setShowDutyForm(false)
    setDutyEditingId(null)
    setDutyForm(emptyDuty)
  }

  async function handleDutySubmit(event: FormEvent) {
    event.preventDefault()
    setDutyError(null)
    setDutySubmitting(true)
    try {
      const payload: DutyScheduleCreate = { ...dutyForm, note: dutyForm.note || null }
      if (dutyEditingId !== null) {
        const updated = await dutySchedulesApi.update(dutyEditingId, payload)
        setDuties((prev) => prev.map((d) => (d.id === dutyEditingId ? updated : d)))
      } else {
        const created = await dutySchedulesApi.create(payload)
        setDuties((prev) => [...prev, created])
      }
      cancelDutyForm()
      loadDuties()
    } catch (err) {
      setDutyError(err instanceof ApiError ? err.message : 'Không thể lưu lịch trực')
    } finally {
      setDutySubmitting(false)
    }
  }

  async function handleDutyDelete(id: number) {
    setDutyError(null)
    try {
      await dutySchedulesApi.remove(id)
      setDuties((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setDutyError(err instanceof ApiError ? err.message : 'Không thể xoá lịch trực')
    }
  }

  return (
    <div>
      <section>
        <h1>Thông báo nội bộ</h1>

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
          <p>Chưa có thông báo nào.</p>
        ) : (
          <div className="post-list">
            {items.map((item) => (
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
                      <button type="button" onClick={() => startEdit(item)}>
                        Sửa
                      </button>
                      <button type="button" onClick={() => handleDelete(item.id)}>
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

      <section style={{ marginTop: '2.5rem' }}>
        <h1>Lịch trực kíp</h1>

        <div className="post-toolbar">
          <span className="filter-inline">
            <label>
              Từ ngày
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </label>
            <label>
              Đến ngày
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </label>
          </span>

          {canEditContent && !showDutyForm ? (
            <button type="button" onClick={startDutyCreate}>
              Thêm ca trực
            </button>
          ) : null}
        </div>

        {showDutyForm ? (
          <form onSubmit={handleDutySubmit} className="entity-form">
            <label>
              Ngày trực
              <input
                type="date"
                value={dutyForm.duty_date}
                onChange={(e) => setDutyForm((f) => ({ ...f, duty_date: e.target.value }))}
                required
              />
            </label>
            <label>
              Ca / kíp
              <input
                type="text"
                maxLength={50}
                value={dutyForm.shift}
                onChange={(e) => setDutyForm((f) => ({ ...f, shift: e.target.value }))}
                placeholder="VD: Ca ngày, Ca đêm, 06:00–18:00"
                required
              />
            </label>
            <label>
              Người trực
              <input
                type="text"
                maxLength={100}
                value={dutyForm.duty_officer}
                onChange={(e) => setDutyForm((f) => ({ ...f, duty_officer: e.target.value }))}
                required
              />
            </label>
            <label>
              Cương vị trực
              <input
                type="text"
                maxLength={100}
                value={dutyForm.role_title}
                onChange={(e) => setDutyForm((f) => ({ ...f, role_title: e.target.value }))}
                placeholder="VD: Trực ban tác chiến, Trực chỉ huy"
                required
              />
            </label>
            <label>
              Ghi chú
              <textarea
                rows={3}
                maxLength={500}
                value={dutyForm.note ?? ''}
                onChange={(e) => setDutyForm((f) => ({ ...f, note: e.target.value }))}
              />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={dutySubmitting}>
                {dutyEditingId !== null ? 'Cập nhật' : 'Thêm ca trực'}
              </button>
              <button type="button" onClick={cancelDutyForm}>
                Huỷ
              </button>
            </div>
          </form>
        ) : null}

        {dutyError ? (
          <p role="alert" className="form-error">
            {dutyError}
          </p>
        ) : null}

        {dutyLoading ? (
          <p>Đang tải...</p>
        ) : duties.length === 0 ? (
          <p>Chưa có ca trực nào trong khoảng thời gian đã chọn.</p>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ngày</th>
                  <th>Ca / kíp</th>
                  <th>Cương vị</th>
                  <th>Người trực</th>
                  <th>Ghi chú</th>
                  {canEditContent ? <th aria-label="Thao tác" /> : null}
                </tr>
              </thead>
              <tbody>
                {duties.map((duty) => (
                  <tr key={duty.id}>
                    <td>{formatDate(duty.duty_date)}</td>
                    <td>{duty.shift}</td>
                    <td>{duty.role_title}</td>
                    <td>{duty.duty_officer}</td>
                    <td>{duty.note ?? '—'}</td>
                    {canEditContent ? (
                      <td>
                        {canManage(duty) ? (
                          <div className="row-actions">
                            <button type="button" onClick={() => startDutyEdit(duty)}>
                              Sửa
                            </button>
                            <button type="button" onClick={() => handleDutyDelete(duty.id)}>
                              Xoá
                            </button>
                          </div>
                        ) : null}
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
