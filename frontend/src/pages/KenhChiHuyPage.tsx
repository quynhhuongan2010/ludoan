import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { commandThreadsApi, officialDispatchesApi } from '../api/commandDispatches'
import { usersApi } from '../api/users'
import { EmptyState } from '../components/EmptyState'
import { Icon } from '../components/Icon'
import { LeadershipWorkdeskSection } from '../components/LeadershipWorkdeskSection'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import {
  DISPATCH_DIRECTION_LABELS,
  DISPATCH_STATUS_LABELS,
  DOC_TYPE_LABELS,
  DOC_VISIBILITY_LABELS,
  SECURITY_LEVEL_LABELS,
  URGENCY_LABELS,
  type CommandThread,
  type CommandThreadDetail,
  type CommandThreadDocument,
  type CommandThreadMinutes,
  type DispatchDirection,
  type DispatchStatus,
  type DocType,
  type DocVisibility,
  type OfficialDispatch,
  type OfficialDispatchDetail,
} from '../types/commandDispatch'
import type { User } from '../types/user'

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

const PAGE_SIZE_OPTIONS = [5, 10, 20]

const TAB_LABELS = {
  'chi-dao': 'Bàn làm việc Chỉ đạo BCH',
  'hop-ban': 'Họp bàn BCH & Cấp uỷ',
  'cong-van': 'Sổ công văn mật',
} as const

export function KenhChiHuyPage() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const rawTab = params.get('tab')
  const tab: 'chi-dao' | 'hop-ban' | 'cong-van' =
    rawTab === 'hop-ban' ? 'hop-ban' : rawTab === 'cong-van' ? 'cong-van' : 'chi-dao'
  const setTab = (t: 'chi-dao' | 'hop-ban' | 'cong-van') =>
    setParams(t === 'chi-dao' ? {} : { tab: t }, { replace: true })

  return (
    <section className="kenh-chi-huy">
      <div className="crumb-bar">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Kênh chỉ huy (MẬT)</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">{TAB_LABELS[tab]}</span>
        </nav>
      </div>

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
          className={tab === 'chi-dao' ? 'tab active' : 'tab'}
          onClick={() => setTab('chi-dao')}
        >
          <Icon name="star" size={13} /> Bàn làm việc Chỉ đạo BCH
        </button>
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

      {tab === 'chi-dao' ? (
        <LeadershipWorkdeskSection />
      ) : tab === 'hop-ban' ? (
        <CommandThreadsTab />
      ) : (
        <DispatchLedgerTab />
      )}
    </section>
  )
}

