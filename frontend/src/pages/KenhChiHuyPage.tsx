import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { commandThreadsApi, officialDispatchesApi } from '../api/commandDispatches'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import {
  DISPATCH_DIRECTION_LABELS,
  DISPATCH_STATUS_LABELS,
  type CommandThread,
  type CommandThreadDetail,
  type DispatchDirection,
  type DispatchFormValues,
  type DispatchStatus,
  type OfficialDispatch,
  type OfficialDispatchDetail,
} from '../types/commandDispatch'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const fileUrl = (url: string | null) =>
  url && url.startsWith('/static') ? `${API_BASE}${url}` : url ?? ''

function when(iso: string | null): string {
  return iso
    ? new Date(iso).toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''
}
function fmtDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString('vi-VN') : '—'
}

export function KenhChiHuyPage() {
  const [tab, setTab] = useState<'hop-ban' | 'cong-van'>('hop-ban')

  return (
    <section className="kenh-chi-huy">
      <h1>
        Kênh chuyên Ban Chỉ huy &amp; Cấp uỷ{' '}
        <span className="mat-chip">
          <Icon name="lock" size={11} /> MẬT
        </span>
      </h1>
      <p className="state-note">
        Khu vực bảo mật cao dành cho Ban Chỉ huy Lữ đoàn và Cấp uỷ / Đảng bộ. Nghiêm cấm sao chụp,
        chuyển tiếp nội dung ra ngoài phạm vi được phép.
      </p>

      <div className="tab-bar">
        <button
          type="button"
          className={tab === 'hop-ban' ? 'tab active' : 'tab'}
          onClick={() => setTab('hop-ban')}
        >
          Họp bàn BCH &amp; Cấp uỷ
        </button>
        <button
          type="button"
          className={tab === 'cong-van' ? 'tab active' : 'tab'}
          onClick={() => setTab('cong-van')}
        >
          Sổ công văn mật
        </button>
      </div>

      {tab === 'hop-ban' ? <CommandThreadsTab /> : <DispatchLedgerTab />}
    </section>
  )
}

