import {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { dutySchedulesApi, dutyWeekPlansApi } from '../api/dutySchedules'
import { dutyShiftHandoversApi } from '../api/dutyShiftHandovers'
import { unitsApi } from '../api/units'
import {
  DutyShiftHandoverCreateModal,
  DutyShiftHandoverDetailModal,
  DutyShiftHandoverTab,
} from '../components/DutyShiftHandoverSection'
import { EmptyState } from '../components/EmptyState'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { Modal } from '../components/Modal'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { useRequiredFields } from '../hooks/useRequiredFields'
import {
  DUTY_TYPE_LABELS,
  type DutyDayBoard,
  type DutyPlanAttachment,
  type DutyPlanStatus,
  type DutySchedule,
  type DutyScheduleCreate,
  type DutyType,
  type DutyWeekBoard,
  type DutyWeekPlan,
  type DutyWeekPlanDetail,
} from '../types/dutySchedule'
import type { DutyShiftHandover } from '../types/dutyShiftHandover'
import type { Unit } from '../types/unit'

type TabKey = 'week' | 'day' | 'manage' | 'handover'
type ScopeMode = 'toan_lu_doan' | 'khoi_co_quan'

const DUTY_TYPES = Object.keys(DUTY_TYPE_LABELS) as DutyType[]
const DUTY_TYPE_ORDER: DutyType[] = [
  'truc_chi_huy',
  'truc_ban_tac_chien',
  'truc_ban_noi_vu',
  'truc_chuyen_mon',
  'truc_ca_kip',
  'truc_bao_ve',
  'khac',
]
const DUTY_TYPE_TONE: Record<string, string> = {
  truc_chi_huy: 'red',
  truc_ban_tac_chien: 'green',
  truc_ban_noi_vu: 'blue',
  truc_chuyen_mon: 'green',
  truc_ca_kip: 'green',
  truc_bao_ve: 'gold',
  khac: 'gray',
}
const WEEKDAYS = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']

const PLAN_STATUSES: DutyPlanStatus[] = ['nhap', 'cho_duyet', 'da_duyet', 'tra_lai']
const PLAN_STATUS_LABELS: Record<DutyPlanStatus, string> = {
  nhap: 'Nháp',
  cho_duyet: 'Chờ duyệt',
  da_duyet: 'Đã duyệt',
  tra_lai: 'Trả lại',
}

const CO_QUAN_KINDS = new Set(['phong_ban', 'bch_lu_doan', 'cap_uy'])

function isoOf(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}
function todayIso(): string {
  return isoOf(new Date())
}
function mondayOf(iso: string): string {
  const d = new Date(`${iso}T00:00:00`)
  const wd = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - wd)
  return isoOf(d)
}
function addDays(iso: string, n: number): string {
  const d = new Date(`${iso}T00:00:00`)
  d.setDate(d.getDate() + n)
  return isoOf(d)
}
function ddmm(iso: string): string {
  const d = new Date(`${iso}T00:00:00`)
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
}
function formatDate(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('vi-VN')
}
function formatDateTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('vi-VN') : '—'
}
function errMsg(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
}
function muster(present: number | null, total: number | null): string {
  if (!present && !total) return '—'
  return `${present ?? 0}/${total ?? 0}`
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
/** Tệp đính kèm lịch trực lưu ở /static -> URL tuyệt đối để tải về. */
function staticUrl(url: string): string {
  return url.startsWith('/static') ? `${API_BASE}${url}` : url
}
function formatFileSize(bytes: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
/** Định dạng tệp lịch trực được phép đính kèm (khớp DUTY_ATTACH_EXTENSIONS ở backend). */
const DUTY_ATTACH_ACCEPT =
  '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.webp,.gif'

function StatusChip({ status, label }: { status: string; label: string }) {
  return <span className={`status-chip st-${status}`}>{label}</span>
}

const emptyEntry: DutyScheduleCreate = {
  duty_date: '',
  duty_type: 'truc_chi_huy',
  shift: '',
  duty_officer: '',
  role_title: '',
  contact_phone: '',
  personnel_present: null,
  personnel_total: null,
  note: '',
}

// ----------------------------------------------------------------- Scope (phạm vi)
interface Scope {
  mode: ScopeMode
  setMode: (m: ScopeMode) => void
  unitPick: string // '' = theo tab | 'khoi_co_quan' | '<unitId>'
  setUnitPick: (v: string) => void
  units: Unit[]
  coQuanIds: Set<number>
  inScope: (unitId: number | null) => boolean
  unitRank: Map<number, number>
  label: string
}

function useScope(): Scope {
  const [mode, setMode] = useState<ScopeMode>('toan_lu_doan')
  const [unitPick, setUnitPick] = useState('')
  const [units, setUnits] = useState<Unit[]>([])

  useEffect(() => {
    unitsApi
      .list({ active: true })
      .then(setUnits)
      .catch(() => setUnits([]))
  }, [])

  const coQuanIds = useMemo(
    () => new Set(units.filter((u) => CO_QUAN_KINDS.has(u.unit_kind)).map((u) => u.id)),
    [units],
  )

  const unitRank = useMemo(() => {
    const rankKind = (k: string) =>
      k === 'bch_lu_doan' ? 0 : k === 'cap_uy' ? 1 : k === 'phong_ban' ? 2 : 5
    const sorted = [...units].sort(
      (a, b) =>
        rankKind(a.unit_kind) - rankKind(b.unit_kind) ||
        a.name.localeCompare(b.name, 'vi', { numeric: true }),
    )
    return new Map(sorted.map((u, i) => [u.id, i]))
  }, [units])

  const inScope = useCallback(
    (unitId: number | null): boolean => {
      if (unitPick && unitPick !== 'khoi_co_quan') return unitId === Number(unitPick)
      const useCoQuan = unitPick === 'khoi_co_quan' || mode === 'khoi_co_quan'
      if (!useCoQuan) return true
      return unitId != null && coQuanIds.has(unitId)
    },
    [unitPick, mode, coQuanIds],
  )

  const label =
    unitPick && unitPick !== 'khoi_co_quan'
      ? (units.find((u) => u.id === Number(unitPick))?.name ?? 'Đơn vị')
      : unitPick === 'khoi_co_quan' || mode === 'khoi_co_quan'
        ? 'Khối Cơ quan Lữ đoàn'
        : 'Toàn Lữ đoàn Thông tin 21'

  return { mode, setMode, unitPick, setUnitPick, units, coQuanIds, inScope, unitRank, label }
}

function ScopeSelector({ scope }: { scope: Scope }) {
  const donViUnits = scope.units.filter((u) => !CO_QUAN_KINDS.has(u.unit_kind))
  return (
    <div className="duty-scope no-print">
      <div className="duty-scope-modes" role="tablist" aria-label="Phạm vi biểu trực">
        <button
          type="button"
          role="tab"
          aria-selected={scope.mode === 'toan_lu_doan'}
          className={scope.mode === 'toan_lu_doan' ? 'duty-scope-tab active' : 'duty-scope-tab'}
          onClick={() => {
            scope.setMode('toan_lu_doan')
            scope.setUnitPick('')
          }}
        >
          <Icon name="layers" size={15} /> Toàn Lữ đoàn
          <em>Cơ quan + d1, d2, TT2</em>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={scope.mode === 'khoi_co_quan'}
          className={scope.mode === 'khoi_co_quan' ? 'duty-scope-tab active' : 'duty-scope-tab'}
          onClick={() => {
            scope.setMode('khoi_co_quan')
            scope.setUnitPick('')
          }}
        >
          <Icon name="shield" size={15} /> Khối Cơ quan Lữ đoàn
          <em>Tham mưu · Chính trị · Hậu cần – KT</em>
        </button>
      </div>
      <label className="duty-scope-pick">
        Lọc chi tiết
        <select value={scope.unitPick} onChange={(e) => scope.setUnitPick(e.target.value)}>
          <option value="">Tất cả (theo phạm vi)</option>
          <option value="khoi_co_quan">Khối Cơ quan</option>
          {donViUnits.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}

// ---------------------------------------------------------- Ma trận biểu trực
interface MatrixDay {
  date: string
  weekday_label: string
  is_today: boolean
  entries: DutySchedule[]
  muster?: string
}

interface MRow {
  key: string
  unit_id: number
  unit_name: string
  duty_type: string
  role_title: string
  cells: DutySchedule[][]
}

function DutyMatrix({
  days,
  groupByUnit,
  unitRank,
}: {
  days: MatrixDay[]
  groupByUnit: boolean
  unitRank?: Map<number, number>
}) {
  const n = days.length

  const tree = useMemo(() => {
    const idx = new Map(days.map((d, i) => [d.date, i]))
    const rowMap = new Map<string, MRow>()
    const seenUnitOrder = new Map<number, number>()
    let ord = 0
    for (const d of days) {
      for (const e of d.entries) {
        const uid = e.unit_id ?? -1
        if (!seenUnitOrder.has(uid)) seenUnitOrder.set(uid, ord++)
        const key = `${uid}||${e.duty_type}||${e.role_title}`
        let r = rowMap.get(key)
        if (!r) {
          r = {
            key,
            unit_id: uid,
            unit_name: e.unit_name ?? '—',
            duty_type: e.duty_type,
            role_title: e.role_title,
            cells: Array.from({ length: n }, () => [] as DutySchedule[]),
          }
          rowMap.set(key, r)
        }
        const di = idx.get(e.duty_date)
        if (di != null) r.cells[di].push(e)
      }
    }
    const rows = [...rowMap.values()]
    const dtRank = (t: string) => {
      const i = DUTY_TYPE_ORDER.indexOf(t as DutyType)
      return i < 0 ? DUTY_TYPE_ORDER.length : i
    }
    const uRank = (uid: number) =>
      unitRank?.get(uid) ?? 1000 + (seenUnitOrder.get(uid) ?? 0)

    if (!groupByUnit) {
      const groups: { key: string; label: string; tone: string; rows: MRow[] }[] = []
      for (const dt of [...DUTY_TYPE_ORDER, '__other__']) {
        const rs = rows
          .filter((r) =>
            dt === '__other__'
              ? !DUTY_TYPE_ORDER.includes(r.duty_type as DutyType)
              : r.duty_type === dt,
          )
          .sort((a, b) => a.role_title.localeCompare(b.role_title, 'vi'))
        if (rs.length)
          groups.push({
            key: dt,
            label: dt === '__other__' ? 'Khác' : (DUTY_TYPE_LABELS[dt as DutyType] ?? dt),
            tone: DUTY_TYPE_TONE[dt] ?? 'gray',
            rows: rs,
          })
      }
      return { kind: 'flat' as const, groups }
    }

    const unitIds = [...new Set(rows.map((r) => r.unit_id))].sort((a, b) => uRank(a) - uRank(b))
    const units = unitIds.map((uid) => {
      const uRows = rows.filter((r) => r.unit_id === uid)
      const subGroups: { key: string; label: string; tone: string; rows: MRow[] }[] = []
      for (const dt of [...DUTY_TYPE_ORDER, '__other__']) {
        const rs = uRows
          .filter((r) =>
            dt === '__other__'
              ? !DUTY_TYPE_ORDER.includes(r.duty_type as DutyType)
              : r.duty_type === dt,
          )
          .sort((a, b) => dtRank(a.duty_type) - dtRank(b.duty_type))
        if (rs.length)
          subGroups.push({
            key: dt,
            label: dt === '__other__' ? 'Khác' : (DUTY_TYPE_LABELS[dt as DutyType] ?? dt),
            tone: DUTY_TYPE_TONE[dt] ?? 'gray',
            rows: rs,
          })
      }
      return { uid, name: uRows[0]?.unit_name ?? '—', subGroups }
    })
    return { kind: 'byUnit' as const, units }
  }, [days, n, groupByUnit, unitRank])

  const hasMuster = days.some((d) => d.muster && d.muster !== '—')
  const totalRows =
    tree.kind === 'flat'
      ? tree.groups.reduce((s, g) => s + g.rows.length, 0)
      : tree.units.reduce((s, u) => s + u.subGroups.reduce((x, g) => x + g.rows.length, 0), 0)
  if (totalRows === 0) {
    return (
      <EmptyState
        icon="clock"
        message={
          <>
            Chưa có ca trực nào <strong>đã duyệt</strong> trong phạm vi / tuần này.
            <br />
            Trực ban đơn vị vào thẻ <em>“Lập &amp; duyệt bảng trực”</em> để tạo bảng trực tuần và
            gửi chỉ huy phê duyệt; bảng được duyệt sẽ hiện ở đây.
          </>
        }
      />
    )
  }

  const renderRow = (r: MRow) => (
    <tr key={r.key}>
      <th className="dm-role">
        <span className="dm-role-title">{r.role_title || '—'}</span>
      </th>
      {r.cells.map((cell, ci) => (
        <td key={ci} className={days[ci].is_today ? 'is-today' : undefined}>
          {cell.length === 0 ? (
            <span className="dm-empty">–</span>
          ) : (
            cell.map((e) => (
              <div
                key={e.id}
                className={`dm-card tone-${DUTY_TYPE_TONE[e.duty_type] ?? 'gray'}`}
              >
                <strong>{e.duty_officer}</strong>
                {e.shift ? <span className="dm-shift">{e.shift}</span> : null}
                {e.contact_phone ? (
                  <span className="dm-phone">
                    <Icon name="phone" size={10} /> {e.contact_phone}
                  </span>
                ) : null}
                {e.personnel_present || e.personnel_total ? (
                  <span className="dm-qs">
                    Quân số {muster(e.personnel_present, e.personnel_total)}
                  </span>
                ) : null}
                {e.note ? <span className="dm-note">{e.note}</span> : null}
              </div>
            ))
          )}
        </td>
      ))}
    </tr>
  )

  return (
    <div className="table-scroll">
      <table className="duty-matrix">
        <thead>
          <tr>
            <th className="dm-role">Cương vị trực</th>
            {days.map((d) => (
              <th key={d.date} className={d.is_today ? 'is-today' : undefined}>
                <span>{d.weekday_label}</span>
                <em>{ddmm(d.date)}</em>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tree.kind === 'flat'
            ? tree.groups.map((g) => (
                <Fragment key={g.key}>
                  <tr className={`dm-band tone-${g.tone}`}>
                    <th colSpan={n + 1}>{g.label}</th>
                  </tr>
                  {g.rows.map(renderRow)}
                </Fragment>
              ))
            : tree.units.map((u) => (
                <Fragment key={u.uid}>
                  <tr className="dm-unit-band">
                    <th colSpan={n + 1}>{u.name}</th>
                  </tr>
                  {u.subGroups.map((g) => (
                    <Fragment key={g.key}>
                      <tr className={`dm-band tone-${g.tone}`}>
                        <th colSpan={n + 1}>{g.label}</th>
                      </tr>
                      {g.rows.map(renderRow)}
                    </Fragment>
                  ))}
                </Fragment>
              ))}
          {hasMuster ? (
            <tr className="dm-muster">
              <th className="dm-role">Quân số có mặt</th>
              {days.map((d) => (
                <td key={d.date} className={d.is_today ? 'is-today' : undefined}>
                  {d.muster ?? '—'}
                </td>
              ))}
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  )
}

function DutyLegend() {
  return (
    <div className="duty-legend">
      {DUTY_TYPES.map((t) => (
        <span key={t} className={`duty-legend-item tone-${DUTY_TYPE_TONE[t] ?? 'gray'}`}>
          <i aria-hidden="true" /> {DUTY_TYPE_LABELS[t]}
        </span>
      ))}
    </div>
  )
}

function WeekNav({
  weekOf,
  onChange,
}: {
  weekOf: string
  onChange: (iso: string) => void
}) {
  const monday = mondayOf(weekOf)
  return (
    <div className="duty-nav">
      <button type="button" className="btn-cancel" onClick={() => onChange(addDays(monday, -7))}>
        <Icon name="arrow-left" size={14} /> Tuần trước
      </button>
      <input type="date" value={weekOf} onChange={(e) => onChange(e.target.value)} />
      <button type="button" className="btn-cancel" onClick={() => onChange(addDays(monday, 7))}>
        Tuần sau <Icon name="chevron-right" size={14} />
      </button>
      <button type="button" className="btn-cancel" onClick={() => onChange(todayIso())}>
        Tuần này
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------- Page
export function DutyRosterPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<TabKey>('week')

  return (
    <section className="duty-page">
      <div className="crumb-bar no-print">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Điều hành – Nhiệm vụ</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">Lịch trực – Kíp trực</span>
        </nav>
      </div>

      <header className="cdb-head no-print">
        <div>
          <h1>
            <Icon name="clock" size={22} /> Lịch trực – Kíp trực
          </h1>
          <p className="state-note">
            Biểu trực toàn Lữ đoàn do Phòng Tham mưu tổng hợp, phân cấp từ Ban chỉ huy Lữ đoàn
            xuống các tiểu đoàn, trung tâm. Chỉ huy Lữ đoàn thẩm định &amp; phê duyệt; toàn đơn vị
            theo dõi và in biểu trực tuần.
          </p>
        </div>
      </header>

      <details className="duty-guide no-print">
        <summary>Hướng dẫn nhanh — 4 thẻ &amp; quy trình trực ban</summary>
        <div className="duty-guide-body">
          <div>
            <h4>1. Biểu trực tuần</h4>
            <p>
              Xem tổng hợp 7 ngày (Thứ Hai → Chủ nhật). Đổi tuần bằng nút{' '}
              <em>Tuần trước / Tuần này / Tuần sau</em>; chọn phạm vi <em>Toàn Lữ đoàn</em> hoặc theo{' '}
              <em>khối cơ quan / từng đơn vị</em>. Có chú giải màu theo 7 loại trực và nút{' '}
              <em>In biểu trực</em>. Chỉ bảng đã <strong>Đã duyệt</strong> mới lên bảng tổng hợp
              chung; chỉ huy Lữ đoàn thấy mọi trạng thái để đôn đốc.
            </p>
          </div>
          <div>
            <h4>2. Kíp trực ngày</h4>
            <p>
              Xem chi tiết kíp trực của một ngày cụ thể, gom theo đơn vị, kèm tổng quân số có mặt /
              quân số biên chế từng kíp.
            </p>
          </div>
          <div>
            <h4>3. Lập &amp; duyệt bảng trực</h4>
            <p>
              Trực ban đơn vị tạo bảng trực tuần, thêm từng dòng ca trực (ngày, loại trực, ca, sĩ
              quan trực, chức trách, số điện thoại, quân số, ghi chú) rồi <em>Gửi duyệt</em>. Luồng
              trạng thái:
            </p>
            <p className="duty-guide-flow">
              Nháp → Chờ duyệt → Đã duyệt / Trả lại (kèm lý do) → có thể Mở lại để sửa.
            </p>
            <p>
              Mỗi đơn vị chỉ có <strong>một</strong> bảng cho mỗi tuần. <strong>Phê duyệt / Trả
              lại</strong> là quyền của chỉ huy / quản trị.
            </p>
          </div>
          <div>
            <h4>4. Sổ bàn giao &amp; Nhật ký kíp trực</h4>
            <p>Biên bản bàn giao ca điện tử gắn với một dòng ca trực. Quy trình 3 bước:</p>
            <ol>
              <li>
                <strong>Kíp trước lập biên bản</strong>: tình hình quân số, khí tài thông tin liên
                lạc – vũ khí trang bị, nhật ký sự vụ / mệnh lệnh trong ca, nhiệm vụ còn dở dang.
              </li>
              <li>
                <strong>Kíp sau đối soát &amp; ký nhận điện tử</strong>: chọn <em>Đã nhận</em> hoặc{' '}
                <em>Có kiến nghị</em> (kèm ghi chú phản hồi).
              </li>
              <li>
                <strong>Chỉ huy ca trực</strong> kiểm tra và ghi ý kiến chỉ đạo vào sổ.
              </li>
            </ol>
            <p>Trạng thái biên bản: Chờ nhận / Đã nhận / Có kiến nghị — đều lưu vết thời gian, người giao – người nhận.</p>
          </div>
        </div>
      </details>

      <div className="tab-bar no-print">
        <button
          type="button"
          className={tab === 'week' ? 'tab active' : 'tab'}
          onClick={() => setTab('week')}
        >
          <Icon name="calendar" size={14} /> Biểu trực tuần
        </button>
        <button
          type="button"
          className={tab === 'day' ? 'tab active' : 'tab'}
          onClick={() => setTab('day')}
        >
          <Icon name="clock" size={14} /> Kíp trực ngày
        </button>
        <button
          type="button"
          className={tab === 'manage' ? 'tab active' : 'tab'}
          onClick={() => setTab('manage')}
        >
          <Icon name="clipboard" size={14} /> Lập &amp; duyệt bảng trực
        </button>
        <button
          type="button"
          className={tab === 'handover' ? 'tab active' : 'tab'}
          onClick={() => setTab('handover')}
        >
          <Icon name="book" size={14} /> Sổ bàn giao &amp; Nhật ký kíp trực
        </button>
      </div>

      {tab === 'week' ? <WeekBoardTab /> : null}
      {tab === 'day' ? <DayBoardTab /> : null}
      {tab === 'manage' ? <ManageTab /> : null}
      {tab === 'handover' ? <HandoverTabWrapper /> : null}
    </section>
  )
}

function HandoverTabWrapper() {
  const scope = useScope()
  return <DutyShiftHandoverTab units={scope.units} />
}

// ------------------------------------------------------------- Tab 1: biểu trực tuần
function WeekBoardTab() {
  const { role } = useAuth()
  const confirm = useConfirm()
  const scope = useScope()
  const canApprove = role != null && role <= 2

  const [weekOf, setWeekOf] = useState(todayIso())
  const [board, setBoard] = useState<DutyWeekBoard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reload, setReload] = useState(0)
  const [returnOpen, setReturnOpen] = useState(false)
  const [returnReason, setReturnReason] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setLoading(true)
    dutySchedulesApi
      .weekBoard(weekOf)
      .then(setBoard)
      .catch((e: unknown) => setError(errMsg(e, 'Không thể tải bảng trực tuần')))
      .finally(() => setLoading(false))
  }, [weekOf, reload])

  const days: MatrixDay[] = useMemo(() => {
    if (!board) return []
    return board.days.map((d) => {
      const entries = d.entries.filter((e) => scope.inScope(e.unit_id))
      const present = entries.reduce((s, e) => s + (e.personnel_present ?? 0), 0)
      const totalP = entries.reduce((s, e) => s + (e.personnel_total ?? 0), 0)
      return {
        date: d.date,
        weekday_label: d.weekday_label,
        is_today: d.is_today,
        entries,
        muster: present || totalP ? `${present}/${totalP}` : '—',
      }
    })
  }, [board, scope])

  const scopePlans = useMemo(
    () => (board?.unit_plans ?? []).filter((p) => scope.inScope(p.unit_id)),
    [board, scope],
  )
  const pending = scopePlans.filter((p) => p.status === 'cho_duyet')
  const totalEntries = days.reduce((s, d) => s + d.entries.length, 0)

  const agg = useMemo(() => {
    if (scopePlans.length === 0) return { cls: 'nhap', text: 'Chưa có bảng trực' }
    if (pending.length > 0)
      return { cls: 'cho_duyet', text: `Chờ Chỉ huy duyệt (${pending.length} bảng)` }
    if (scopePlans.every((p) => p.status === 'da_duyet'))
      return { cls: 'da_duyet', text: 'Đã phê duyệt' }
    return { cls: 'tra_lai', text: 'Yêu cầu sửa / chưa trình đủ' }
  }, [scopePlans, pending.length])

  async function reviewPlans(status: 'da_duyet' | 'tra_lai', note: string | null) {
    setBusy(true)
    setError(null)
    try {
      await Promise.all(
        pending.map((p) => dutyWeekPlansApi.review(p.plan_id, { status, review_note: note })),
      )
      setReturnOpen(false)
      setReturnReason('')
      setReload((x) => x + 1)
    } catch (err) {
      setError(errMsg(err, 'Không thực hiện được thao tác phê duyệt'))
    } finally {
      setBusy(false)
    }
  }

  async function approveAll() {
    const ok = await confirm({
      title: 'Phê duyệt biểu trực',
      confirmText: 'Phê duyệt',
      message: (
        <>
          Phê duyệt <strong>{pending.length}</strong> bảng trực tuần đang chờ trong phạm vi{' '}
          <strong>{scope.label}</strong>? Bảng đã duyệt sẽ hiển thị chính thức cho toàn đơn vị.
        </>
      ),
    })
    if (ok) reviewPlans('da_duyet', null)
  }

  return (
    <div className="duty-print">
      <ScopeSelector scope={scope} />

      <div className="duty-toolbar no-print">
        <WeekNav weekOf={weekOf} onChange={setWeekOf} />
        <div className="duty-toolbar-right">
          <button type="button" className="btn-create" onClick={() => window.print()}>
            <Icon name="file" size={15} /> In biểu trực
          </button>
        </div>
      </div>

      {error ? (
        <p className="form-error cdb-alert" role="alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      {loading && !board ? (
        <div className="cdb-skeleton-list">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="cdb-skeleton-row" />
          ))}
        </div>
      ) : !board ? null : (
        <>
          <div className="duty-board-title">
            <h2>BIỂU TRỰC TUẦN</h2>
            <p>
              {board.week_label} · {scope.label}
            </p>
            <p className="duty-board-sub">
              {totalEntries} ca trực · {scopePlans.filter((p) => p.status === 'da_duyet').length}/
              {scopePlans.length} bảng đơn vị đã duyệt
            </p>
          </div>

          {canApprove ? (
            <div className="duty-approve-bar no-print">
              <span className={`duty-agg st-${agg.cls}`}>
                {agg.cls === 'da_duyet' ? <Icon name="check" size={14} /> : null}
                {agg.cls === 'cho_duyet' ? <Icon name="clock" size={14} /> : null}
                {agg.text}
              </span>
              {agg.cls === 'da_duyet' ? (
                <span className="duty-seal">
                  <Icon name="shield" size={13} /> Đã ký duyệt điện tử
                </span>
              ) : null}
              <div className="duty-approve-actions">
                <button
                  type="button"
                  className="btn-submit"
                  disabled={busy || pending.length === 0}
                  onClick={approveAll}
                >
                  <Icon name="check" size={14} /> Phê duyệt lịch trực
                </button>
                <button
                  type="button"
                  className="btn-delete"
                  disabled={busy || pending.length === 0}
                  onClick={() => setReturnOpen(true)}
                >
                  <Icon name="undo" size={14} /> Trả lại / Yêu cầu Tham mưu sửa
                </button>
                <button
                  type="button"
                  className="btn-cancel"
                  disabled
                  title="Chức năng lưu &amp; tải file gốc từ Phòng Tham mưu sẽ bổ sung ở bản cập nhật sau"
                >
                  <Icon name="download" size={14} /> Tải file gốc Tham mưu
                  <span className="duty-soon">Sắp có</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="duty-approve-bar no-print">
              <span className={`duty-agg st-${agg.cls}`}>{agg.text}</span>
              <div className="duty-approve-actions">
                <button type="button" className="btn-cancel" onClick={() => window.print()}>
                  <Icon name="file" size={14} /> In biểu trực tuần / Xuất PDF
                </button>
              </div>
            </div>
          )}

          <DutyLegend />

          <DutyMatrix days={days} groupByUnit unitRank={scope.unitRank} />

          <div className="duty-approval">
            <h3>Tình hình phê duyệt bảng trực tuần theo đơn vị</h3>
            {scopePlans.length === 0 ? (
              <p className="state-note">Chưa đơn vị nào lập bảng trực tuần này trong phạm vi.</p>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Đơn vị</th>
                      <th>Trạng thái</th>
                      <th>Số ca</th>
                      <th>Đã trình</th>
                      <th>Đã duyệt</th>
                      {canApprove ? <th aria-label="Thao tác" /> : null}
                    </tr>
                  </thead>
                  <tbody>
                    {scopePlans.map((p) => (
                      <tr key={p.plan_id}>
                        <td>{p.unit_name}</td>
                        <td>
                          <StatusChip status={p.status} label={p.status_label} />
                        </td>
                        <td>{p.entry_count}</td>
                        <td>{formatDateTime(p.submitted_at)}</td>
                        <td>{formatDateTime(p.reviewed_at)}</td>
                        {canApprove ? (
                          <td>
                            {p.status === 'cho_duyet' ? (
                              <div className="row-actions">
                                <button
                                  type="button"
                                  className="btn-approve"
                                  disabled={busy}
                                  onClick={() =>
                                    dutyWeekPlansApi
                                      .review(p.plan_id, { status: 'da_duyet', review_note: null })
                                      .then(() => setReload((x) => x + 1))
                                      .catch((e: unknown) =>
                                        setError(errMsg(e, 'Không duyệt được')),
                                      )
                                  }
                                >
                                  <Icon name="check" /> Duyệt
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
          </div>
        </>
      )}

      {returnOpen ? (
        <Modal title="Trả lại biểu trực — yêu cầu Tham mưu chỉnh sửa" onClose={() => setReturnOpen(false)}>
          <p className="state-note">
            Nội dung phản hồi sẽ gửi kèm về {pending.length} bảng trực đang chờ duyệt trong phạm vi{' '}
            <strong>{scope.label}</strong>.
          </p>
          <label>
            Lý do / nội dung yêu cầu sửa
            <textarea
              rows={4}
              maxLength={500}
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              placeholder="VD: Bổ sung kíp trực Trạm Thông tin cơ quan ngày Thứ Bảy; ghi rõ SĐT trực chỉ huy d2..."
            />
          </label>
          <div className="form-actions">
            <button
              type="button"
              className="btn-delete"
              disabled={busy || !returnReason.trim()}
              onClick={() => reviewPlans('tra_lai', returnReason.trim())}
            >
              <Icon name="undo" size={14} /> Gửi trả lại
            </button>
            <button type="button" className="btn-cancel" onClick={() => setReturnOpen(false)}>
              Huỷ
            </button>
          </div>
        </Modal>
      ) : null}
    </div>
  )
}

// ------------------------------------------------------------- Tab 2: kíp trực ngày
function DayBoardTab() {
  const scope = useScope()
  const [day, setDay] = useState(todayIso())
  const [board, setBoard] = useState<DutyDayBoard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [createSchedule, setCreateSchedule] = useState<DutySchedule | null>(null)
  const [viewHandover, setViewHandover] = useState<DutyShiftHandover | null>(null)
  const [checkingEntryId, setCheckingEntryId] = useState<number | null>(null)

  const handleOpenHandoverForEntry = async (entry: DutySchedule) => {
    setCheckingEntryId(entry.id)
    try {
      const existing = await dutyShiftHandoversApi.getBySchedule(entry.id)
      if (existing) {
        setViewHandover(existing)
      } else {
        setCreateSchedule(entry)
      }
    } catch {
      setCreateSchedule(entry)
    } finally {
      setCheckingEntryId(null)
    }
  }

  useEffect(() => {
    setLoading(true)
    dutySchedulesApi
      .dayBoard(day)
      .then(setBoard)
      .catch((e: unknown) => setError(errMsg(e, 'Không thể tải kíp trực theo ngày')))
      .finally(() => setLoading(false))
  }, [day])

  const groups = useMemo(
    () => (board?.groups ?? []).filter((g) => scope.inScope(g.unit_id)),
    [board, scope],
  )
  const totalEntries = groups.reduce((s, g) => s + g.entry_count, 0)
  const present = groups.reduce((s, g) => s + g.personnel_present, 0)
  const totalP = groups.reduce((s, g) => s + g.personnel_total, 0)

  return (
    <div className="duty-print">
      <ScopeSelector scope={scope} />

      <div className="duty-toolbar no-print">
        <div className="duty-nav">
          <button type="button" className="btn-cancel" onClick={() => setDay(addDays(day, -1))}>
            <Icon name="arrow-left" size={14} /> Hôm trước
          </button>
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
          <button type="button" className="btn-cancel" onClick={() => setDay(addDays(day, 1))}>
            Hôm sau <Icon name="chevron-right" size={14} />
          </button>
          <button type="button" className="btn-cancel" onClick={() => setDay(todayIso())}>
            Hôm nay
          </button>
        </div>
        <div className="duty-toolbar-right">
          <button type="button" className="btn-create" onClick={() => window.print()}>
            <Icon name="file" size={15} /> In danh sách
          </button>
        </div>
      </div>

      {error ? (
        <p className="form-error cdb-alert" role="alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      {loading && !board ? (
        <div className="cdb-skeleton-list">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="cdb-skeleton-row" />
          ))}
        </div>
      ) : !board ? null : (
        <>
          <div className="duty-board-title">
            <h2>DANH SÁCH KÍP TRỰC</h2>
            <p>
              {board.weekday_label}, {formatDate(board.date)} · {scope.label}
            </p>
          </div>

          <div className="cdb-stats">
            <div className="cdb-stat">
              <span className="cdb-stat-value">{groups.length}</span>
              <span className="cdb-stat-label">Đơn vị có ca trực</span>
            </div>
            <div className="cdb-stat cdb-stat-open">
              <span className="cdb-stat-value">{totalEntries}</span>
              <span className="cdb-stat-label">Tổng ca trực</span>
            </div>
            <div className="cdb-stat cdb-stat-done">
              <span className="cdb-stat-value">{muster(present, totalP)}</span>
              <span className="cdb-stat-label">Quân số có mặt</span>
            </div>
          </div>

          {groups.length === 0 ? (
            <EmptyState icon="clock" message="Chưa có bảng trực tuần đã duyệt nào phủ ngày này." />
          ) : (
            groups.map((g) => (
              <div className="duty-daycard" key={g.unit_id ?? g.unit_name}>
                <header>
                  <h3>{g.unit_name}</h3>
                  {g.plan_status && g.plan_status_label ? (
                    <StatusChip status={g.plan_status} label={g.plan_status_label} />
                  ) : null}
                  <span className="duty-daycard-meta">
                    {g.entry_count} ca · quân số{' '}
                    <strong>{muster(g.personnel_present, g.personnel_total)}</strong>
                  </span>
                </header>
                <EntryTable
                  entries={g.entries}
                  showUnit={false}
                  actions={(entry) => (
                    <button
                      type="button"
                      className="btn-view text-xs flex items-center gap-1"
                      disabled={checkingEntryId === entry.id}
                      onClick={() => handleOpenHandoverForEntry(entry)}
                      title="Lập hoặc xem biên bản bàn giao ca trực"
                    >
                      <Icon name="book" size={12} />
                      <span>{checkingEntryId === entry.id ? 'Đang tải...' : 'Bàn giao ca'}</span>
                    </button>
                  )}
                />
              </div>
            ))
          )}
        </>
      )}

      {createSchedule && (
        <DutyShiftHandoverCreateModal
          schedule={createSchedule}
          onClose={() => setCreateSchedule(null)}
          onSuccess={() => setCreateSchedule(null)}
        />
      )}

      {viewHandover && (
        <DutyShiftHandoverDetailModal
          handover={viewHandover}
          onClose={() => setViewHandover(null)}
          onUpdated={() => setViewHandover(null)}
        />
      )}
    </div>
  )
}

function EntryTable({
  entries,
  showUnit,
  actions,
}: {
  entries: DutySchedule[]
  showUnit: boolean
  actions?: (entry: DutySchedule) => ReactNode
}) {
  const ordered = useMemo(() => {
    const rank = (t: string) => {
      const i = DUTY_TYPE_ORDER.indexOf(t as DutyType)
      return i < 0 ? DUTY_TYPE_ORDER.length : i
    }
    return [...entries].sort(
      (a, b) => rank(a.duty_type) - rank(b.duty_type) || a.role_title.localeCompare(b.role_title, 'vi'),
    )
  }, [entries])

  return (
    <div className="table-scroll">
      <table className="data-table duty-table">
        <thead>
          <tr>
            {showUnit ? <th>Đơn vị</th> : null}
            <th>Cấp trực</th>
            <th>Chức trách</th>
            <th>Ca / kíp</th>
            <th>Người trực</th>
            <th>SĐT</th>
            <th>Quân số</th>
            <th>Ghi chú</th>
            {actions ? <th aria-label="Thao tác" /> : null}
          </tr>
        </thead>
        <tbody>
          {ordered.map((e) => (
            <tr key={e.id}>
              {showUnit ? <td>{e.unit_name ?? '—'}</td> : null}
              <td>
                <span className={`duty-type-dot tone-${DUTY_TYPE_TONE[e.duty_type] ?? 'gray'}`} />
                {e.duty_type_label}
              </td>
              <td>{e.role_title}</td>
              <td>{e.shift}</td>
              <td className="duty-officer-cell">{e.duty_officer}</td>
              <td>{e.contact_phone ?? '—'}</td>
              <td>{muster(e.personnel_present, e.personnel_total)}</td>
              <td>{e.note ?? '—'}</td>
              {actions ? <td>{actions(e)}</td> : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ------------------------------------------------- Tab 3: lập & duyệt bảng trực đơn vị
function ManageTab() {
  const { canEditContent, isCommander, unitId } = useAuth()

  const [units, setUnits] = useState<Unit[]>([])
  const [plans, setPlans] = useState<DutyWeekPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [fUnit, setFUnit] = useState('')
  const [fWeek, setFWeek] = useState('')
  const [fStatus, setFStatus] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [cUnit, setCUnit] = useState('')
  const [cWeek, setCWeek] = useState(todayIso())
  const [cNote, setCNote] = useState('')
  const planReq = useRequiredFields(
    isCommander ? (['unit', 'week'] as const) : (['week'] as const),
  )
  const [busy, setBusy] = useState(false)

  const [openId, setOpenId] = useState<number | null>(null)

  const loadPlans = useCallback(() => {
    setLoading(true)
    dutyWeekPlansApi
      .list({
        unitId: fUnit ? Number(fUnit) : undefined,
        weekOf: fWeek || undefined,
        status: fStatus || undefined,
      })
      .then(setPlans)
      .catch((e: unknown) => setError(errMsg(e, 'Không thể tải danh sách bảng trực tuần')))
      .finally(() => setLoading(false))
  }, [fUnit, fWeek, fStatus])

  useEffect(() => {
    unitsApi.list({ active: true }).then(setUnits).catch(() => setUnits([]))
  }, [])
  useEffect(loadPlans, [loadPlans])

  const stats = useMemo(() => {
    const s = { total: plans.length, nhap: 0, cho_duyet: 0, da_duyet: 0, tra_lai: 0 }
    for (const p of plans) s[p.status] += 1
    return s
  }, [plans])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!planReq.validate(isCommander ? { unit: cUnit, week: cWeek } : { week: cWeek })) return
    setBusy(true)
    try {
      const unit_id = isCommander ? Number(cUnit) : unitId ?? 0
      if (!unit_id) {
        setError(isCommander ? 'Chọn đơn vị' : 'Tài khoản chưa được gán đơn vị')
        return
      }
      await dutyWeekPlansApi.create({ unit_id, week_start: cWeek, note: cNote || null })
      setShowCreate(false)
      setCNote('')
      loadPlans()
    } catch (err) {
      setError(errMsg(err, 'Không thể lập bảng trực tuần'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="cdb-stats">
        <div className="cdb-stat">
          <span className="cdb-stat-value">{stats.total}</span>
          <span className="cdb-stat-label">Tổng bảng trực</span>
        </div>
        <div className="cdb-stat cdb-stat-unread">
          <span className="cdb-stat-value">{stats.cho_duyet}</span>
          <span className="cdb-stat-label">Chờ duyệt</span>
        </div>
        <div className="cdb-stat cdb-stat-done">
          <span className="cdb-stat-value">{stats.da_duyet}</span>
          <span className="cdb-stat-label">Đã duyệt</span>
        </div>
        <div className="cdb-stat cdb-stat-closed">
          <span className="cdb-stat-value">{stats.nhap + stats.tra_lai}</span>
          <span className="cdb-stat-label">Nháp / trả lại</span>
        </div>
      </div>

      <div className="duty-toolbar">
        <div className="duty-toolbar-right" style={{ flexWrap: 'wrap' }}>
          {isCommander ? (
            <select value={fUnit} onChange={(e) => setFUnit(e.target.value)}>
              <option value="">Mọi đơn vị</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          ) : null}
          <input
            type="date"
            value={fWeek}
            onChange={(e) => setFWeek(e.target.value)}
            aria-label="Tuần chứa ngày"
          />
          <select value={fStatus} onChange={(e) => setFStatus(e.target.value)}>
            <option value="">Mọi trạng thái</option>
            {PLAN_STATUSES.map((s) => (
              <option key={s} value={s}>
                {PLAN_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>
        {canEditContent && !showCreate ? (
          <button type="button" className="btn-create" onClick={() => setShowCreate(true)}>
            <Icon name="plus" size={15} /> Lập bảng trực tuần
          </button>
        ) : null}
      </div>

      {showCreate ? (
        <form onSubmit={handleCreate} className="entity-form cdb-create">
          <div className="card-head">
            <h2>
              <Icon name="plus" size={16} /> Lập bảng trực tuần mới
            </h2>
            <p>Chọn ngày bất kỳ trong tuần — hệ thống quy về Thứ Hai đầu tuần.</p>
          </div>
          {isCommander ? (
            <Field label="Đơn vị" required req={planReq} name="unit">
              <select
                value={cUnit}
                onChange={(e) => setCUnit(e.target.value)}
                onBlur={(e) => planReq.mark('unit', e.target.value)}
                required
              >
                <option value="">— Chọn đơn vị —</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </Field>
          ) : (
            <p className="state-note">
              Bảng trực sẽ lập cho đơn vị của bạn. Nếu tài khoản chưa được gán đơn vị, liên hệ quản
              trị.
            </p>
          )}
          <Field label="Tuần trực" required req={planReq} name="week">
            <input
              type="date"
              value={cWeek}
              onChange={(e) => setCWeek(e.target.value)}
              onBlur={(e) => planReq.mark('week', e.target.value)}
              required
            />
          </Field>
          <label>
            Ghi chú chung
            <textarea
              rows={2}
              maxLength={500}
              value={cNote}
              onChange={(e) => setCNote(e.target.value)}
            />
          </label>
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={busy}>
              {busy ? 'Đang lập...' : 'Lập bảng'}
            </button>
            <button type="button" className="btn-cancel" onClick={() => setShowCreate(false)}>
              Huỷ
            </button>
          </div>
        </form>
      ) : null}

      {error ? (
        <p className="form-error cdb-alert" role="alert">
          <Icon name="alert-triangle" size={14} /> {error}
        </p>
      ) : null}

      {loading ? (
        <div className="cdb-skeleton-list">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="cdb-skeleton-row" />
          ))}
        </div>
      ) : plans.length === 0 ? (
        <EmptyState icon="clipboard" message="Chưa có bảng trực tuần nào khớp bộ lọc." />
      ) : (
        <div className="duty-plan-list">
          {plans.map((p) => (
            <PlanCard
              key={p.id}
              plan={p}
              open={openId === p.id}
              onToggle={() => setOpenId(openId === p.id ? null : p.id)}
              onChanged={loadPlans}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function PlanCard({
  plan,
  open,
  onToggle,
  onChanged,
}: {
  plan: DutyWeekPlan
  open: boolean
  onToggle: () => void
  onChanged: () => void
}) {
  const { isCommander, unitId, canEditContent } = useAuth()
  const confirm = useConfirm()
  const [detail, setDetail] = useState<DutyWeekPlanDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [reviewNote, setReviewNote] = useState('')

  const isOwnerUnit = isCommander || plan.unit_id === unitId
  const editable = (plan.status === 'nhap' || plan.status === 'tra_lai') && isOwnerUnit

  const loadDetail = useCallback(() => {
    dutyWeekPlansApi
      .get(plan.id)
      .then(setDetail)
      .catch((e: unknown) => setError(errMsg(e, 'Không thể tải chi tiết bảng trực')))
  }, [plan.id])

  useEffect(() => {
    if (open) loadDetail()
  }, [open, loadDetail])

  async function run(fn: () => Promise<unknown>, fallback: string) {
    setError(null)
    setBusy(true)
    try {
      await fn()
      onChanged()
      if (open) loadDetail()
    } catch (err) {
      setError(errMsg(err, fallback))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={`duty-plan${open ? ' open' : ''}`}>
      <div className="duty-plan-head">
        <div className="duty-plan-id">
          <span className="duty-plan-unit">{plan.unit_name}</span>
          <span className="duty-plan-week">
            <Icon name="calendar" size={12} /> {plan.week_label} · {formatDate(plan.week_start)} –{' '}
            {formatDate(plan.week_end)}
          </span>
        </div>
        <div className="duty-plan-right">
          <StatusChip status={plan.status} label={plan.status_label} />
          <span className="duty-plan-meta">
            {plan.entry_count} ca · quân số{' '}
            <strong>{muster(plan.personnel_present, plan.personnel_total)}</strong>
            {plan.attachment_count > 0 ? (
              <>
                {' '}
                · <Icon name="paperclip" size={12} /> {plan.attachment_count}
              </>
            ) : null}
          </span>
          <button type="button" className="btn-view" onClick={onToggle}>
            <Icon name={open ? 'eye-off' : 'eye'} /> {open ? 'Thu gọn' : 'Chi tiết'}
          </button>
        </div>
      </div>

      <p className="duty-plan-trail">
        Lập bởi {plan.author_full_name}
        {plan.submitted_by_name
          ? ` · Trình: ${plan.submitted_by_name} (${formatDateTime(plan.submitted_at)})`
          : ''}
        {plan.reviewed_by_name
          ? ` · Duyệt: ${plan.reviewed_by_name} (${formatDateTime(plan.reviewed_at)})`
          : ''}
      </p>
      {plan.note ? <p className="duty-plan-note">{plan.note}</p> : null}
      {plan.review_note ? (
        <p className="review-note">
          <Icon name="shield" size={12} /> Ý kiến duyệt: {plan.review_note}
        </p>
      ) : null}

      <div className="row-actions">
        {isOwnerUnit && (plan.status === 'nhap' || plan.status === 'tra_lai') ? (
          <button
            type="button"
            className="btn-approve"
            disabled={busy}
            onClick={() => run(() => dutyWeekPlansApi.submit(plan.id), 'Không thể trình duyệt')}
          >
            <Icon name="send" /> Trình duyệt
          </button>
        ) : null}
        {isOwnerUnit && plan.status === 'nhap' ? (
          <button
            type="button"
            className="btn-delete"
            disabled={busy}
            onClick={async () => {
              const ok = await confirm({
                message: (
                  <>
                    Xoá bảng trực tuần <strong>{plan.week_label}</strong> của {plan.unit_name}? Thao
                    tác này không thể hoàn tác.
                  </>
                ),
              })
              if (ok) run(() => dutyWeekPlansApi.remove(plan.id), 'Không thể xoá')
            }}
          >
            <Icon name="trash" /> Xoá
          </button>
        ) : null}
        {isOwnerUnit && plan.status === 'cho_duyet' ? (
          <button
            type="button"
            className="btn-view"
            disabled={busy}
            onClick={() => run(() => dutyWeekPlansApi.reopen(plan.id), 'Không thể rút lại')}
          >
            <Icon name="undo" /> Rút lại
          </button>
        ) : null}
        {isCommander && plan.status === 'da_duyet' ? (
          <button
            type="button"
            className="btn-view"
            disabled={busy}
            onClick={() => run(() => dutyWeekPlansApi.reopen(plan.id), 'Không thể mở lại')}
          >
            <Icon name="undo" /> Mở lại
          </button>
        ) : null}
      </div>

      {isCommander && plan.status === 'cho_duyet' ? (
        <div className="duty-review">
          <input
            type="text"
            maxLength={500}
            placeholder="Ý kiến duyệt / lý do trả lại (không bắt buộc)"
            value={reviewNote}
            onChange={(e) => setReviewNote(e.target.value)}
          />
          <div className="form-actions">
            <button
              type="button"
              className="btn-approve"
              disabled={busy}
              onClick={() =>
                run(
                  () =>
                    dutyWeekPlansApi.review(plan.id, {
                      status: 'da_duyet',
                      review_note: reviewNote || null,
                    }),
                  'Không thể duyệt',
                )
              }
            >
              <Icon name="check" /> Duyệt
            </button>
            <button
              type="button"
              className="btn-delete"
              disabled={busy}
              onClick={() =>
                run(
                  () =>
                    dutyWeekPlansApi.review(plan.id, {
                      status: 'tra_lai',
                      review_note: reviewNote || null,
                    }),
                  'Không thể trả lại',
                )
              }
            >
              <Icon name="undo" /> Trả lại
            </button>
          </div>
        </div>
      ) : null}

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}

      {open && detail ? (
        <>
          <PlanEntries
            detail={detail}
            editable={editable && canEditContent}
            onChanged={() => {
              onChanged()
              loadDetail()
            }}
          />
          <PlanAttachments
            detail={detail}
            canEdit={isOwnerUnit && canEditContent}
            onChanged={() => {
              onChanged()
              loadDetail()
            }}
          />
        </>
      ) : null}
    </div>
  )
}

function PlanAttachments({
  detail,
  canEdit,
  onChanged,
}: {
  detail: DutyWeekPlanDetail
  canEdit: boolean
  onChanged: () => void
}) {
  const { userId, isCommander } = useAuth()
  const confirm = useConfirm()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const items = detail.attachments ?? []

  async function upload(file: File) {
    setError(null)
    setBusy(true)
    try {
      await dutyWeekPlansApi.uploadAttachment(detail.id, file, label)
      setLabel('')
      onChanged()
    } catch (err) {
      setError(errMsg(err, 'Không thể đính kèm tệp'))
    } finally {
      setBusy(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function remove(att: DutyPlanAttachment) {
    const ok = await confirm({
      message: (
        <>
          Xoá tệp đính kèm <strong>{att.original_name}</strong> khỏi bảng trực này?
        </>
      ),
    })
    if (!ok) return
    setError(null)
    setBusy(true)
    try {
      await dutyWeekPlansApi.deleteAttachment(detail.id, att.id)
      onChanged()
    } catch (err) {
      setError(errMsg(err, 'Không thể xoá tệp'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="duty-attach">
      <div className="duty-attach-head">
        <Icon name="paperclip" size={13} /> Tệp đính kèm ({items.length})
      </div>

      {items.length === 0 ? (
        <p className="state-note">Chưa có tệp lịch trực nào được đính kèm.</p>
      ) : (
        <ul className="duty-attach-list">
          {items.map((att) => (
            <li key={att.id}>
              <a href={staticUrl(att.file_url)} target="_blank" rel="noreferrer" className="duty-attach-name">
                <Icon name="file" size={13} /> {att.original_name}
              </a>
              {att.label ? <span className="duty-attach-label">{att.label}</span> : null}
              <span className="duty-attach-meta">
                {formatFileSize(att.file_size)} · {att.uploaded_by_name} ·{' '}
                {formatDateTime(att.created_at)}
              </span>
              {isCommander || att.uploaded_by_id === userId ? (
                <button
                  type="button"
                  className="btn-delete duty-attach-del"
                  disabled={busy}
                  onClick={() => remove(att)}
                  title="Xoá tệp"
                >
                  <Icon name="x" size={12} />
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {canEdit ? (
        <div className="duty-attach-upload">
          <input
            type="text"
            maxLength={200}
            placeholder="Mô tả ngắn (VD: Bản đã ký, Phụ lục quân số) — không bắt buộc"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept={DUTY_ATTACH_ACCEPT}
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) void upload(f)
            }}
          />
          <button
            type="button"
            className="btn-cancel"
            disabled={busy}
            onClick={() => fileInputRef.current?.click()}
          >
            <Icon name="upload" size={14} /> {busy ? 'Đang tải…' : 'Đính kèm tệp'}
          </button>
          <span className="state-note">
            Nhận PDF, Word, Excel, PowerPoint, ảnh (.jpg/.png/.webp/.gif). Đính kèm được ở mọi
            trạng thái bảng trực.
          </span>
        </div>
      ) : null}

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}

function PlanEntries({
  detail,
  editable,
  onChanged,
}: {
  detail: DutyWeekPlanDetail
  editable: boolean
  onChanged: () => void
}) {
  const confirm = useConfirm()
  const [form, setForm] = useState<DutyScheduleCreate>({
    ...emptyEntry,
    duty_date: detail.week_start,
  })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const entryReq = useRequiredFields([
    'duty_date',
    'shift',
    'role_title',
    'duty_officer',
  ] as const)

  const days: MatrixDay[] = useMemo(
    () =>
      Array.from({ length: 7 }, (_, i) => {
        const date = addDays(detail.week_start, i)
        return {
          date,
          weekday_label: WEEKDAYS[i],
          is_today: date === todayIso(),
          entries: detail.entries.filter((e) => e.duty_date === date),
        }
      }),
    [detail],
  )

  function reset() {
    setForm({ ...emptyEntry, duty_date: detail.week_start })
    setEditingId(null)
    setShowForm(false)
    entryReq.reset()
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (
      !entryReq.validate({
        duty_date: form.duty_date,
        shift: form.shift,
        role_title: form.role_title,
        duty_officer: form.duty_officer,
      })
    )
      return
    setBusy(true)
    try {
      const payload: DutyScheduleCreate = {
        ...form,
        contact_phone: form.contact_phone || null,
        note: form.note || null,
        personnel_present:
          form.personnel_present === null ? null : Number(form.personnel_present),
        personnel_total: form.personnel_total === null ? null : Number(form.personnel_total),
      }
      if (editingId !== null) await dutySchedulesApi.updateEntry(editingId, payload)
      else await dutyWeekPlansApi.addEntry(detail.id, payload)
      reset()
      onChanged()
    } catch (err) {
      setError(errMsg(err, 'Không thể lưu dòng ca trực'))
    } finally {
      setBusy(false)
    }
  }

  async function remove(id: number) {
    if (!(await confirm({ message: 'Xoá dòng ca trực này? Thao tác này không thể hoàn tác.' })))
      return
    setError(null)
    try {
      await dutySchedulesApi.removeEntry(id)
      onChanged()
    } catch (err) {
      setError(errMsg(err, 'Không thể xoá dòng ca trực'))
    }
  }

  function startEdit(entry: DutySchedule) {
    setEditingId(entry.id)
    setShowForm(true)
    setForm({
      duty_date: entry.duty_date,
      duty_type: (entry.duty_type as DutyType) ?? 'khac',
      shift: entry.shift,
      duty_officer: entry.duty_officer,
      role_title: entry.role_title,
      contact_phone: entry.contact_phone ?? '',
      personnel_present: entry.personnel_present,
      personnel_total: entry.personnel_total,
      note: entry.note ?? '',
    })
  }

  return (
    <div className="duty-plan-detail">
      {detail.entries.length === 0 ? (
        <p className="state-note">Chưa có dòng ca trực nào.</p>
      ) : (
        <DutyMatrix days={days} groupByUnit={false} />
      )}

      {detail.entries.length > 0 && editable ? (
        <div className="duty-plan-edit-list">
          <EntryTable
            entries={detail.entries}
            showUnit={false}
            actions={(entry) => (
              <div className="row-actions">
                <button type="button" className="btn-edit" onClick={() => startEdit(entry)}>
                  <Icon name="edit" /> Sửa
                </button>
                <button type="button" className="btn-delete" onClick={() => remove(entry.id)}>
                  <Icon name="trash" /> Xoá
                </button>
              </div>
            )}
          />
        </div>
      ) : null}

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}

      {editable ? (
        showForm ? (
          <form onSubmit={submit} className="entity-form duty-entry-form">
            <strong>{editingId !== null ? 'Sửa dòng ca trực' : 'Thêm dòng ca trực'}</strong>
            <div className="form-row">
              <Field label="Ngày trực" required req={entryReq} name="duty_date">
                <input
                  type="date"
                  value={form.duty_date}
                  min={detail.week_start}
                  max={detail.week_end}
                  onChange={(e) => setForm((f) => ({ ...f, duty_date: e.target.value }))}
                  onBlur={(e) => entryReq.mark('duty_date', e.target.value)}
                  required
                />
              </Field>
              <label>
                Cấp trực
                <select
                  value={form.duty_type}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, duty_type: e.target.value as DutyType }))
                  }
                >
                  {DUTY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {DUTY_TYPE_LABELS[t]}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="form-row">
              <Field label="Ca / kíp" required req={entryReq} name="shift">
                <input
                  type="text"
                  maxLength={50}
                  value={form.shift}
                  placeholder="VD: Ca ngày 06:00–18:00"
                  onChange={(e) => setForm((f) => ({ ...f, shift: e.target.value }))}
                  onBlur={(e) => entryReq.mark('shift', e.target.value)}
                  required
                />
              </Field>
              <Field label="Chức trách cụ thể" required req={entryReq} name="role_title">
                <input
                  type="text"
                  maxLength={100}
                  value={form.role_title}
                  placeholder="VD: Trực chỉ huy Lữ đoàn"
                  onChange={(e) => setForm((f) => ({ ...f, role_title: e.target.value }))}
                  onBlur={(e) => entryReq.mark('role_title', e.target.value)}
                  required
                />
              </Field>
            </div>
            <div className="form-row">
              <Field label="Người trực" required req={entryReq} name="duty_officer">
                <input
                  type="text"
                  maxLength={100}
                  value={form.duty_officer}
                  onChange={(e) => setForm((f) => ({ ...f, duty_officer: e.target.value }))}
                  onBlur={(e) => entryReq.mark('duty_officer', e.target.value)}
                  required
                />
              </Field>
              <label>
                SĐT trực
                <input
                  type="text"
                  maxLength={30}
                  value={form.contact_phone ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, contact_phone: e.target.value }))}
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                Quân số có mặt
                <input
                  type="number"
                  min={0}
                  value={form.personnel_present ?? ''}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      personnel_present: e.target.value === '' ? null : Number(e.target.value),
                    }))
                  }
                />
              </label>
              <label>
                Tổng quân số
                <input
                  type="number"
                  min={0}
                  value={form.personnel_total ?? ''}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      personnel_total: e.target.value === '' ? null : Number(e.target.value),
                    }))
                  }
                />
              </label>
            </div>
            <label>
              Ghi chú
              <textarea
                rows={2}
                maxLength={500}
                value={form.note ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
              />
            </label>
            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={busy}>
                {editingId !== null ? 'Cập nhật' : 'Thêm dòng'}
              </button>
              <button type="button" className="btn-cancel" onClick={reset}>
                Huỷ
              </button>
            </div>
          </form>
        ) : (
          <button
            type="button"
            className="btn-create duty-add-row"
            onClick={() => {
              setEditingId(null)
              setForm({ ...emptyEntry, duty_date: detail.week_start })
              setShowForm(true)
            }}
          >
            <Icon name="plus" size={15} /> Thêm dòng ca trực
          </button>
        )
      ) : null}
    </div>
  )
}