// ------------------------------------------------------------------ Tab 1: threads
function CommandThreadsTab() {
  const { isCommander, userId } = useAuth()
  const confirm = useConfirm()
  const [threads, setThreads] = useState<CommandThread[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<CommandThreadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [newTitle, setNewTitle] = useState('')
  const [newMemberIds, setNewMemberIds] = useState<number[]>([])
  const [body, setBody] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement | null>(null)

  // Thanh phan (thanh vien) cua luong dang mo
  const [addMemberId, setAddMemberId] = useState('')
  const [memberBusy, setMemberBusy] = useState(false)

  // Kho van ban cua luong dang mo
  const [documents, setDocuments] = useState<CommandThreadDocument[]>([])
  const [docTitle, setDocTitle] = useState('')
  const [docVisibility, setDocVisibility] = useState<DocVisibility>('chung')
  const [docFile, setDocFile] = useState<File | null>(null)
  const [uploadingDoc, setUploadingDoc] = useState(false)
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null)
  const docFileRef = useRef<HTMLInputElement | null>(null)

  // Bien ban thao luan (tu ghep tu lich su tin nhan)
  const [minutesList, setMinutesList] = useState<CommandThreadMinutes[]>([])
  const [generatingMinutes, setGeneratingMinutes] = useState(false)
  const [openMinutesId, setOpenMinutesId] = useState<number | null>(null)

  // Tim kiem + loc + phan trang danh sach luong (client-side)
  const [threadSearch, setThreadSearch] = useState('')
  const [threadStatusFilter, setThreadStatusFilter] = useState<'' | 'open' | 'closed'>('')
  const [pageSize, setPageSize] = useState(10)
  const [currentPage, setCurrentPage] = useState(0)

  // Tu dong luu ban nhap tin nhan theo tung luong (tranh mat noi dung khi
  // tai lai trang hoac chuyen qua lai giua cac luong).
  const { clearDraft } = useDraftAutosave(
    activeId != null ? `kenhchihuy-msg:${activeId}` : null,
    body,
    setBody,
  )

  function reload() {
    setLoading(true)
    Promise.all([
      commandThreadsApi.list(),
      isCommander ? usersApi.list({ active: true }).then((p) => p.items) : Promise.resolve<User[]>([]),
    ])
      .then(([ts, us]) => {
        setThreads(ts)
        setUsers(us)
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không tải được danh sách'))
      .finally(() => setLoading(false))
  }
  useEffect(reload, [isCommander])

  const filteredThreads = useMemo(() => {
    const kw = threadSearch.trim().toLowerCase()
    return threads.filter((t) => {
      if (threadStatusFilter === 'open' && t.is_closed) return false
      if (threadStatusFilter === 'closed' && !t.is_closed) return false
      if (!kw) return true
      return t.title.toLowerCase().includes(kw)
    })
  }, [threads, threadSearch, threadStatusFilter])

  const threadTotal = filteredThreads.length
  const threadPageCount = Math.max(1, Math.ceil(threadTotal / pageSize))
  const threadPage = Math.min(currentPage, threadPageCount - 1)
  const threadPageItems = filteredThreads.slice(
    threadPage * pageSize,
    threadPage * pageSize + pageSize,
  )

  useEffect(() => {
    setCurrentPage(0)
  }, [threadSearch, threadStatusFilter, pageSize])

  useEffect(() => {
    if (activeId == null) {
      setDetail(null)
      setDocuments([])
      setMinutesList([])
      return
    }
    commandThreadsApi
      .get(activeId)
      .then((d) => {
        setDetail(d)
        setThreads((prev) => prev.map((t) => (t.id === d.id ? { ...t, unread_count: 0 } : t)))
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không mở được luồng'))
    commandThreadsApi
      .listDocuments(activeId)
      .then(setDocuments)
      .catch(() => setDocuments([]))
    commandThreadsApi
      .listMinutes(activeId)
      .then(setMinutesList)
      .catch(() => setMinutesList([]))
    setOpenMinutesId(null)
  }, [activeId])

  async function createThread(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const t = await commandThreadsApi.create(newTitle, newMemberIds)
      setThreads((p) => [t, ...p])
      setNewTitle('')
      setNewMemberIds([])
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

  async function addMember() {
    if (!detail || !addMemberId) return
    setMemberBusy(true)
    setError(null)
    try {
      const d = await commandThreadsApi.addMembers(detail.id, [Number(addMemberId)])
      setDetail(d)
      setAddMemberId('')
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không gán được thành phần')
    } finally {
      setMemberBusy(false)
    }
  }

  async function removeMember(userIdToRemove: number) {
    if (!detail) return
    const member = detail.members.find((m) => m.user_id === userIdToRemove)
    const ok = await confirm({
      title: 'Xác nhận gỡ thành phần',
      confirmText: 'Gỡ',
      message: (
        <>
          Gỡ <strong>{member?.full_name ?? 'thành viên này'}</strong> khỏi thành phần trao đổi của
          luồng này?
        </>
      ),
    })
    if (!ok) return
    setMemberBusy(true)
    setError(null)
    try {
      await commandThreadsApi.removeMember(detail.id, userIdToRemove)
      setDetail((d) =>
        d ? { ...d, members: d.members.filter((m) => m.user_id !== userIdToRemove) } : d,
      )
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không gỡ được thành phần')
    } finally {
      setMemberBusy(false)
    }
  }

  async function uploadDoc(e: FormEvent) {
    e.preventDefault()
    if (!activeId || !docFile) return
    setUploadingDoc(true)
    setError(null)
    try {
      const doc = await commandThreadsApi.uploadDocument(activeId, docTitle, docVisibility, docFile)
      setDocuments((prev) => [doc, ...prev])
      setDocTitle('')
      setDocVisibility('chung')
      setDocFile(null)
      if (docFileRef.current) docFileRef.current.value = ''
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tải lên được văn bản')
    } finally {
      setUploadingDoc(false)
    }
  }

  async function downloadDoc(doc: CommandThreadDocument) {
    if (!activeId) return
    setDownloadingDocId(doc.id)
    setError(null)
    try {
      const blob = await commandThreadsApi.downloadDocument(activeId, doc.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.file_name
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tải được tệp')
    } finally {
      setDownloadingDocId(null)
    }
  }

  async function downloadMsgAttachment(messageId: number) {
    if (!activeId) return
    setError(null)
    try {
      const blob = await commandThreadsApi.downloadMessageAttachment(activeId, messageId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tep-tin-nhan-${messageId}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tải được tệp đính kèm')
    }
  }

  async function removeDoc(doc: CommandThreadDocument) {
    if (!activeId) return
    const ok = await confirm({
      message: (
        <>
          Xoá văn bản <strong>{doc.title}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await commandThreadsApi.removeDocument(activeId, doc.id)
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không xoá được văn bản')
    }
  }

  async function generateMinutes() {
    if (!activeId) return
    setGeneratingMinutes(true)
    setError(null)
    try {
      const m = await commandThreadsApi.generateMinutes(activeId)
      setMinutesList((prev) => [m, ...prev])
      setOpenMinutesId(m.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tạo được biên bản')
    } finally {
      setGeneratingMinutes(false)
    }
  }

  const notMembers = detail ? users.filter((u) => !detail.members.some((m) => m.user_id === u.id)) : []

  return (
    <>
      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}
      <form onSubmit={createThread} className="entity-form">
        <label>
          Tiêu đề luồng trao đổi mới
          <input
            type="text"
            placeholder="VD: Trao đổi phương án huấn luyện quý IV"
            maxLength={255}
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            required
          />
        </label>
        {isCommander ? (
          <fieldset className="unit-picker member-picker">
            <legend>
              Thành phần (tuỳ chọn — bạn luôn tự động có trong luồng do mình tạo)
            </legend>
            {users
              .filter((u) => u.id !== userId)
              .map((u) => (
                <label key={u.id} className="switch-cell">
                  <input
                    type="checkbox"
                    checked={newMemberIds.includes(u.id)}
                    onChange={(e) =>
                      setNewMemberIds((prev) =>
                        e.target.checked ? [...prev, u.id] : prev.filter((x) => x !== u.id),
                      )
                    }
                  />
                  {u.full_name} ({u.username})
                </label>
              ))}
          </fieldset>
        ) : (
          <p className="state-note">
            Luồng chỉ hiện với thành phần được gán. Sau khi tạo, nhờ Ban chỉ huy gán thêm người
            tham gia nếu cần.
          </p>
        )}
        <div className="form-actions">
          <button type="submit" className="btn-submit">
            Tạo luồng
          </button>
        </div>
      </form>

      <div className="list-panel">
        <div className="list-toolbar">
          <input
            type="search"
            placeholder="Tìm theo tiêu đề luồng..."
            value={threadSearch}
            onChange={(e) => setThreadSearch(e.target.value)}
          />
          <select
            value={threadStatusFilter}
            onChange={(e) => setThreadStatusFilter(e.target.value as '' | 'open' | 'closed')}
          >
            <option value="">Tất cả trạng thái</option>
            <option value="open">Đang mở</option>
            <option value="closed">Đã đóng</option>
          </select>
        </div>

        {loading ? (
          <p className="state-note">Đang tải...</p>
        ) : threads.length === 0 ? (
          <EmptyState icon="clipboard" message="Hiện chưa có luồng trao đổi nào" />
        ) : threadTotal === 0 ? (
          <EmptyState icon="search" message="Không có luồng nào khớp bộ lọc / từ khoá" />
        ) : (
          <>
            <ul className="entity-rows">
              {threadPageItems.map((t) => (
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
                      {t.message_count} tin · {t.member_count} thành phần · {when(t.last_message_at)}
                    </span>
                    {t.unread_count > 0 ? (
                      <span className="badge-unread">{t.unread_count}</span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
            <Pagination
              page={threadPage}
              pageCount={threadPageCount}
              total={threadTotal}
              pageSize={pageSize}
              onPage={setCurrentPage}
              onPageSize={setPageSize}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              itemLabel="luồng"
            />
          </>
        )}
      </div>

      {detail ? (
        <div className="thread-view entity-detail">
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

              <div className="block-section">
                <strong>Thành phần ({detail.members.length})</strong>
                <div className="member-chips">
                  {detail.members.map((m) => (
                    <span key={m.user_id} className="chip">
                      {m.full_name}
                      {m.unit_name ? <em> · {m.unit_name}</em> : null}
                      {isCommander && m.user_id !== detail.created_by_id ? (
                        <button
                          type="button"
                          className="chip-remove"
                          title="Gỡ khỏi thành phần"
                          disabled={memberBusy}
                          onClick={() => removeMember(m.user_id)}
                        >
                          <Icon name="x" size={11} />
                        </button>
                      ) : null}
                    </span>
                  ))}
                </div>
                {isCommander && notMembers.length > 0 ? (
                  <div className="inline-form">
                    <select value={addMemberId} onChange={(e) => setAddMemberId(e.target.value)}>
                      <option value="">— Gán thêm thành phần —</option>
                      {notMembers.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.full_name} ({u.username})
                        </option>
                      ))}
                    </select>
                    <button type="button" disabled={memberBusy || !addMemberId} onClick={addMember}>
                      Gán
                    </button>
                  </div>
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
                      <button
                        type="button"
                        className="btn-text-link"
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--primary, #0f5132)',
                          cursor: 'pointer',
                          padding: 0,
                          font: 'inherit',
                          fontSize: '0.85rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          textDecoration: 'underline',
                        }}
                        onClick={() => downloadMsgAttachment(m.id)}
                      >
                        <Icon name="clipboard" size={12} /> Tệp đính kèm (Bảo mật)
                      </button>
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

              <div className="block-section">
                <strong>Kho văn bản ({documents.length})</strong>
                {documents.length === 0 ? (
                  <p className="state-note">Chưa có văn bản nào được chia sẻ trong luồng.</p>
                ) : (
                  <ul className="doc-list">
                    {documents.map((doc) => (
                      <li key={doc.id} className="doc-row">
                        <div className="doc-row-main">
                          <span className="doc-title">{doc.title}</span>
                          <span className={`chip ${doc.visibility === 'rieng' ? 'chip-mat' : ''}`}>
                            {DOC_VISIBILITY_LABELS[doc.visibility]}
                          </span>
                        </div>
                        <span className="thread-meta">
                          {doc.file_name} · {doc.uploaded_by_full_name} · {when(doc.created_at)}
                        </span>
                        <div className="row-actions">
                          <button
                            type="button"
                            className="btn-approve"
                            disabled={downloadingDocId === doc.id}
                            onClick={() => downloadDoc(doc)}
                          >
                            <Icon name="download" size={12} />{' '}
                            {downloadingDocId === doc.id ? 'Đang tải...' : 'Tải về'}
                          </button>
                          {isCommander || doc.uploaded_by_id === userId ? (
                            <button type="button" className="btn-delete" onClick={() => removeDoc(doc)}>
                              <Icon name="trash" /> Xoá
                            </button>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                {!detail.is_closed ? (
                  <form onSubmit={uploadDoc} className="inline-form doc-upload-form">
                    <input
                      type="text"
                      placeholder="Tiêu đề văn bản (bỏ trống = lấy tên tệp)"
                      maxLength={255}
                      value={docTitle}
                      onChange={(e) => setDocTitle(e.target.value)}
                    />
                    <select
                      value={docVisibility}
                      onChange={(e) => setDocVisibility(e.target.value as DocVisibility)}
                    >
                      <option value="chung">Chung (cả luồng xem)</option>
                      <option value="rieng">Riêng (chỉ tôi + BCH)</option>
                    </select>
                    <input
                      ref={docFileRef}
                      type="file"
                      required
                      onChange={(e) => setDocFile(e.target.files?.[0] ?? null)}
                    />
                    <button type="submit" disabled={uploadingDoc || !docFile}>
                      {uploadingDoc ? 'Đang tải lên...' : 'Chia sẻ văn bản'}
                    </button>
                  </form>
                ) : null}
              </div>

              <div className="block-section">
                <strong>Biên bản thảo luận</strong>
                <p className="state-note">
                  Tự động ghép toàn bộ tin nhắn của luồng (kèm văn bản dùng chung) thành 1 bản
                  biên bản có cấu trúc — không dùng AI.
                </p>
                <div className="form-actions">
                  <button type="button" disabled={generatingMinutes} onClick={generateMinutes}>
                    {generatingMinutes ? 'Đang tạo...' : 'Tạo biên bản'}
                  </button>
                </div>
                {minutesList.length === 0 ? (
                  <p className="state-note">Chưa có biên bản nào được tạo.</p>
                ) : (
                  <ul className="minutes-list">
                    {minutesList.map((m) => (
                      <li key={m.id} className="minutes-item">
                        <button
                          type="button"
                          className="minutes-item-head"
                          onClick={() => setOpenMinutesId((id) => (id === m.id ? null : m.id))}
                        >
                          <span>
                            Biên bản #{m.id} — {when(m.generated_at)} · {m.message_count} tin nhắn
                          </span>
                          <span className="thread-meta">bởi {m.generated_by_full_name}</span>
                        </button>
                        {openMinutesId === m.id ? (
                          <pre className="minutes-content">{m.content}</pre>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
          </>
        </div>
      ) : null}
    </>
  )
}

// ------------------------------------------------------------------ Tab 2: dispatch ledger
function DispatchLedgerTab() {
  const { isCommander } = useAuth()
  const confirm = useConfirm()
  const navigate = useNavigate()
  const [list, setList] = useState<OfficialDispatch[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<OfficialDispatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [busy, setBusy] = useState(false)
  const [ackNote, setAckNote] = useState('')

  // Tim kiem + loc + phan trang so cong van (client-side)
  const [dispatchSearch, setDispatchSearch] = useState('')
  const [directionFilter, setDirectionFilter] = useState<'' | DispatchDirection>('')
  const [docTypeFilter, setDocTypeFilter] = useState<'' | DocType>('')
  const [statusFilter, setStatusFilter] = useState<'' | DispatchStatus>('')
  const [pageSize, setPageSize] = useState(10)
  const [currentPage, setCurrentPage] = useState(0)

  function reload() {
    setLoading(true)
    officialDispatchesApi
      .list()
      .then(setList)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không tải được sổ công văn'))
      .finally(() => setLoading(false))
  }
  useEffect(reload, [])

  const filteredList = useMemo(() => {
    const kw = dispatchSearch.trim().toLowerCase()
    return list.filter((d) => {
      if (directionFilter && d.direction !== directionFilter) return false
      if (docTypeFilter && d.doc_type !== docTypeFilter) return false
      if (statusFilter && d.status !== statusFilter) return false
      if (!kw) return true
      return (
        d.dispatch_number.toLowerCase().includes(kw) ||
        d.summary.toLowerCase().includes(kw) ||
        (d.issuing_org ?? '').toLowerCase().includes(kw) ||
        (d.receiving_org ?? '').toLowerCase().includes(kw) ||
        (d.signer ?? '').toLowerCase().includes(kw)
      )
    })
  }, [list, dispatchSearch, directionFilter, docTypeFilter, statusFilter])

  const dispatchTotal = filteredList.length
  const dispatchPageCount = Math.max(1, Math.ceil(dispatchTotal / pageSize))
  const dispatchPage = Math.min(currentPage, dispatchPageCount - 1)
  const dispatchPageItems = filteredList.slice(
    dispatchPage * pageSize,
    dispatchPage * pageSize + pageSize,
  )

  useEffect(() => {
    setCurrentPage(0)
  }, [dispatchSearch, directionFilter, docTypeFilter, statusFilter, pageSize])

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

  async function remove(d: OfficialDispatch) {
    const ok = await confirm({
      message: (
        <>
          Xoá công văn số <strong>{d.dispatch_number}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
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
        <div className="actions-bar">
          <button
            type="button"
            className="btn-create"
            onClick={() => navigate('/kenh-chi-huy/cong-van/moi')}
          >
            <Icon name="upload" size={16} /> Vào sổ công văn
          </button>
        </div>
      ) : null}

      <div className="list-panel">
        <div className="list-toolbar">
          <input
            type="search"
            placeholder="Tìm theo số/ký hiệu, trích yếu, cơ quan, người ký..."
            value={dispatchSearch}
            onChange={(e) => setDispatchSearch(e.target.value)}
          />
          <select
            value={directionFilter}
            onChange={(e) => setDirectionFilter(e.target.value as '' | DispatchDirection)}
          >
            <option value="">Cả 2 chiều</option>
            {(Object.keys(DISPATCH_DIRECTION_LABELS) as DispatchDirection[]).map((d) => (
              <option key={d} value={d}>
                {DISPATCH_DIRECTION_LABELS[d]}
              </option>
            ))}
          </select>
          <select
            value={docTypeFilter}
            onChange={(e) => setDocTypeFilter(e.target.value as '' | DocType)}
          >
            <option value="">Mọi loại văn bản</option>
            {(Object.keys(DOC_TYPE_LABELS) as DocType[]).map((d) => (
              <option key={d} value={d}>
                {DOC_TYPE_LABELS[d]}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as '' | DispatchStatus)}
          >
            <option value="">Tất cả trạng thái</option>
            {(Object.keys(DISPATCH_STATUS_LABELS) as DispatchStatus[]).map((s) => (
              <option key={s} value={s}>
                {DISPATCH_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="state-note">Đang tải...</p>
        ) : list.length === 0 ? (
          <EmptyState icon="clipboard" message="Sổ chưa có công văn nào" />
        ) : dispatchTotal === 0 ? (
          <EmptyState icon="search" message="Không có công văn nào khớp bộ lọc / từ khoá" />
        ) : (
          <>
            <ul className="entity-rows">
              {dispatchPageItems.map((d) => (
                <li key={d.id}>
                  <button
                    type="button"
                    className={d.id === activeId ? 'thread-item active' : 'thread-item'}
                    onClick={() => setActiveId(d.id)}
                  >
                    <span className="thread-title">
                      [{DOC_TYPE_LABELS[d.doc_type]}] {d.dispatch_number} — {d.summary}
                    </span>
                    <span className="thread-meta">
                      {DISPATCH_DIRECTION_LABELS[d.direction]} ·{' '}
                      <span className={`status-chip st-${d.status}`}>
                        {DISPATCH_STATUS_LABELS[d.status]}
                      </span>{' '}
                      · {SECURITY_LEVEL_LABELS[d.security_level]}
                      {d.urgency !== 'thuong' ? ` · ${URGENCY_LABELS[d.urgency]}` : ''} · ký nhận{' '}
                      {d.acknowledged_count}/{d.recipient_count}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            <Pagination
              page={dispatchPage}
              pageCount={dispatchPageCount}
              total={dispatchTotal}
              pageSize={pageSize}
              onPage={setCurrentPage}
              onPageSize={setPageSize}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              itemLabel="công văn"
            />
          </>
        )}
      </div>

      {detail ? (
        <div className="thread-view entity-detail">
          <>
              <div className="thread-view-head">
                <div>
                  <h2>
                    [{DOC_TYPE_LABELS[detail.doc_type]}] {detail.dispatch_number} — {detail.summary}
                  </h2>
                  <p className="thread-meta">
                    {DISPATCH_DIRECTION_LABELS[detail.direction]} ·{' '}
                    <span className={`status-chip st-${detail.status}`}>
                      {DISPATCH_STATUS_LABELS[detail.status]}
                    </span>{' '}
                    · Độ mật: {SECURITY_LEVEL_LABELS[detail.security_level]} · Độ khẩn:{' '}
                    {URGENCY_LABELS[detail.urgency]} · vào sổ bởi {detail.created_by_full_name}
                  </p>
                </div>
                {isCommander ? (
                  <div className="row-actions">
                    <button
                      type="button"
                      className="btn-edit"
                      onClick={() => navigate(`/kenh-chi-huy/cong-van/${detail.id}/sua`)}
                    >
                      <Icon name="edit" /> Sửa
                    </button>
                    <button type="button" className="btn-delete" onClick={() => remove(detail)}>
                      <Icon name="trash" /> Xoá
                    </button>
                  </div>
                ) : null}
              </div>

              <dl className="profile-facts">
                <dt>Loại văn bản</dt>
                <dd>{DOC_TYPE_LABELS[detail.doc_type]}</dd>
                <dt>Cơ quan ban hành</dt>
                <dd>{detail.issuing_org ?? '—'}</dd>
                <dt>Nơi nhận</dt>
                <dd>{detail.receiving_org ?? '—'}</dd>
                <dt>Người ký</dt>
                <dd>{detail.signer ?? '—'}</dd>
                <dt>Ngày ban hành</dt>
                <dd>{fmtDate(detail.issued_date)}</dd>
                <dt>Ngày đến</dt>
                <dd>{fmtDate(detail.received_date)}</dd>
                <dt>Hạn xử lý</dt>
                <dd>{fmtDate(detail.deadline)}</dd>
                <dt>Số tờ</dt>
                <dd>{detail.page_count ?? '—'}</dd>
                <dt>Số hồ sơ lưu trữ</dt>
                <dd>{detail.archive_ref ?? '—'}</dd>
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
        </div>
      ) : null}
    </>
  )
}
