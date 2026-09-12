import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { dutyShiftHandoversApi } from '../api/dutyShiftHandovers'
import { EmptyState } from './EmptyState'
import { Icon } from './Icon'
import { Modal } from './Modal'
import { useAuth } from '../context/AuthContext'
import {
  HANDOVER_STATUS_COLORS,
  HANDOVER_STATUS_LABELS,
  type DutyShiftHandover,
  type DutyShiftHandoverCreate,
  type DutyShiftHandoverStatus,
} from '../types/dutyShiftHandover'
import type { DutySchedule } from '../types/dutySchedule'
import type { Unit } from '../types/unit'

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(`${iso}T00:00:00`).toLocaleDateString('vi-VN')
  } catch {
    return iso
  }
}

// ---------------------------------------------------------------------------
// 1. Modal Lập biên bản bàn giao ca trực mới
// ---------------------------------------------------------------------------
interface CreateModalProps {
  schedule: DutySchedule
  onClose: () => void
  onSuccess: () => void
}

export function DutyShiftHandoverCreateModal({
  schedule,
  onClose,
  onSuccess,
}: CreateModalProps) {
  const { username } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [giverName, setGiverName] = useState(schedule.duty_officer || username || '')
  const [receiverName, setReceiverName] = useState('')
  const [personnelReport, setPersonnelReport] = useState(
    `Quân số ca trực ${schedule.personnel_present ?? '...'}/${
      schedule.personnel_total ?? '...'
    } đồng chí có mặt đầy đủ, chấp hành nghiêm điều lệnh.`
  )
  const [equipmentStatus, setEquipmentStatus] = useState(
    'Khí tài vô tuyến điện, tổng đài chỉ huy, tuyến cáp thông suốt, niêm phong trang bị kỹ thuật nguyên vẹn.'
  )
  const [incidentLog, setIncidentLog] = useState('Trong ca tình hình thông tin liên lạc ổn định, không có sự cố bất thường.')
  const [pendingTasks, setPendingTasks] = useState(
    'Tiếp tục duy trì nghiêm chế độ canh trực SSCĐ 24/24, theo dõi chặt chẽ mạng liên lạc chỉ huy.'
  )

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!personnelReport.trim() || !equipmentStatus.trim()) {
      setError('Vui lòng nhập đầy đủ báo cáo quân số và tình trạng vũ khí trang bị.')
      return
    }

    setBusy(true)
    setError(null)
    try {
      const payload: DutyShiftHandoverCreate = {
        schedule_id: schedule.id,
        giver_name: giverName.trim() || undefined,
        receiver_name: receiverName.trim() || undefined,
        personnel_report: personnelReport.trim(),
        equipment_status: equipmentStatus.trim(),
        incident_log: incidentLog.trim() || undefined,
        pending_tasks: pendingTasks.trim() || undefined,
      }
      await dutyShiftHandoversApi.create(payload)
      onSuccess()
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'Không thể lập biên bản bàn giao ca trực.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Lập biên bản bàn giao ca trực điện tử" onClose={onClose}>
      <form onSubmit={handleSubmit} className="entity-form space-y-4">
        <div className="p-3 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 rounded text-sm">
          <p className="font-semibold text-amber-900 dark:text-amber-200">
            Ca trực: {schedule.shift} ({formatDate(schedule.duty_date)})
          </p>
          <p className="text-amber-800 dark:text-amber-300">
            Đơn vị: {schedule.unit_name || 'Lữ đoàn'} · Cương vị: {schedule.role_title} ({schedule.duty_officer})
          </p>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded text-sm flex items-center gap-2">
            <Icon name="alert-triangle" size={16} />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
              Đồng chí bàn giao (Ca trước) *
            </span>
            <input
              type="text"
              required
              className="w-full mt-1 px-3 py-1.5 border rounded dark:bg-slate-800"
              value={giverName}
              onChange={(e) => setGiverName(e.target.value)}
            />
          </label>

          <label className="block">
            <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
              Đồng chí nhận bàn giao (Ca tiếp theo)
            </span>
            <input
              type="text"
              className="w-full mt-1 px-3 py-1.5 border rounded dark:bg-slate-800"
              placeholder="Họ tên ca trưởng tiếp nhận (nếu có)"
              value={receiverName}
              onChange={(e) => setReceiverName(e.target.value)}
            />
          </label>
        </div>

        <label className="block">
          <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
            1. Báo cáo quân số &amp; Chấp hành kỷ luật *
          </span>
          <textarea
            rows={2}
            required
            className="w-full mt-1 px-3 py-1.5 border rounded dark:bg-slate-800"
            value={personnelReport}
            onChange={(e) => setPersonnelReport(e.target.value)}
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
            2. Tình trạng vũ khí trang bị &amp; Khí tài TTLL *
          </span>
          <textarea
            rows={3}
            required
            className="w-full mt-1 px-3 py-1.5 border rounded dark:bg-slate-800"
            value={equipmentStatus}
            onChange={(e) => setEquipmentStatus(e.target.value)}
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
            3. Nhật ký các sự vụ phát sinh trong ca
          </span>
          <textarea
            rows={2}
            className="w-full mt-1 px-3 py-1.5 border rounded dark:bg-slate-800"
            value={incidentLog}
            onChange={(e) => setIncidentLog(e.target.value)}
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
            4. Nhiệm vụ tồn đọng bàn giao ca sau xử lý
          </span>
          <textarea
            rows={2}
            className="w-full mt-1 px-3 py-1.5 border rounded dark:bg-slate-800"
            value={pendingTasks}
            onChange={(e) => setPendingTasks(e.target.value)}
          />
        </label>

        <div className="flex justify-end gap-2 pt-2 border-t">
          <button
            type="button"
            className="px-4 py-2 text-sm rounded border hover:bg-slate-100 dark:hover:bg-slate-800"
            onClick={onClose}
          >
            Huỷ bỏ
          </button>
          <button
            type="submit"
            disabled={busy}
            className="px-4 py-2 text-sm rounded bg-amber-700 hover:bg-amber-800 text-white font-medium flex items-center gap-1.5"
          >
            <Icon name="check" size={16} />
            <span>{busy ? 'Đang lưu...' : 'Ký lập biên bản'}</span>
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ---------------------------------------------------------------------------
// 2. Modal Xem chi tiết, Ký nhận ca & Phê duyệt của Chỉ huy
// ---------------------------------------------------------------------------
interface DetailModalProps {
  handover: DutyShiftHandover
  onClose: () => void
  onUpdated: () => void
}

export function DutyShiftHandoverDetailModal({
  handover,
  onClose,
  onUpdated,
}: DetailModalProps) {
  const { username, userId, isCommander } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Nhận ca
  const [receiverNote, setReceiverNote] = useState(handover.receiver_note || '')
  const [ackStatus, setAckStatus] = useState<'da_nhan' | 'co_kien_nghi'>('da_nhan')

  // openapi v8.0.0 (F7): chỉ hiện nút "Ký nhận" khi biên bản còn chờ, người
  // ký không phải người lập, và là người-nhận-được-chỉ-định (hoặc chưa chỉ định).
  const canAcknowledge =
    handover.status === 'cho_nhan' &&
    handover.giver_id !== userId &&
    (handover.receiver_id == null || handover.receiver_id === userId)

  // Chỉ huy ghi ý kiến
  const [commanderNoteInput, setCommanderNoteInput] = useState('')

  const handleAcknowledge = async () => {
    setBusy(true)
    setError(null)
    try {
      await dutyShiftHandoversApi.acknowledge(handover.id, {
        receiver_note: receiverNote.trim() || undefined,
        status: ackStatus,
      })
      onUpdated()
      onClose()
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'Không thể ký nhận ca trực.')
    } finally {
      setBusy(false)
    }
  }

  const handleCommanderReview = async () => {
    if (!commanderNoteInput.trim()) {
      setError('Vui lòng nhập ý kiến chỉ đạo của Chỉ huy.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await dutyShiftHandoversApi.review(handover.id, {
        commander_note: commanderNoteInput.trim(),
      })
      setCommanderNoteInput('')
      onUpdated()
      onClose()
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'Không thể ghi ý kiến chỉ đạo.')
    } finally {
      setBusy(false)
    }
  }

  const statusColor = HANDOVER_STATUS_COLORS[handover.status]
  const statusLabel = HANDOVER_STATUS_LABELS[handover.status]

  return (
    <Modal title="Biên bản bàn giao ca trực &amp; Sổ nhật ký kíp trực" onClose={onClose}>
      <div className="space-y-4 max-h-[80vh] overflow-y-auto pr-1">
        {/* Tiêu đề & Thông tin cơ bản */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-slate-50 dark:bg-slate-900 border rounded">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-slate-900 dark:text-slate-100">
                {handover.shift || 'Ca trực'}
              </span>
              <span className="text-sm text-slate-500">
                ({formatDate(handover.duty_date)})
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Đơn vị: {handover.unit_name || 'Toàn Lữ đoàn'} · Cương vị: {handover.duty_type || '—'}
            </p>
          </div>
          <span
            className={`px-2.5 py-1 text-xs font-semibold rounded border ${statusColor.bg} ${statusColor.text} ${statusColor.border}`}
          >
            {statusLabel}
          </span>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded text-sm flex items-center gap-2">
            <Icon name="alert-triangle" size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Khối Thông tin Giao - Nhận */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 rounded">
          <div>
            <span className="text-xs font-bold uppercase text-amber-900 dark:text-amber-200">
              Bên giao (Ca trước)
            </span>
            <p className="font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {handover.giver_name}
            </p>
            <p className="text-xs text-slate-500">
              Lập lúc: {formatDateTime(handover.handover_time)}
            </p>
          </div>

          <div>
            <span className="text-xs font-bold uppercase text-amber-900 dark:text-amber-200">
              Bên nhận (Ca tiếp theo)
            </span>
            <p className="font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {handover.receiver_name || '(Chưa có người ký nhận)'}
            </p>
            <p className="text-xs text-slate-500">
              Ký nhận lúc: {formatDateTime(handover.acknowledged_at)}
            </p>
          </div>
        </div>

        {/* Chi tiết 4 mục bàn giao */}
        <div className="space-y-3 text-sm">
          <div className="p-2.5 bg-slate-50 dark:bg-slate-900/50 rounded border">
            <h4 className="font-semibold text-xs text-slate-700 dark:text-slate-300 uppercase">
              1. Quân số &amp; Tình hình kỷ luật
            </h4>
            <p className="mt-1 text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
              {handover.personnel_report}
            </p>
          </div>

          <div className="p-2.5 bg-slate-50 dark:bg-slate-900/50 rounded border">
            <h4 className="font-semibold text-xs text-slate-700 dark:text-slate-300 uppercase">
              2. Tình trạng vũ khí trang bị &amp; Khí tài TTLL
            </h4>
            <p className="mt-1 text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
              {handover.equipment_status}
            </p>
          </div>

          <div className="p-2.5 bg-slate-50 dark:bg-slate-900/50 rounded border">
            <h4 className="font-semibold text-xs text-slate-700 dark:text-slate-300 uppercase">
              3. Nhật ký sự vụ trong ca
            </h4>
            <p className="mt-1 text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
              {handover.incident_log || '— Không có sự vụ phát sinh.'}
            </p>
          </div>

          <div className="p-2.5 bg-slate-50 dark:bg-slate-900/50 rounded border">
            <h4 className="font-semibold text-xs text-slate-700 dark:text-slate-300 uppercase">
              4. Nhiệm vụ tồn đọng bàn giao
            </h4>
            <p className="mt-1 text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
              {handover.pending_tasks || '— Không có nhiệm vụ tồn đọng.'}
            </p>
          </div>
        </div>

        {/* Ghi chú khi nhận ca nếu đã ký */}
        {handover.receiver_note && (
          <div className="p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded text-sm">
            <span className="text-xs font-bold text-blue-900 dark:text-blue-300 uppercase">
              Ghi chú của ca nhận bàn giao:
            </span>
            <p className="text-blue-950 dark:text-blue-100 mt-1 whitespace-pre-wrap">
              {handover.receiver_note}
            </p>
          </div>
        )}

        {/* Ý kiến chỉ đạo của Chỉ huy */}
        <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded text-sm">
          <div className="flex items-center gap-1.5 text-xs font-bold text-red-900 dark:text-red-300 uppercase">
            <Icon name="shield" size={14} />
            <span>Ý kiến kiểm tra, chỉ đạo của Chỉ huy đơn vị:</span>
          </div>
          {handover.commander_note ? (
            <p className="text-red-950 dark:text-red-100 mt-1.5 whitespace-pre-wrap font-medium">
              {handover.commander_note}
            </p>
          ) : (
            <p className="text-red-700 dark:text-red-400 mt-1 italic">
              (Chưa có ý kiến chỉ đạo của Chỉ huy)
            </p>
          )}
        </div>

        {/* Khối Thao tác: Ký nhận ca (dành cho người nhận nếu chưa nhận hoặc muốn cập nhật) */}
        {canAcknowledge && (
          <div className="p-3 border-2 border-dashed border-amber-300 dark:border-amber-700 rounded-lg space-y-2 bg-amber-50/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-amber-900 dark:text-amber-200">
                Xác nhận nhận bàn giao ca trực ({username || 'Ca nhận'})
              </span>
              <div className="flex items-center gap-3 text-xs">
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="ackStatus"
                    value="da_nhan"
                    checked={ackStatus === 'da_nhan'}
                    onChange={() => setAckStatus('da_nhan')}
                  />
                  <span>Nhận đủ (Đã nhận)</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer text-rose-700">
                  <input
                    type="radio"
                    name="ackStatus"
                    value="co_kien_nghi"
                    checked={ackStatus === 'co_kien_nghi'}
                    onChange={() => setAckStatus('co_kien_nghi')}
                  />
                  <span>Có kiến nghị</span>
                </label>
              </div>
            </div>

            <textarea
              rows={2}
              className="w-full px-3 py-1.5 border rounded text-sm dark:bg-slate-800"
              placeholder="Ghi chú xác nhận hiện trạng vũ khí, khí tài, trang bị khi nhận ca..."
              value={receiverNote}
              onChange={(e) => setReceiverNote(e.target.value)}
            />

            <div className="flex justify-end">
              <button
                type="button"
                disabled={busy}
                onClick={handleAcknowledge}
                className="px-4 py-1.5 text-sm rounded bg-emerald-700 hover:bg-emerald-800 text-white font-medium flex items-center gap-1.5"
              >
                <Icon name="check" size={15} />
                <span>{busy ? 'Đang xử lý...' : 'Ký xác nhận nhận ca'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Khối Thao tác: Bút phê Chỉ huy */}
        {isCommander && (
          <div className="p-3 border border-red-200 dark:border-red-900/60 rounded-lg space-y-2 bg-red-50/20">
            <span className="text-xs font-bold uppercase text-red-900 dark:text-red-300 flex items-center gap-1">
              <Icon name="edit" size={13} />
              <span>Chỉ huy ghi bút phê / Ý kiến chỉ đạo</span>
            </span>
            <textarea
              rows={2}
              className="w-full px-3 py-1.5 border rounded text-sm dark:bg-slate-800"
              placeholder="Nhập nội dung nhận xét kíp trực hoặc mệnh lệnh chỉ đạo..."
              value={commanderNoteInput}
              onChange={(e) => setCommanderNoteInput(e.target.value)}
            />
            <div className="flex justify-end">
              <button
                type="button"
                disabled={busy || !commanderNoteInput.trim()}
                onClick={handleCommanderReview}
                className="px-3 py-1.5 text-xs rounded bg-red-700 hover:bg-red-800 text-white font-medium flex items-center gap-1"
              >
                <Icon name="send" size={13} />
                <span>Ghi ý kiến chỉ đạo</span>
              </button>
            </div>
          </div>
        )}

        {/* Nút in và đóng */}
        <div className="flex justify-between items-center pt-3 border-t">
          <button
            type="button"
            className="px-3 py-1.5 text-sm rounded border hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-1.5"
            onClick={() => window.print()}
          >
            <Icon name="file" size={15} />
            <span>In biên bản</span>
          </button>
          <button
            type="button"
            className="px-4 py-1.5 text-sm rounded bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 font-medium"
            onClick={onClose}
          >
            Đóng
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ---------------------------------------------------------------------------
// 3. Tab Sổ Bàn Giao Ca Trực & Nhật Ký Kíp Trực
// ---------------------------------------------------------------------------
interface HandoverTabProps {
  units: Unit[]
  onOpenCreateForSchedule?: (schedule: DutySchedule) => void
}

export function DutyShiftHandoverTab({ units }: HandoverTabProps) {
  const [handovers, setHandovers] = useState<DutyShiftHandover[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Bộ lọc
  const [filterDateFrom, setFilterDateFrom] = useState('')
  const [filterDateTo, setFilterDateTo] = useState('')
  const [filterUnitId, setFilterUnitId] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  // Modal chi tiết
  const [selectedHandover, setSelectedHandover] = useState<DutyShiftHandover | null>(null)

  const loadData = useCallback(() => {
    setLoading(true)
    setError(null)
    dutyShiftHandoversApi
      .list({
        date_from: filterDateFrom || undefined,
        date_to: filterDateTo || undefined,
        unit_id: filterUnitId ? Number(filterUnitId) : undefined,
        status: filterStatus || undefined,
        limit: 100,
      })
      .then((res) => {
        setHandovers(res.items)
        setTotal(res.total)
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : 'Không thể tải Sổ bàn giao ca trực.')
      })
      .finally(() => setLoading(false))
  }, [filterDateFrom, filterDateTo, filterUnitId, filterStatus])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Thống kê nhanh
  const countPending = handovers.filter((h) => h.status === 'cho_nhan').length
  const countDone = handovers.filter((h) => h.status === 'da_nhan').length
  const countFeedback = handovers.filter((h) => h.status === 'co_kien_nghi').length

  return (
    <div className="duty-print space-y-4">
      {/* Bộ lọc thanh công cụ */}
      <div className="duty-toolbar no-print flex flex-wrap items-center justify-between gap-3 p-3 bg-white dark:bg-slate-900 border rounded-lg shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs font-medium">
            <span>Từ ngày:</span>
            <input
              type="date"
              className="px-2 py-1 border rounded text-xs dark:bg-slate-800"
              value={filterDateFrom}
              onChange={(e) => setFilterDateFrom(e.target.value)}
            />
          </label>

          <label className="flex items-center gap-1.5 text-xs font-medium">
            <span>Đến ngày:</span>
            <input
              type="date"
              className="px-2 py-1 border rounded text-xs dark:bg-slate-800"
              value={filterDateTo}
              onChange={(e) => setFilterDateTo(e.target.value)}
            />
          </label>

          <label className="flex items-center gap-1.5 text-xs font-medium">
            <span>Đơn vị:</span>
            <select
              className="px-2 py-1 border rounded text-xs dark:bg-slate-800"
              value={filterUnitId}
              onChange={(e) => setFilterUnitId(e.target.value)}
            >
              <option value="">Tất cả đơn vị</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-1.5 text-xs font-medium">
            <span>Trạng thái:</span>
            <select
              className="px-2 py-1 border rounded text-xs dark:bg-slate-800"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="">Tất cả trạng thái</option>
              <option value="cho_nhan">Chờ nhận ca</option>
              <option value="da_nhan">Đã nhận ca</option>
              <option value="co_kien_nghi">Có kiến nghị</option>
            </select>
          </label>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="px-3 py-1 text-xs rounded border hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-1"
            onClick={() => loadData()}
          >
            <Icon name="undo" size={13} />
            <span>Làm mới</span>
          </button>
          <button
            type="button"
            className="px-3 py-1 text-xs rounded bg-slate-800 hover:bg-slate-900 text-white flex items-center gap-1"
            onClick={() => window.print()}
          >
            <Icon name="file" size={13} />
            <span>In sổ nhật ký</span>
          </button>
        </div>
      </div>

      {/* Thống kê nhanh */}
      <div className="cdb-stats no-print grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="cdb-stat">
          <span className="cdb-stat-value">{total}</span>
          <span className="cdb-stat-label">Tổng biên bản bàn giao</span>
        </div>
        <div className="cdb-stat">
          <span className="cdb-stat-value text-amber-600">{countPending}</span>
          <span className="cdb-stat-label">Chờ bàn giao / Ký nhận</span>
        </div>
        <div className="cdb-stat cdb-stat-done">
          <span className="cdb-stat-value text-emerald-600">{countDone}</span>
          <span className="cdb-stat-label">Đã bàn giao xong</span>
        </div>
        <div className="cdb-stat">
          <span className="cdb-stat-value text-rose-600">{countFeedback}</span>
          <span className="cdb-stat-label">Có kiến nghị phát sinh</span>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded text-sm flex items-center gap-2">
          <Icon name="alert-triangle" size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Bảng danh sách Sổ bàn giao ca trực */}
      {loading ? (
        <div className="cdb-skeleton-list">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="cdb-skeleton-row" />
          ))}
        </div>
      ) : handovers.length === 0 ? (
        <EmptyState
          icon="clipboard"
          message="Chưa có biên bản bàn giao ca trực nào khớp với bộ lọc."
        />
      ) : (
        <div className="table-scroll border rounded-lg overflow-hidden bg-white dark:bg-slate-900">
          <table className="data-table duty-table w-full text-sm">
            <thead>
              <tr className="bg-slate-100 dark:bg-slate-800 text-left">
                <th>Ngày / Ca</th>
                <th>Đơn vị</th>
                <th>Người bàn giao</th>
                <th>Người nhận ca</th>
                <th>Hiện trạng VKTB &amp; Khí tài</th>
                <th>Trạng thái</th>
                <th>Chỉ huy duyệt</th>
                <th className="no-print">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {handovers.map((h) => {
                const statusColor = HANDOVER_STATUS_COLORS[h.status as DutyShiftHandoverStatus]
                const statusLabel = HANDOVER_STATUS_LABELS[h.status as DutyShiftHandoverStatus]
                return (
                  <tr key={h.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td>
                      <div className="font-semibold text-slate-900 dark:text-slate-100">
                        {h.shift || 'Ca trực'}
                      </div>
                      <div className="text-xs text-slate-500">{formatDate(h.duty_date)}</div>
                    </td>
                    <td>{h.unit_name || 'Lữ đoàn'}</td>
                    <td>
                      <div className="font-medium text-slate-800 dark:text-slate-200">
                        {h.giver_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {formatDateTime(h.handover_time)}
                      </div>
                    </td>
                    <td>
                      {h.receiver_name ? (
                        <>
                          <div className="font-medium text-slate-800 dark:text-slate-200">
                            {h.receiver_name}
                          </div>
                          <div className="text-xs text-emerald-600">
                            {formatDateTime(h.acknowledged_at)}
                          </div>
                        </>
                      ) : (
                        <span className="text-xs text-amber-600 italic">Chờ ký nhận...</span>
                      )}
                    </td>
                    <td className="max-w-xs truncate" title={h.equipment_status}>
                      {h.equipment_status}
                    </td>
                    <td>
                      <span
                        className={`inline-block px-2 py-0.5 text-xs font-semibold rounded border ${statusColor.bg} ${statusColor.text} ${statusColor.border}`}
                      >
                        {statusLabel}
                      </span>
                    </td>
                    <td>
                      {h.commander_note ? (
                        <span className="text-xs text-emerald-700 dark:text-emerald-300 font-medium flex items-center gap-1">
                          <Icon name="check" size={13} />
                          <span>Đã chỉ đạo</span>
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Chưa ghi</span>
                      )}
                    </td>
                    <td className="no-print">
                      <button
                        type="button"
                        className="px-2.5 py-1 text-xs rounded bg-amber-100 text-amber-800 hover:bg-amber-200 dark:bg-amber-950/60 dark:text-amber-300 font-medium flex items-center gap-1"
                        onClick={() => setSelectedHandover(h)}
                      >
                        <Icon name="eye" size={13} />
                        <span>Xem / Ký sổ</span>
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal chi tiết khi nhấn Xem/Ký sổ */}
      {selectedHandover && (
        <DutyShiftHandoverDetailModal
          handover={selectedHandover}
          onClose={() => setSelectedHandover(null)}
          onUpdated={() => {
            loadData()
            setSelectedHandover(null)
          }}
        />
      )}
    </div>
  )
}
