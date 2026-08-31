import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { directiveThreadsApi } from '../api/directiveThreads'
import { unitsApi } from '../api/units'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import type { DirectiveThread, DirectiveThreadDetail } from '../types/directiveThread'
import type { Unit } from '../types/unit'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const fileUrl = (url: string | null) =>
  url && url.startsWith('/static') ? `${API_BASE}${url}` : url ?? ''

function when(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function ChiDaoBaoCaoPage() {
  const { isCommander, userId } = useAuth()

  const [threads, setThreads] = useState<DirectiveThread[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<DirectiveThreadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [newTitle, setNewTitle] = useState('')
  const [newUnitId, setNewUnitId] = useState<string>('')
  const [creating, setCreating] = useState(false)

  const [body, setBody] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [sending, setSending] = useState(false)
  const fileRef = useRef<HTMLInputElement | null>(null)

  // Tu dong luu ban nhap tin nhan/bao cao theo tung luong (tranh mat noi
  // dung khi tai lai trang hoac chuyen qua lai giua cac luong).
  const { clearDraft } = useDraftAutosave(
    activeId != null ? `chidao-msg:${activeId}` : null,
    body,
    setBody,
  )

  function loadThreads() {
    setLoading(true)
    const jobs: [Promise<DirectiveThread[]>, Promise<Unit[]>] = [
      directiveThreadsApi.list(),
      isCommander ? unitsApi.list({ active: true }) : Promise.resolve([]),
    ]
    Promise.all(jobs)
      .then(([ts, us]) => {
        setThreads(ts)
        setUnits(us)
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không tải được danh sách luồng'),
      )
      .finally(() => setLoading(false))
  }

  useEffect(loadThreads, [isCommander])

  useEffect(() => {
    if (activeId == null) {
      setDetail(null)
      return
    }
    directiveThreadsApi
      .get(activeId)
      .then((d) => {
        setDetail(d)
        setThreads((prev) => prev.map((t) => (t.id === d.id ? { ...t, unread_count: 0 } : t)))
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không mở được luồng'),
      )
  }, [activeId])

  const totalUnread = useMemo(
    () => threads.reduce((s, t) => s + t.unread_count, 0),
    [threads],
  )

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const created = await directiveThreadsApi.create({
        title: newTitle,
        unit_id: isCommander ? (newUnitId ? Number(newUnitId) : null) : undefined,
      })
      setThreads((prev) => [created, ...prev])
      setNewTitle('')
      setNewUnitId('')
      setActiveId(created.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tạo được luồng')
    } finally {
      setCreating(false)
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault()
    if (!activeId) return
    if (!body.trim() && !file) return
    setError(null)
    setSending(true)
    try {
      await directiveThreadsApi.postMessage(activeId, body.trim(), file)
      setBody('')
      clearDraft()
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      const d = await directiveThreadsApi.get(activeId)
      setDetail(d)
      setThreads((prev) =>
        prev.map((t) =>
          t.id === d.id
            ? { ...t, message_count: d.message_count, last_message_at: d.last_message_at, unread_count: 0 }
            : t,
        ),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không gửi được tin')
    } finally {
      setSending(false)
    }
  }

  async function toggleClose() {
    if (!detail) return
    setError(null)
    try {
      const updated = await directiveThreadsApi.close(detail.id, !detail.is_closed)
      setDetail((d) => (d ? { ...d, is_closed: updated.is_closed } : d))
      setThreads((prev) =>
        prev.map((t) => (t.id === updated.id ? { ...t, is_closed: updated.is_closed } : t)),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không đổi được trạng thái luồng')
    }
  }

  return (
    <section className="chi-dao-page">
      <h1>
        Kênh Chỉ đạo – Báo cáo{' '}
        {totalUnread > 0 ? <span className="badge-unread">{totalUnread}</span> : null}
      </h1>
      <p className="state-note">
        <Icon name="lock" size={12} /> Trao đổi & báo cáo hai chiều giữa Ban chỉ huy Lữ đoàn và đơn
        vị. Chỉ tài khoản được cấp quyền kênh mới truy cập được. Đơn vị cấp dưới chỉ thấy luồng của
        đơn vị mình.
      </p>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleCreate} className="entity-form inline-form">
        <input
          type="text"
          placeholder="Tiêu đề luồng mới (VD: Báo cáo SSCĐ tuần 35)"
          maxLength={255}
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          required
        />
        {isCommander ? (
          <select value={newUnitId} onChange={(e) => setNewUnitId(e.target.value)} required>
            <option value="">— Chọn đơn vị —</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        ) : null}
        <button type="submit" disabled={creating}>
          Tạo luồng
        </button>
      </form>

      <div className="chi-dao-grid">
        <aside className="thread-list">
          {loading ? (
            <p>Đang tải...</p>
          ) : threads.length === 0 ? (
            <p className="state-note">Chưa có luồng nào.</p>
          ) : (
            <ul>
              {threads.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    className={t.id === activeId ? 'thread-item active' : 'thread-item'}
                    onClick={() => setActiveId(t.id)}
                  >
                    <span className="thread-title">
                      {t.title}
                      {t.is_closed ? ' (đã đóng)' : ''}
                    </span>
                    <span className="thread-meta">
                      {t.unit_name} · {t.message_count} tin · {when(t.last_message_at)}
                    </span>
                    {t.unread_count > 0 ? (
                      <span className="badge-unread">{t.unread_count}</span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="thread-view">
          {!detail ? (
            <p className="state-note">Chọn một luồng để xem nội dung trao đổi.</p>
          ) : (
            <>
              <div className="thread-view-head">
                <div>
                  <h2>{detail.title}</h2>
                  <p className="thread-meta">
                    {detail.unit_name} · tạo bởi {detail.created_by_full_name}
                  </p>
                </div>
                {isCommander ? (
                  <button type="button" onClick={toggleClose}>
                    {detail.is_closed ? 'Mở lại luồng' : 'Đóng luồng'}
                  </button>
                ) : null}
              </div>

              <div className="message-scroll">
                {detail.messages.map((m) => (
                  <div
                    key={m.id}
                    className={m.sender_id === userId ? 'msg msg-own' : 'msg'}
                  >
                    <div className="msg-head">
                      <strong>{m.sender_full_name}</strong> <span>{when(m.created_at)}</span>
                    </div>
                    {m.body ? <p className="msg-body">{m.body}</p> : null}
                    {m.attachment_url ? (
                      <a href={fileUrl(m.attachment_url)} target="_blank" rel="noreferrer">
                        <Icon name="clipboard" size={12} /> Tệp đính kèm
                      </a>
                    ) : null}
                  </div>
                ))}
                {detail.messages.length === 0 ? (
                  <p className="state-note">Chưa có tin nhắn.</p>
                ) : null}
              </div>

              {detail.is_closed ? (
                <p className="state-note">Luồng đã đóng — không thể gửi thêm.</p>
              ) : (
                <form onSubmit={handleSend} className="message-compose">
                  <textarea
                    rows={2}
                    placeholder="Nhập nội dung trao đổi / báo cáo..."
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                  />
                  <div className="compose-actions">
                    <input
                      ref={fileRef}
                      type="file"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    />
                    <button type="submit" disabled={sending || (!body.trim() && !file)}>
                      Gửi
                    </button>
                  </div>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}
