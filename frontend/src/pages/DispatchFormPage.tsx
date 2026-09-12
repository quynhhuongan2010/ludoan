import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { officialDispatchesApi } from '../api/commandDispatches'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { useRequiredFields } from '../hooks/useRequiredFields'
import {
  DISPATCH_DIRECTION_LABELS,
  DISPATCH_STATUS_LABELS,
  DOC_TYPE_LABELS,
  SECURITY_LEVEL_LABELS,
  URGENCY_LABELS,
  type DispatchDirection,
  type DispatchFormValues,
  type DispatchStatus,
  type DocType,
  type SecurityLevel,
  type Urgency,
} from '../types/commandDispatch'

const emptyDispatch: DispatchFormValues = {
  direction: 'den',
  doc_type: 'cong_van',
  dispatch_number: '',
  summary: '',
  issuing_org: '',
  receiving_org: '',
  signer: '',
  issued_date: '',
  received_date: '',
  deadline: '',
  page_count: '',
  security_level: 'mat',
  urgency: 'thuong',
  archive_ref: '',
  status: 'moi',
  note: '',
}

const LIST_PATH = '/kenh-chi-huy?tab=cong-van'

export function DispatchFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const editingId = id ? Number(id) : null
  const { isCommander } = useAuth()

  const [form, setForm] = useState<DispatchFormValues>(emptyDispatch)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(editingId !== null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const req = useRequiredFields(['dispatch_number', 'summary'] as const)

  useEffect(() => {
    if (editingId === null) return
    setLoading(true)
    officialDispatchesApi
      .get(editingId)
      .then((d) =>
        setForm({
          direction: d.direction,
          doc_type: d.doc_type,
          dispatch_number: d.dispatch_number,
          summary: d.summary,
          issuing_org: d.issuing_org ?? '',
          receiving_org: d.receiving_org ?? '',
          signer: d.signer ?? '',
          issued_date: d.issued_date ?? '',
          received_date: d.received_date ?? '',
          deadline: d.deadline ?? '',
          page_count: d.page_count != null ? String(d.page_count) : '',
          security_level: d.security_level,
          urgency: d.urgency,
          archive_ref: d.archive_ref ?? '',
          status: d.status,
          note: d.note ?? '',
        }),
      )
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không mở được công văn'),
      )
      .finally(() => setLoading(false))
  }, [editingId])

  function goBack() {
    navigate(LIST_PATH)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!req.validate({ dispatch_number: form.dispatch_number, summary: form.summary })) return
    setBusy(true)
    try {
      if (editingId !== null) {
        await officialDispatchesApi.update(editingId, form, file)
      } else {
        await officialDispatchesApi.create(form, file)
      }
      goBack()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không lưu được công văn')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="kenh-chi-huy">
      <div className="page-head">
        <h1>
          {editingId !== null ? `Sửa công văn #${editingId}` : 'Vào sổ công văn mới'}{' '}
          <span className="mat-chip">
            <Icon name="lock" size={11} /> MẬT
          </span>
        </h1>
        <button type="button" className="btn-back" onClick={goBack}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
      </div>

      {!isCommander ? (
        <p role="alert" className="form-error">
          Chỉ Ban Chỉ huy / Cấp uỷ mới được vào sổ công văn.
        </p>
      ) : error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {isCommander && !loading ? (
        <form onSubmit={handleSubmit} className="entity-form">
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
              Loại văn bản
              <select
                value={form.doc_type}
                onChange={(e) => setForm((f) => ({ ...f, doc_type: e.target.value as DocType }))}
              >
                {(Object.keys(DOC_TYPE_LABELS) as DocType[]).map((d) => (
                  <option key={d} value={d}>
                    {DOC_TYPE_LABELS[d]}
                  </option>
                ))}
              </select>
            </label>
            <Field label="Số / ký hiệu" required req={req} name="dispatch_number">
              <input
                type="text"
                maxLength={80}
                value={form.dispatch_number}
                onChange={(e) => setForm((f) => ({ ...f, dispatch_number: e.target.value }))}
                onBlur={(e) => req.mark('dispatch_number', e.target.value)}
                required
              />
            </Field>
          </div>
          <div className="form-row">
            <label>
              Độ mật
              <select
                value={form.security_level}
                onChange={(e) =>
                  setForm((f) => ({ ...f, security_level: e.target.value as SecurityLevel }))
                }
              >
                {(Object.keys(SECURITY_LEVEL_LABELS) as SecurityLevel[]).map((s) => (
                  <option key={s} value={s}>
                    {SECURITY_LEVEL_LABELS[s]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Độ khẩn
              <select
                value={form.urgency}
                onChange={(e) => setForm((f) => ({ ...f, urgency: e.target.value as Urgency }))}
              >
                {(Object.keys(URGENCY_LABELS) as Urgency[]).map((u) => (
                  <option key={u} value={u}>
                    {URGENCY_LABELS[u]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Trạng thái xử lý
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
          <Field label="Trích yếu" required req={req} name="summary">
            <input
              type="text"
              maxLength={500}
              value={form.summary}
              onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
              onBlur={(e) => req.mark('summary', e.target.value)}
              required
            />
          </Field>
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
              Người ký (chức vụ + họ tên)
              <input
                type="text"
                maxLength={200}
                value={form.signer}
                onChange={(e) => setForm((f) => ({ ...f, signer: e.target.value }))}
                placeholder="VD: Đại tá Nguyễn Văn A, Lữ trưởng"
              />
            </label>
            <label>
              Số tờ
              <input
                type="number"
                min={0}
                value={form.page_count}
                onChange={(e) => setForm((f) => ({ ...f, page_count: e.target.value }))}
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
            <label>
              Hạn xử lý / trả lời
              <input
                type="date"
                value={form.deadline}
                onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value }))}
              />
            </label>
          </div>
          <label>
            Số hồ sơ lưu trữ (hộp / cặp)
            <input
              type="text"
              maxLength={120}
              value={form.archive_ref}
              onChange={(e) => setForm((f) => ({ ...f, archive_ref: e.target.value }))}
              placeholder="VD: HS 04/2026 – Hộp 12"
            />
          </label>
          <label>
            Ghi chú / nội dung
            <textarea
              rows={2}
              value={form.note}
              onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
            />
          </label>
          <label>
            Tệp đính kèm {editingId != null ? '(để trống nếu giữ nguyên)' : ''}
            <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </label>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={busy}>
              {busy ? 'Đang lưu...' : editingId != null ? 'Lưu thay đổi' : 'Vào sổ'}
            </button>
            <button type="button" className="btn-cancel" onClick={goBack}>
              Huỷ
            </button>
          </div>
        </form>
      ) : isCommander && loading ? (
        <p>Đang tải...</p>
      ) : null}
    </section>
  )
}