// ------------------------------------------------------------------ Tab 1: threads
function CommandThreadsTab() {
  const { isCommander, userId } = useAuth()
  const [threads, setThreads] = useState<CommandThread[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<CommandThreadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState('')
  const [body, setBody] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement | null>(null)

  // Tu dong luu ban nhap tin nhan theo tung luong (tranh mat noi dung khi
  // tai lai trang hoac chuyen qua lai giua cac luong).
  const { clearDraft } = useDraftAutosave(
    activeId != null ? `kenhchihuy-msg:${activeId}` : null,
    body,
    setBody,
  )

  function reload() {
    setLoading(true)
    commandThreadsApi
      .list()
      .then(setThreads)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không tải được danh sách'))
      .finally(() => setLoading(false))
  }
  useEffect(reload, [])

  useEffect(() => {
    if (activeId == null) {
      setDetail(null)
      return
    }
    commandThreadsApi
      .get(activeId)
      .then((d) => {
        setDetail(d)
        setThreads((prev) => prev.map((t) => (t.id === d.id ? { ...t, unread_count: 0 } : t)))
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không mở được luồng'))
  }, [activeId])

  async function createThread(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const t = await commandThreadsApi.create(newTitle)
      setThreads((p) => [t, ...p])
      setNewTitle('')
      setActiveId(t.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tạo được luồng')
    }
  }

  async function send(e: FormEvent) {
    e.preventDefault()
    if (!activeId || (!body.trim() && !file)) return
    setBusy(true)
    setError(null)
    try {
      await commandThreadsApi.postMessage(activeId, body.trim(), file)
      setBody('')
      clearDraft()
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      const d = await commandThreadsApi.get(activeId)
      setDetail(d)
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không gửi được tin')
    } finally {
      setBusy(false)
    }
  }

  async function toggleClose() {
    if (!detail) return
    try {
      const u = await commandThreadsApi.close(detail.id, !detail.is_closed)
      setDetail((d) => (d ? { ...d, is_closed: u.is_closed } : d))
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không đổi được trạng thái')
    }
  }

  return (
    <>
      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}
      <form onSubmit={createThread} className="entity-form inline-form">
        <input
          type="text"
          placeholder="Tiêu đề luồng trao đổi mới"
          maxLength={255}
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          required
        />
        <button type="submit">Tạo luồng</button>
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
                      {t.message_count} tin · {when(t.last_message_at)}
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
            <p className="state-note">Chọn một luồng để xem nội dung.</p>
          ) : (
            <>
              <div className="thread-view-head">
                <div>
                  <h2>{detail.title}</h2>
                  <p className="thread-meta">tạo bởi {detail.created_by_full_name}</p>
                </div>
                {isCommander ? (
                  <button type="button" onClick={toggleClose}>
                    {detail.is_closed ? 'Mở lại luồng' : 'Đóng luồng'}
                  </button>
                ) : null}
              </div>
              <div className="message-scroll">
                {detail.messages.map((m) => (
                  <div key={m.id} className={m.sender_id === userId ? 'msg msg-own' : 'msg'}>
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
                <form onSubmit={send} className="message-compose">
                  <textarea
                    rows={2}
                    placeholder="Nội dung trao đổi..."
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                  />
                  <div className="compose-actions">
                    <input
                      ref={fileRef}
                      type="file"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    />
                    <button type="submit" disabled={busy || (!body.trim() && !file)}>
                      Gửi
                    </button>
                  </div>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}

// ------------------------------------------------------------------ Tab 2: dispatch ledger
const emptyDispatch: DispatchFormValues = {
  direction: 'den',
  dispatch_number: '',
  summary: '',
  issuing_org: '',
  receiving_org: '',
  issued_date: '',
  received_date: '',
  status: 'moi',
  note: '',
}

function DispatchLedgerTab() {
  const { isCommander } = useAuth()
  const [list, setList] = useState<OfficialDispatch[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<OfficialDispatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<DispatchFormValues>(emptyDispatch)
  const [formFile, setFormFile] = useState<File | null>(null)
  const [editing, setEditing] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [ackNote, setAckNote] = useState('')

  function reload() {
    setLoading(true)
    officialDispatchesApi
      .list()
      .then(setList)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không tải được sổ công văn'))
      .finally(() => setLoading(false))
  }
  useEffect(reload, [])

  useEffect(() => {
    if (activeId == null) {
      setDetail(null)
      return
    }
    officialDispatchesApi
      .get(activeId)
      .then(setDetail)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không mở được công văn'))
  }, [activeId])

  function startEdit(d: OfficialDispatchDetail) {
    setEditing(d.id)
    setForm({
      direction: d.direction,
      dispatch_number: d.dispatch_number,
      summary: d.summary,
      issuing_org: d.issuing_org ?? '',
      receiving_org: d.receiving_org ?? '',
      issued_date: d.issued_date ?? '',
      received_date: d.received_date ?? '',
      status: d.status,
      note: d.note ?? '',
    })
    setFormFile(null)
  }

  async function submitForm(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const saved =
        editing != null
          ? await officialDispatchesApi.update(editing, form, formFile)
          : await officialDispatchesApi.create(form, formFile)
      setForm(emptyDispatch)
      setFormFile(null)
      setEditing(null)
      reload()
      setActiveId(saved.id)
      setDetail(saved)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không lưu được công văn')
    } finally {
      setBusy(false)
    }
  }

  async function remove(d: OfficialDispatch) {
    if (!window.confirm(`Xoá công văn số ${d.dispatch_number}?`)) return
    try {
      await officialDispatchesApi.remove(d.id)
      setActiveId(null)
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không xoá được công văn')
    }
  }

  async function acknowledge() {
    if (!detail) return
    setBusy(true)
    setError(null)
    try {
      const d = await officialDispatchesApi.acknowledge(detail.id, ackNote)
      setDetail(d)
      setAckNote('')
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không ghi nhận ký nhận được')
    } finally {
      setBusy(false)
    }
  }

  async function download(d: OfficialDispatch) {
    try {
      const blob = await officialDispatchesApi.download(d.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = d.attachment_name ?? `cong-van-${d.dispatch_number}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tải được tệp')
    }
  }

  return (
    <>
      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {isCommander ? (
        <form onSubmit={submitForm} className="entity-form">
          <h2>{editing != null ? `Sửa công văn #${editing}` : 'Vào sổ công văn mới'}</h2>
          <div className="form-row">
            <label>
              Chiều
              <select
                value={form.direction}
                onChange={(e) =>
                  setForm((f) => ({ ...f, direction: e.target.value as DispatchDirection }))
                }
              >
                {(Object.keys(DISPATCH_DIRECTION_LABELS) as DispatchDirection[]).map((d) => (
                  <option key={d} value={d}>
                    {DISPATCH_DIRECTION_LABELS[d]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Số / ký hiệu
              <input
                type="text"
                maxLength={80}
                value={form.dispatch_number}
                onChange={(e) => setForm((f) => ({ ...f, dispatch_number: e.target.value }))}
                required
              />
            </label>
            <label>
              Trạng thái
              <select
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as DispatchStatus }))}
              >
                {(Object.keys(DISPATCH_STATUS_LABELS) as DispatchStatus[]).map((s) => (
                  <option key={s} value={s}>
                    {DISPATCH_STATUS_LABELS[s]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Trích yếu
            <input
              type="text"
              maxLength={500}
              value={form.summary}
              onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
              required
            />
          </label>
          <div className="form-row">
            <label>
              Cơ quan ban hành
              <input
                type="text"
                value={form.issuing_org}
                onChange={(e) => setForm((f) => ({ ...f, issuing_org: e.target.value }))}
              />
            </label>
            <label>
              Nơi nhận
              <input
                type="text"
                value={form.receiving_org}
                onChange={(e) => setForm((f) => ({ ...f, receiving_org: e.target.value }))}
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Ngày ban hành
              <input
                type="date"
                value={form.issued_date}
                onChange={(e) => setForm((f) => ({ ...f, issued_date: e.target.value }))}
              />
            </label>
            <label>
              Ngày đến
              <input
                type="date"
                value={form.received_date}
                onChange={(e) => setForm((f) => ({ ...f, received_date: e.target.value }))}
              />
            </label>
          </div>
          <label>
            Ghi chú / nội dung
            <textarea
              rows={2}
              value={form.note}
              onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
            />
          </label>
          <label>
            Tệp đính kèm {editing != null ? '(để trống nếu giữ nguyên)' : ''}
            <input type="file" onChange={(e) => setFormFile(e.target.files?.[0] ?? null)} />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={busy}>
              {editing != null ? 'Lưu thay đổi' : 'Vào sổ'}
            </button>
            {editing != null ? (
              <button
                type="button"
                onClick={() => {
                  setEditing(null)
                  setForm(emptyDispatch)
                  setFormFile(null)
                }}
              >
                Huỷ
              </button>
            ) : null}
          </div>
        </form>
      ) : null}

      <div className="chi-dao-grid">
        <aside className="thread-list">
          {loading ? (
            <p>Đang tải...</p>
          ) : list.length === 0 ? (
            <p className="state-note">Sổ chưa có công văn nào.</p>
          ) : (
            <ul>
              {list.map((d) => (
                <li key={d.id}>
                  <button
                    type="button"
                    className={d.id === activeId ? 'thread-item active' : 'thread-item'}
                    onClick={() => setActiveId(d.id)}
                  >
                    <span className="thread-title">
                      {d.dispatch_number} — {d.summary}
                    </span>
                    <span className="thread-meta">
                      {DISPATCH_DIRECTION_LABELS[d.direction]} ·{' '}
                      <span className={`status-chip st-${d.status}`}>
                        {DISPATCH_STATUS_LABELS[d.status]}
                      </span>{' '}
                      · ký nhận {d.acknowledged_count}/{d.recipient_count}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="thread-view">
          {!detail ? (
            <p className="state-note">Chọn một công văn để xem chi tiết.</p>
          ) : (
            <>
              <div className="thread-view-head">
                <div>
                  <h2>
                    {detail.dispatch_number} — {detail.summary}
                  </h2>
                  <p className="thread-meta">
                    {DISPATCH_DIRECTION_LABELS[detail.direction]} ·{' '}
                    <span className={`status-chip st-${detail.status}`}>
                      {DISPATCH_STATUS_LABELS[detail.status]}
                    </span>{' '}
                    · vào sổ bởi {detail.created_by_full_name}
                  </p>
                </div>
                {isCommander ? (
                  <div className="row-actions">
                    <button type="button" onClick={() => startEdit(detail)}>
                      Sửa
                    </button>
                    <button type="button" onClick={() => remove(detail)}>
                      Xoá
                    </button>
                  </div>
                ) : null}
              </div>

              <dl className="profile-facts">
                <dt>Cơ quan ban hành</dt>
                <dd>{detail.issuing_org ?? '—'}</dd>
                <dt>Nơi nhận</dt>
                <dd>{detail.receiving_org ?? '—'}</dd>
                <dt>Ngày ban hành</dt>
                <dd>{fmtDate(detail.issued_date)}</dd>
                <dt>Ngày đến</dt>
                <dd>{fmtDate(detail.received_date)}</dd>
              </dl>
              {detail.note ? <p className="msg-body">{detail.note}</p> : null}
              {detail.attachment_url ? (
                <p>
                  <button type="button" onClick={() => download(detail)}>
                    <Icon name="clipboard" size={12} /> Tải tệp: {detail.attachment_name}
                  </button>
                </p>
              ) : null}

              <div className="ack-box">
                <h3>
                  Ký nhận tiếp thu ({detail.acknowledged_count}/{detail.recipient_count})
                </h3>
                {!detail.acknowledged_by_me ? (
                  <div className="ack-form">
                    <input
                      type="text"
                      placeholder="Phản hồi thực hiện (tuỳ chọn)"
                      value={ackNote}
                      onChange={(e) => setAckNote(e.target.value)}
                      maxLength={500}
                    />
                    <button type="button" onClick={acknowledge} disabled={busy}>
                      Ký nhận đã tiếp thu
                    </button>
                  </div>
                ) : (
                  <p className="form-success">Bạn đã ký nhận công văn này.</p>
                )}
                <table className="users-table">
                  <tbody>
                    {detail.acknowledged.map((a) => (
                      <tr key={a.user_id}>
                        <td>{a.full_name}</td>
                        <td>{when(a.acknowledged_at)}</td>
                        <td>{a.response_note ?? ''}</td>
                      </tr>
                    ))}
                    {detail.pending.map((a) => (
                      <tr key={a.user_id} className="ack-todo">
                        <td>{a.full_name}</td>
                        <td colSpan={2}>Chưa ký nhận</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}
