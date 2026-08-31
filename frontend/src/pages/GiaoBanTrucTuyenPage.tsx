import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { commandMeetingsApi } from '../api/commandMeetings'
import { usersApi } from '../api/users'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { useDraftAutosave } from '../hooks/useDraftAutosave'
import {
  ATTENDANCE_LABELS,
  MEETING_STATUS_LABELS,
  type Attendee,
  type AttendanceStatus,
  type CommandMeeting,
  type CommandMeetingCreate,
  type CommandMeetingDetail,
  type MeetingStatus,
} from '../types/commandMeeting'
import type { User } from '../types/user'

function fmt(iso: string | null): string {
  return iso
    ? new Date(iso).toLocaleString('vi-VN', {
        weekday: 'short',
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'
}

const ATT_OPTIONS = Object.keys(ATTENDANCE_LABELS) as AttendanceStatus[]
const STATUS_OPTIONS = Object.keys(MEETING_STATUS_LABELS) as MeetingStatus[]

const emptyCreate: Omit<CommandMeetingCreate, 'attendee_user_ids'> = {
  title: '',
  start_time: '',
  end_time: '',
  location: '',
  meeting_link: '',
  agenda: '',
}

export function GiaoBanTrucTuyenPage() {
  const { isCommander } = useAuth()
  const [list, setList] = useState<CommandMeeting[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<CommandMeetingDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState(emptyCreate)
  const [invitees, setInvitees] = useState<number[]>([])
  const [creating, setCreating] = useState(false)

  function reload() {
    setLoading(true)
    Promise.all([
      commandMeetingsApi.list(),
      isCommander ? usersApi.list({ active: true }) : Promise.resolve([]),
    ])
      .then(([ms, us]) => {
        setList(ms)
        setUsers(us)
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không tải được lịch giao ban'))
      .finally(() => setLoading(false))
  }
  useEffect(reload, [isCommander])

  function openDetail(id: number) {
    setActiveId(id)
    commandMeetingsApi
      .get(id)
      .then(setDetail)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : 'Không mở được cuộc họp'))
  }
  function refreshDetail() {
    if (activeId != null) openDetail(activeId)
    reload()
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const created = await commandMeetingsApi.create({
        ...form,
        end_time: form.end_time || null,
        location: form.location || null,
        meeting_link: form.meeting_link || null,
        agenda: form.agenda || null,
        attendee_user_ids: invitees,
      })
      setForm(emptyCreate)
      setInvitees([])
      reload()
      setActiveId(created.id)
      setDetail(created)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tạo được cuộc họp')
    } finally {
      setCreating(false)
    }
  }

  return (
    <section className="kenh-chi-huy">
      <h1>
        Giao ban trực tuyến{' '}
        <span className="mat-chip">
          <Icon name="lock" size={11} /> MẬT
        </span>
      </h1>
      <p className="state-note">
        Lịch giao ban / họp Chỉ huy &amp; Cấp uỷ. Phần mềm không tự dựng hạ tầng video — bấm “Vào
        phòng trực tuyến” để mở liên kết phòng họp ngoài do Ban chỉ huy cung cấp.
      </p>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {isCommander ? (
        <form onSubmit={handleCreate} className="entity-form">
          <h2>Tạo cuộc họp / giao ban</h2>
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
          <div className="form-row">
            <label>
              Bắt đầu
              <input
                type="datetime-local"
                value={form.start_time}
                onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
                required
              />
            </label>
            <label>
              Kết thúc (dự kiến)
              <input
                type="datetime-local"
                value={form.end_time ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Địa điểm / phòng họp
              <input
                type="text"
                value={form.location ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
              />
            </label>
            <label>
              Liên kết phòng trực tuyến
              <input
                type="url"
                placeholder="https://..."
                value={form.meeting_link ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, meeting_link: e.target.value }))}
              />
            </label>
          </div>
          <label>
            Chương trình / nội dung
            <textarea
              rows={3}
              value={form.agenda ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, agenda: e.target.value }))}
            />
          </label>
          <fieldset className="unit-picker">
            <legend>Thành phần triệu tập</legend>
            {users.map((u) => (
              <label key={u.id} className="switch-cell">
                <input
                  type="checkbox"
                  checked={invitees.includes(u.id)}
                  onChange={(e) =>
                    setInvitees((prev) =>
                      e.target.checked ? [...prev, u.id] : prev.filter((x) => x !== u.id),
                    )
                  }
                />
                {u.full_name} ({u.username})
              </label>
            ))}
          </fieldset>
          <div className="form-actions">
            <button type="submit" disabled={creating}>
              Tạo cuộc họp
            </button>
          </div>
        </form>
      ) : null}

      <div className="chi-dao-grid">
        <aside className="thread-list">
          {loading ? (
            <p>Đang tải...</p>
          ) : list.length === 0 ? (
            <p className="state-note">Chưa có cuộc họp nào.</p>
          ) : (
            <ul>
              {list.map((m) => (
                <li key={m.id}>
                  <button
                    type="button"
                    className={m.id === activeId ? 'thread-item active' : 'thread-item'}
                    onClick={() => openDetail(m.id)}
                  >
                    <span className="thread-title">{m.title}</span>
                    <span className="thread-meta">
                      <span className={`status-chip st-${m.status}`}>
                        {MEETING_STATUS_LABELS[m.status]}
                      </span>{' '}
                      · {fmt(m.start_time)} · {m.present_count}/{m.attendee_count} có mặt
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="thread-view">
          {!detail ? (
            <p className="state-note">Chọn một cuộc họp để xem chi tiết.</p>
          ) : (
            <MeetingDetailView
              detail={detail}
              users={users}
              isCommander={isCommander}
              onChanged={refreshDetail}
              setError={setError}
            />
          )}
        </div>
      </div>
    </section>
  )
}

function MeetingDetailView({
  detail,
  users,
  isCommander,
  onChanged,
  setError,
}: {
  detail: CommandMeetingDetail
  users: User[]
  isCommander: boolean
  onChanged: () => void
  setError: (m: string | null) => void
}) {
  const { userId } = useAuth()
  const [minutes, setMinutes] = useState(detail.minutes ?? '')
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<MeetingStatus>(detail.status)
  const [busy, setBusy] = useState(false)
  const [inviteId, setInviteId] = useState('')

  useEffect(() => {
    setMinutes(detail.minutes ?? '')
    setStatus(detail.status)
  }, [detail.id, detail.minutes, detail.status])

  // Tu dong luu ban nhap bien ban hop theo tung cuoc hop (tranh mat noi
  // dung khi tai lai trang / mat dien, mat mang LAN dot ngot giua buoi hop).
  // Chi khoi phuc ban nhap khi bien ban tren may chu dang trong (khong ghi
  // de len bien ban da luu thuc su).
  const { clearDraft: clearMinutesDraft } = useDraftAutosave(
    `giaoban-minutes:${detail.id}`,
    minutes,
    setMinutes,
  )

  async function saveMinutes(finish: boolean) {
    setBusy(true)
    setError(null)
    try {
      await commandMeetingsApi.setMinutes(detail.id, minutes.trim(), finish)
      clearMinutesDraft()
      onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không lưu được biên bản')
    } finally {
      setBusy(false)
    }
  }

  const mine = detail.attendees.find((a) => a.user_id === userId)
  const notInvited = users.filter((u) => !detail.attendees.some((a) => a.user_id === u.id))

  async function guard(fn: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
      onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Thao tác không thành công')
    } finally {
      setBusy(false)
    }
  }

  async function download() {
    try {
      const blob = await commandMeetingsApi.download(detail.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = detail.attachment_name ?? `bien-ban-${detail.id}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không tải được tệp')
    }
  }

  return (
    <>
      <div className="thread-view-head">
        <div>
          <h2>{detail.title}</h2>
          <p className="thread-meta">
            <span className={`status-chip st-${detail.status}`}>
              {MEETING_STATUS_LABELS[detail.status]}
            </span>{' '}
            · {fmt(detail.start_time)}
            {detail.end_time ? ` → ${fmt(detail.end_time)}` : ''}
            {detail.location ? ` · ${detail.location}` : ''}
          </p>
        </div>
        {detail.meeting_link ? (
          <a
            className="join-btn"
            href={detail.meeting_link}
            target="_blank"
            rel="noreferrer"
          >
            <Icon name="phone" size={13} /> Vào phòng trực tuyến
          </a>
        ) : null}
      </div>

      {detail.agenda ? (
        <div className="block-section">
          <strong>Chương trình:</strong>
          <p className="msg-body">{detail.agenda}</p>
        </div>
      ) : null}

      {isCommander ? (
        <div className="form-row">
          <label>
            Trạng thái
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as MeetingStatus)}
              disabled={busy}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {MEETING_STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </label>
          <div className="form-actions">
            <button
              type="button"
              disabled={busy || status === detail.status}
              onClick={() =>
                guard(() =>
                  commandMeetingsApi.update(detail.id, {
                    title: detail.title,
                    start_time: detail.start_time,
                    end_time: detail.end_time,
                    location: detail.location,
                    meeting_link: detail.meeting_link,
                    agenda: detail.agenda,
                    status,
                  }),
                )
              }
            >
              Cập nhật trạng thái
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                if (window.confirm('Huỷ hẳn cuộc họp này?'))
                  guard(() => commandMeetingsApi.remove(detail.id)).then(onChanged)
              }}
            >
              Xoá cuộc họp
            </button>
          </div>
        </div>
      ) : null}

      <div className="block-section">
        <strong>Biên bản / kết luận</strong>
        {isCommander ? (
          <>
            <textarea
              rows={4}
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
              placeholder="Ghi kết luận cuộc họp..."
            />
            <div className="form-actions">
              <button type="button" disabled={busy || !minutes.trim()} onClick={() => saveMinutes(false)}>
                Lưu biên bản
              </button>
              <button type="button" disabled={busy || !minutes.trim()} onClick={() => saveMinutes(true)}>
                Lưu &amp; kết thúc họp
              </button>
            </div>
          </>
        ) : (
          <p className="msg-body">{detail.minutes ?? 'Chưa có biên bản.'}</p>
        )}
      </div>

      <div className="block-section">
        <strong>Tài liệu họp</strong>
        <div className="compose-actions">
          {detail.attachment_url ? (
            <button type="button" onClick={download}>
              <Icon name="clipboard" size={12} /> Tải: {detail.attachment_name}
            </button>
          ) : (
            <span className="state-note">Chưa có tài liệu.</span>
          )}
          {isCommander ? (
            <span>
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
              <button
                type="button"
                disabled={busy || !file}
                onClick={() => file && guard(() => commandMeetingsApi.uploadAttachment(detail.id, file))}
              >
                Tải lên
              </button>
            </span>
          ) : null}
        </div>
      </div>

      {mine ? (
        <div className="block-section">
          <strong>Điểm danh của tôi</strong>
          <SelfAttendance meetingId={detail.id} me={mine} onChanged={onChanged} setError={setError} />
        </div>
      ) : null}

      <div className="block-section">
        <strong>
          Thành phần tham dự ({detail.present_count}/{detail.attendee_count} có mặt)
        </strong>
        <table className="users-table">
          <thead>
            <tr>
              <th>Họ tên</th>
              <th>Đơn vị</th>
              <th>Điểm danh</th>
              <th>Lý do vắng</th>
              <th>Ý kiến</th>
              {isCommander ? <th /> : null}
            </tr>
          </thead>
          <tbody>
            {detail.attendees.map((a) => (
              <tr key={a.id}>
                <td>{a.full_name}</td>
                <td>{a.unit_name ?? '—'}</td>
                <td>
                  {isCommander ? (
                    <select
                      value={a.attendance}
                      disabled={busy}
                      onChange={(e) =>
                        guard(() =>
                          commandMeetingsApi.setAttendance(detail.id, a.user_id, {
                            attendance: e.target.value as AttendanceStatus,
                          }),
                        )
                      }
                    >
                      {ATT_OPTIONS.map((o) => (
                        <option key={o} value={o}>
                          {ATTENDANCE_LABELS[o]}
                        </option>
                      ))}
                    </select>
                  ) : (
                    ATTENDANCE_LABELS[a.attendance]
                  )}
                </td>
                <td>{a.absence_reason ?? ''}</td>
                <td>{a.contribution_note ?? ''}</td>
                {isCommander ? (
                  <td className="row-actions">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        guard(() => commandMeetingsApi.removeAttendee(detail.id, a.user_id))
                      }
                    >
                      Gỡ
                    </button>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
        {isCommander && notInvited.length > 0 ? (
          <div className="inline-form">
            <select value={inviteId} onChange={(e) => setInviteId(e.target.value)}>
              <option value="">— Mời thêm —</option>
              {notInvited.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.username})
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={busy || !inviteId}
              onClick={() => {
                guard(() => commandMeetingsApi.invite(detail.id, [Number(inviteId)]))
                setInviteId('')
              }}
            >
              Mời
            </button>
          </div>
        ) : null}
      </div>
    </>
  )
}

function SelfAttendance({
  meetingId,
  me,
  onChanged,
  setError,
}: {
  meetingId: number
  me: Attendee
  onChanged: () => void
  setError: (m: string | null) => void
}) {
  const [attendance, setAttendance] = useState<AttendanceStatus>(me.attendance)
  const [reason, setReason] = useState(me.absence_reason ?? '')
  const [note, setNote] = useState(me.contribution_note ?? '')
  const [busy, setBusy] = useState(false)

  async function save() {
    setBusy(true)
    setError(null)
    try {
      await commandMeetingsApi.setAttendance(meetingId, me.user_id, {
        attendance,
        absence_reason: reason || null,
        contribution_note: note || null,
      })
      onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không lưu được')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="self-attendance">
      <div className="form-row">
        <label>
          Trạng thái
          <select
            value={attendance}
            onChange={(e) => setAttendance(e.target.value as AttendanceStatus)}
          >
            {ATT_OPTIONS.map((o) => (
              <option key={o} value={o}>
                {ATTENDANCE_LABELS[o]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Lý do vắng (nếu có)
          <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
        </label>
      </div>
      <label>
        Ý kiến đóng góp
        <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      <div className="form-actions">
        <button type="button" onClick={save} disabled={busy}>
          Gửi
        </button>
      </div>
    </div>
  )
}
