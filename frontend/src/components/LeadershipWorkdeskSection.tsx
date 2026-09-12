import { useEffect, useMemo, useState } from 'react'
import { ApiError } from '../api/client'
import { leadershipTasksApi } from '../api/leadershipTasks'
import { unitsApi } from '../api/units'
import { EmptyState } from './EmptyState'
import { Icon } from './Icon'
import { Pagination } from './Pagination'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import {
  COMMANDER_ROLE_META,
  TASK_STATUS_META,
  TASK_URGENCY_META,
  type CommanderBranch,
  type CommanderRole,
  type LeadershipReviewStatus,
  type LeadershipTask,
  type LeadershipTaskCreatePayload,
  type TaskStatus,
  type TaskUrgency,
} from '../types/leadershipTask'
import type { Unit } from '../types/unit'

const BRANCH_OPTIONS: { value: CommanderBranch; label: string }[] = [
  { value: 'tham_muu', label: 'Khối Tham mưu (Tác chiến · SSCĐ · TTLL)' },
  { value: 'chinh_tri', label: 'Khối Chính trị (CTĐ-CTCT · Tuyên huấn)' },
  { value: 'hau_can_ky_thuat', label: 'Khối Hậu cần – Kỹ thuật (VKTB · Khí tài)' },
  { value: 'toan_lu_doan', label: 'Toàn thể Lữ đoàn' },
]

function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function fmtDate(dStr: string | null | undefined): string {
  if (!dStr) return '—'
  const d = new Date(dStr)
  if (isNaN(d.getTime())) return dStr
  return d.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function LeadershipWorkdeskSection() {
  const { role, isCommander } = useAuth()
  const toast = useToast()

  const isBCHCommander = useMemo(() => {
    return isCommander || (role !== null && role <= 2)
  }, [isCommander, role])

  // State danh sách
  const [tasks, setTasks] = useState<LeadershipTask[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Bộ lọc
  const [selectedRole, setSelectedRole] = useState<CommanderRole | 'all'>('all')
  const [selectedBranch, setSelectedBranch] = useState<CommanderBranch | ''>('')
  const [selectedUrgency, setSelectedUrgency] = useState<TaskUrgency | ''>('')
  const [selectedStatus, setSelectedStatus] = useState<TaskStatus | ''>('')
  const [page, setPage] = useState(1)
  const pageSize = 8

  // Đơn vị
  const [units, setUnits] = useState<Unit[]>([])

  // Modal ban hành chỉ đạo
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createRole, setCreateRole] = useState<CommanderRole>('lu_truong')
  const [createTitle, setCreateTitle] = useState('')
  const [createContent, setCreateContent] = useState('')
  const [createBranch, setCreateBranch] = useState<CommanderBranch>('tham_muu')
  const [createUnitId, setCreateUnitId] = useState<number | ''>('')
  const [createUrgency, setCreateUrgency] = useState<TaskUrgency>('khan')
  const [createDeadline, setCreateDeadline] = useState('')
  const [submittingCreate, setSubmittingCreate] = useState(false)

  // Modal xem chi tiết
  const [detailTask, setDetailTask] = useState<LeadershipTask | null>(null)

  // Modal báo cáo tiến độ / kết quả
  const [reportingTask, setReportingTask] = useState<LeadershipTask | null>(null)
  const [reportText, setReportText] = useState('')
  const [submittingReport, setSubmittingReport] = useState(false)

  // Modal phê duyệt & bút phê
  const [reviewingTask, setReviewingTask] = useState<LeadershipTask | null>(null)
  const [reviewStatus, setReviewStatus] = useState<LeadershipReviewStatus>('da_hoan_thanh')
  const [reviewNote, setReviewNote] = useState('')
  const [submittingReview, setSubmittingReview] = useState(false)

  // Tải danh sách đơn vị
  useEffect(() => {
    unitsApi
      .list({ active: true, limit: 100 })
      .then((res) => setUnits(res))
      .catch((err) => console.warn('Không tải được danh sách đơn vị:', err))
  }, [])

  // Tải danh sách chỉ đạo
  const fetchTasks = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await leadershipTasksApi.list({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        commander_role: selectedRole === 'all' ? undefined : selectedRole,
        target_branch: selectedBranch || undefined,
        urgency: selectedUrgency || undefined,
        status: selectedStatus || undefined,
      })
      setTasks(res.items)
      setTotal(res.total)
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Không thể tải danh sách chỉ đạo'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [page, selectedRole, selectedBranch, selectedUrgency, selectedStatus])

  // Thống kê nhanh
  const stats = useMemo(() => {
    const totalCount = total
    const urgentCount = tasks.filter((t) => t.urgency === 'hoa_toc' || t.urgency === 'khan').length
    const pendingReport = tasks.filter((t) => !t.report_content).length
    const completed = tasks.filter((t) => t.status === 'da_hoan_thanh').length
    return { totalCount, urgentCount, pendingReport, completed }
  }, [tasks, total])

  // Xử lý tạo chỉ đạo
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createTitle.trim() || !createContent.trim()) {
      toast?.error('Vui lòng nhập đầy đủ Tiêu đề và Nội dung chỉ đạo.')
      return
    }

    setSubmittingCreate(true)
    try {
      const payload: LeadershipTaskCreatePayload = {
        commander_role: createRole,
        title: createTitle.trim(),
        content: createContent.trim(),
        target_branch: createBranch,
        assigned_unit_id: createUnitId === '' ? null : Number(createUnitId),
        urgency: createUrgency,
        deadline: createDeadline || null,
      }
      await leadershipTasksApi.create(payload)
      toast?.success('Đã ban hành Chỉ đạo tác chiến của Ban Chỉ huy thành công!')
      setShowCreateModal(false)
      setCreateTitle('')
      setCreateContent('')
      setCreateDeadline('')
      setPage(1)
      fetchTasks()
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Ban hành chỉ đạo thất bại'
      toast?.error(msg)
    } finally {
      setSubmittingCreate(false)
    }
  }

  // Xử lý gửi báo cáo
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reportingTask) return
    if (!reportText.trim()) {
      toast?.error('Vui lòng nhập nội dung báo cáo kết quả thực hiện.')
      return
    }

    if (reportText.trim().length < 5) {
      toast?.error('Nội dung báo cáo phải có tối thiểu 5 ký tự.')
      return
    }

    setSubmittingReport(true)
    try {
      await leadershipTasksApi.report(reportingTask.id, { report_content: reportText.trim() })
      toast?.success('Đã nộp báo cáo kết quả lên Ban Chỉ huy Lữ đoàn thành công!')
      setReportingTask(null)
      setReportText('')
      fetchTasks()
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Nộp báo cáo thất bại'
      toast?.error(msg)
    } finally {
      setSubmittingReport(false)
    }
  }

  // Xử lý phê duyệt & bút phê
  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reviewingTask) return
    if (reviewNote.trim().length < 2) {
      toast?.error('Vui lòng nhập ý kiến bút phê (tối thiểu 2 ký tự).')
      return
    }

    setSubmittingReview(true)
    try {
      await leadershipTasksApi.review(reviewingTask.id, {
        status: reviewStatus,
        review_note: reviewNote.trim(),
      })
      toast?.success('Bút phê & đánh giá kết quả chỉ đạo đã được cập nhật thành công!')
      setReviewingTask(null)
      setReviewNote('')
      fetchTasks()
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Bút phê đánh giá thất bại'
      toast?.error(msg)
    } finally {
      setSubmittingReview(false)
    }
  }

  const pageCount = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="leadership-workdesk space-y-6">
      {/* Banner Bàn làm việc Chỉ đạo */}
      <div className="rounded-xl border border-amber-500/40 bg-gradient-to-r from-red-950 via-slate-900 to-amber-950/70 p-6 shadow-xl relative overflow-hidden">
        <div className="absolute -right-8 -top-8 w-40 h-40 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                <Icon name="star" size={12} /> BÀN LÀM VIỆC TÁC CHIẾN BCH
              </span>
              <span className="text-xs text-slate-400 font-mono">v8.0.0 INTRA-SEC</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-wide">
              Chỉ đạo Nghiệp vụ &amp; Mệnh lệnh của Ban Chỉ huy Lữ đoàn
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              Lữ trưởng chỉ đạo chung mọi mặt về <strong>bên Chính quyền</strong> (Quân sự · Tác chiến · SSCĐ); 
              Chính uỷ chỉ đạo chung mọi mặt <strong>bên Đảng</strong> (Đảng uỷ · CTĐ-CTCT · Cán bộ); 
              các Lữ phó chỉ đạo theo <strong>chuyên ngành</strong> (Tham mưu, Hậu cần – Kỹ thuật); 
              Phó Chính uỷ điều hành các <strong>tổ chức quần chúng &amp; tổ chức Đảng</strong>. 
              Đơn vị thực hiện: Các Phòng ban, Tiểu đoàn 1, Tiểu đoàn 2, Đại đội 5, Trung tâm 2, Trạm Kiểm soát.
            </p>
          </div>

          {isBCHCommander && (
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 active:bg-red-700 text-white font-semibold text-sm shadow-lg shadow-red-900/30 transition-all cursor-pointer whitespace-nowrap border border-red-400/40"
            >
              <Icon name="plus" size={15} /> Ban hành Chỉ đạo / Mệnh lệnh
            </button>
          )}
        </div>

        {/* 4 Thẻ tóm tắt số liệu */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-5 border-t border-slate-700/60">
          <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/40">
            <span className="text-xs text-slate-400">Tổng chỉ đạo ghi nhận</span>
            <div className="text-xl font-bold text-white mt-0.5">{stats.totalCount}</div>
          </div>
          <div className="bg-slate-900/60 rounded-lg p-3 border border-red-500/30">
            <span className="text-xs text-red-300 flex items-center gap-1">
              <Icon name="star" size={11} /> Hoả tốc &amp; Khẩn
            </span>
            <div className="text-xl font-bold text-red-400 mt-0.5">{stats.urgentCount}</div>
          </div>
          <div className="bg-slate-900/60 rounded-lg p-3 border border-amber-500/30">
            <span className="text-xs text-amber-300 flex items-center gap-1">
              <Icon name="clock" size={11} /> Đang triển khai / Chờ báo cáo
            </span>
            <div className="text-xl font-bold text-amber-400 mt-0.5">{stats.pendingReport}</div>
          </div>
          <div className="bg-slate-900/60 rounded-lg p-3 border border-emerald-500/30">
            <span className="text-xs text-emerald-300 flex items-center gap-1">
              <Icon name="check" size={11} /> Đã hoàn thành
            </span>
            <div className="text-xl font-bold text-emerald-400 mt-0.5">{stats.completed}</div>
          </div>
        </div>
      </div>

      {/* Thanh chọn 5 Chức danh Ban Chỉ huy */}
      <div className="bg-slate-900/80 rounded-xl p-3 border border-slate-800 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-1 flex items-center gap-1.5">
          <Icon name="users" size={13} /> Chọn Bàn làm việc theo Chức trách Ban Chỉ huy:
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-2">
          <button
            type="button"
            onClick={() => {
              setSelectedRole('all')
              setPage(1)
            }}
            className={`p-2.5 rounded-lg text-left transition-all border cursor-pointer ${
              selectedRole === 'all'
                ? 'bg-amber-500/20 border-amber-400/50 text-amber-200 font-semibold'
                : 'bg-slate-800/60 border-slate-700/50 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="text-xs text-slate-400">Tất cả</div>
            <div className="text-sm font-semibold truncate">Toàn thể Ban Chỉ huy</div>
          </button>

          {(Object.keys(COMMANDER_ROLE_META) as CommanderRole[]).map((rKey) => {
            const meta = COMMANDER_ROLE_META[rKey]
            const active = selectedRole === rKey
            return (
              <button
                key={rKey}
                type="button"
                onClick={() => {
                  setSelectedRole(rKey)
                  setPage(1)
                }}
                className={`p-2.5 rounded-lg text-left transition-all border cursor-pointer ${
                  active
                    ? 'bg-red-900/40 border-amber-400/60 text-amber-200 font-semibold shadow-md'
                    : 'bg-slate-800/60 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center gap-1.5 text-xs text-amber-400/80 mb-0.5">
                  <Icon name={meta.icon} size={11} /> {meta.label}
                </div>
                <div className="text-[11px] text-slate-400 leading-tight line-clamp-2">{meta.desc}</div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Bộ lọc phụ: Ngành, Độ khẩn, Trạng thái */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          {/* Lọc Khối ngành */}
          <select
            value={selectedBranch}
            onChange={(e) => {
              setSelectedBranch(e.target.value as CommanderBranch | '')
              setPage(1)
            }}
            className="bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-amber-400 focus:outline-none"
          >
            <option value="">Tất cả Khối/Ngành</option>
            <option value="tham_muu">Khối Tham mưu</option>
            <option value="chinh_tri">Khối Chính trị</option>
            <option value="hau_can_ky_thuat">Khối Hậu cần – Kỹ thuật</option>
          </select>

          {/* Lọc Độ khẩn */}
          <select
            value={selectedUrgency}
            onChange={(e) => {
              setSelectedUrgency(e.target.value as TaskUrgency | '')
              setPage(1)
            }}
            className="bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-amber-400 focus:outline-none"
          >
            <option value="">Tất cả Độ khẩn</option>
            <option value="hoa_toc">Hoả tốc</option>
            <option value="khan">Khẩn</option>
            <option value="thuong">Thường</option>
          </select>

          {/* Lọc Trạng thái */}
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value as TaskStatus | '')
              setPage(1)
            }}
            className="bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-amber-400 focus:outline-none"
          >
            <option value="">Tất cả Trạng thái</option>
            <option value="dang_thuc_hien">Đang triển khai</option>
            <option value="da_bao_cao">Đã báo cáo, chờ bút phê</option>
            <option value="da_hoan_thanh">Đã hoàn thành</option>
            <option value="can_bo_sung">Cần bổ sung</option>
          </select>
        </div>

        <button
          type="button"
          onClick={() => {
            setSelectedRole('all')
            setSelectedBranch('')
            setSelectedUrgency('')
            setSelectedStatus('')
            setPage(1)
          }}
          className="text-xs text-slate-400 hover:text-amber-300 underline cursor-pointer"
        >
          Đặt lại bộ lọc
        </button>
      </div>

      {/* Danh sách Chỉ đạo */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <Icon name="layers" size={24} className="animate-spin mb-2 mx-auto text-amber-400" />
          <div>Đang tải danh sách chỉ đạo của Ban Chỉ huy Lữ đoàn...</div>
        </div>
      ) : error ? (
        <div className="p-6 rounded-xl border border-red-500/40 bg-red-950/20 text-red-300 text-center">
          <Icon name="alert-triangle" size={20} className="mb-2 mx-auto text-red-400" />
          <div>{error}</div>
          <button
            type="button"
            onClick={fetchTasks}
            className="mt-3 px-3 py-1.5 rounded bg-red-800 text-white text-xs cursor-pointer"
          >
            Thử lại
          </button>
        </div>
      ) : tasks.length === 0 ? (
        <EmptyState
          icon="bullhorn"
          message="Chưa có chỉ đạo hoặc mệnh lệnh nào phù hợp trong danh mục này."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tasks.map((task) => {
            const roleMeta = COMMANDER_ROLE_META[task.commander_role] || {
              label: task.commander_role_label || task.commander_role,
              badgeClass: 'bg-slate-700 text-slate-200 border-slate-600',
              icon: 'shield',
            }
            const urgencyMeta = TASK_URGENCY_META[task.urgency] || {
              label: task.urgency_label || task.urgency,
              badgeClass: 'bg-slate-700 text-slate-200',
            }
            const statusMeta = TASK_STATUS_META[task.status] || {
              label: task.status_label || task.status,
              badgeClass: 'bg-slate-700 text-slate-200',
              icon: 'clock',
            }

            return (
              <div
                key={task.id}
                className="rounded-xl border border-slate-800 bg-slate-900/90 hover:border-slate-700 transition-all p-5 flex flex-col justify-between shadow-md relative"
              >
                {/* Header card */}
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${roleMeta.badgeClass}`}
                      >
                        <Icon name={roleMeta.icon} size={10} /> {roleMeta.label}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold border ${urgencyMeta.badgeClass}`}
                      >
                        {urgencyMeta.label}
                      </span>
                    </div>

                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusMeta.badgeClass}`}
                    >
                      <Icon name={statusMeta.icon} size={10} /> {statusMeta.label}
                    </span>
                  </div>

                  {/* Tiêu đề & Người ban hành */}
                  <h3 className="text-base font-bold text-white mb-1 leading-snug line-clamp-2">
                    {task.title}
                  </h3>
                  <div className="text-xs text-slate-400 mb-3 flex items-center gap-2">
                    <span>
                      Chỉ đạo bởi:{' '}
                      <strong className="text-amber-300 font-semibold">{task.commander_name}</strong>
                    </span>
                    <span>·</span>
                    <span>{fmtDateTime(task.created_at)}</span>
                  </div>

                  {/* Nội dung trích yếu */}
                  <p className="text-sm text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 mb-3 line-clamp-3 whitespace-pre-wrap">
                    {task.content}
                  </p>

                  {/* Thông tin đơn vị & hạn hoàn thành */}
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mb-4 bg-slate-800/40 p-2.5 rounded-lg">
                    <div>
                      <span className="text-slate-500 block">Đơn vị nhận giao việc:</span>
                      <strong className="text-slate-200">
                        {task.assigned_unit_name || 'Toàn Lữ đoàn / Các đơn vị'}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Hạn hoàn thành:</span>
                      <strong className={task.deadline ? 'text-amber-400' : 'text-slate-400'}>
                        {fmtDate(task.deadline)}
                      </strong>
                    </div>
                  </div>

                  {/* Báo cáo nếu có */}
                  {task.report_content && (
                    <div className="bg-emerald-950/20 border border-emerald-500/30 p-2.5 rounded-lg mb-3 text-xs">
                      <div className="flex items-center justify-between text-emerald-400 font-semibold mb-1">
                        <span className="flex items-center gap-1">
                          <Icon name="check" size={11} /> Đã có báo cáo từ{' '}
                          {task.reported_by_name || 'Đơn vị'}
                        </span>
                        <span className="text-slate-400 font-normal">
                          {fmtDateTime(task.reported_at)}
                        </span>
                      </div>
                      <p className="text-slate-300 line-clamp-2">{task.report_content}</p>
                    </div>
                  )}

                  {/* Bút phê chỉ đạo nếu có */}
                  {task.review_note && (
                    <div className="bg-amber-950/20 border border-amber-500/30 p-2.5 rounded-lg mb-3 text-xs">
                      <div className="flex items-center justify-between text-amber-400 font-semibold mb-1">
                        <span className="flex items-center gap-1">
                          <Icon name="clipboard" size={11} /> Bút phê kết luận của Chỉ huy
                        </span>
                        <span className="text-slate-400 font-normal">
                          {fmtDateTime(task.reviewed_at)}
                        </span>
                      </div>
                      <p className="text-slate-300 italic line-clamp-2">"{task.review_note}"</p>
                    </div>
                  )}
                </div>

                {/* Footer Action buttons */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 gap-2">
                  <button
                    type="button"
                    onClick={() => setDetailTask(task)}
                    className="text-xs text-slate-300 hover:text-white flex items-center gap-1 px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 transition cursor-pointer"
                  >
                    <Icon name="eye" size={12} /> Chi tiết
                  </button>

                  <div className="flex items-center gap-2">
                    {/* Nút báo cáo kết quả — role 5 (Người dùng) luôn bị chặn nộp (openapi v8.0.0 F2) */}
                    {role !== null && role <= 4 && (
                      <button
                        type="button"
                        onClick={() => {
                          setReportingTask(task)
                          setReportText(task.report_content || '')
                        }}
                        className="text-xs text-amber-300 hover:text-amber-200 flex items-center gap-1 px-2.5 py-1.5 rounded bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 transition cursor-pointer"
                      >
                        <Icon name="file" size={12} /> Báo cáo kết quả
                      </button>
                    )}

                    {/* Nút bút phê duyệt của Chỉ huy */}
                    {isBCHCommander && (
                      <button
                        type="button"
                        onClick={() => {
                          setReviewingTask(task)
                          setReviewStatus('da_hoan_thanh')
                          setReviewNote(task.review_note || '')
                        }}
                        className="text-xs text-emerald-300 hover:text-emerald-200 flex items-center gap-1 px-2.5 py-1.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 transition cursor-pointer"
                      >
                        <Icon name="clipboard" size={12} /> Bút phê duyệt
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Phân trang */}
      {total > pageSize && (
        <Pagination
          page={page - 1}
          pageCount={pageCount}
          total={total}
          pageSize={pageSize}
          onPage={(p) => setPage(p + 1)}
          onPageSize={() => {}}
          itemLabel="chỉ đạo"
        />
      )}

      {/* ========================================================================= */}
      {/* MODAL 1: BAN HÀNH CHỈ ĐẠO / MỆNH LỆNH (CHỈ HUY ROLE <= 2) */}
      {/* ========================================================================= */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-amber-500/40 rounded-2xl w-full max-w-2xl shadow-2xl p-6 relative">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white cursor-pointer"
            >
              <Icon name="x" size={18} />
            </button>

            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase mb-1">
              <Icon name="bullhorn" size={13} /> Lệnh Chỉ huy Lữ đoàn
            </div>
            <h3 className="text-xl font-bold text-white mb-4">
              Ban hành Chỉ đạo Tác chiến / Mệnh lệnh Công tác
            </h3>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Chọn chức vụ ban hành */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Chức trách Ban Chỉ huy <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={createRole}
                    onChange={(e) => setCreateRole(e.target.value as CommanderRole)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2 text-sm focus:border-amber-400 focus:outline-none"
                    required
                  >
                    <option value="lu_truong">Lữ đoàn trưởng (Chỉ đạo chung mọi mặt về Chính quyền)</option>
                    <option value="chinh_uy">Chính uỷ Lữ đoàn (Chỉ đạo chung mọi mặt bên Đảng)</option>
                    <option value="lu_pho_tmt">Phó Lữ trưởng kiêm TMT (Chỉ đạo chuyên ngành Tham mưu - Tác chiến - TTLL)</option>
                    <option value="lu_pho_hckt">Phó Lữ trưởng HC-KT (Chỉ đạo chuyên ngành Hậu cần - Kỹ thuật - VKTB)</option>
                    <option value="pho_chinh_uy">Phó Chính uỷ (Điều hành các Tổ chức Quần chúng &amp; Tổ chức Đảng)</option>
                  </select>
                </div>

                {/* Độ khẩn */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Độ khẩn <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={createUrgency}
                    onChange={(e) => setCreateUrgency(e.target.value as TaskUrgency)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2 text-sm focus:border-amber-400 focus:outline-none"
                    required
                  >
                    <option value="hoa_toc">Hoả tốc (Thực hiện ngay lập tức)</option>
                    <option value="khan">Khẩn</option>
                    <option value="thuong">Thường</option>
                  </select>
                </div>
              </div>

              {/* Tiêu đề */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Tiêu đề chỉ đạo / Nội dung tóm tắt <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={createTitle}
                  onChange={(e) => setCreateTitle(e.target.value)}
                  placeholder="Ví dụ: Kiểm tra phiên liên lạc mạng vô tuyến điện sóng ngắn cấp Lữ đoàn..."
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2.5 text-sm focus:border-amber-400 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Khối ngành hướng đến */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Khối/Ngành công tác
                  </label>
                  <select
                    value={createBranch}
                    onChange={(e) => setCreateBranch(e.target.value as CommanderBranch)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2 text-sm focus:border-amber-400 focus:outline-none"
                  >
                    {BRANCH_OPTIONS.map((bo) => (
                      <option key={bo.value} value={bo.value}>
                        {bo.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Đơn vị nhận giao việc cụ thể */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Giao đích danh Đơn vị (tuỳ chọn)
                  </label>
                  <select
                    value={createUnitId}
                    onChange={(e) => setCreateUnitId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2 text-sm focus:border-amber-400 focus:outline-none"
                  >
                    <option value="">Toàn Lữ đoàn / Không chỉ định đơn vị</option>
                    {units.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Hạn hoàn thành */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Hạn hoàn thành (Deadline)
                </label>
                <input
                  type="date"
                  value={createDeadline}
                  onChange={(e) => setCreateDeadline(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2 text-sm focus:border-amber-400 focus:outline-none"
                />
              </div>

              {/* Nội dung chỉ đạo chi tiết */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Nội dung Mệnh lệnh / Yêu cầu chi tiết <span className="text-red-400">*</span>
                </label>
                <textarea
                  rows={4}
                  value={createContent}
                  onChange={(e) => setCreateContent(e.target.value)}
                  placeholder="Ghi rõ yêu cầu cụ thể, mốc thời gian hoàn thành và chế độ báo cáo..."
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2.5 text-sm focus:border-amber-400 focus:outline-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm cursor-pointer"
                >
                  Huỷ bỏ
                </button>
                <button
                  type="submit"
                  disabled={submittingCreate}
                  className="px-5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold text-sm shadow-md cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Icon name="send" size={14} /> Ký &amp; Ban hành Mệnh lệnh
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: BÁO CÁO KẾT QUẢ THỰC HIỆN CỦA ĐƠN VỊ */}
      {/* ========================================================================= */}
      {reportingTask && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-amber-500/40 rounded-2xl w-full max-w-xl shadow-2xl p-6 relative">
            <button
              type="button"
              onClick={() => setReportingTask(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white cursor-pointer"
            >
              <Icon name="x" size={18} />
            </button>

            <div className="text-xs text-amber-400 font-semibold uppercase mb-1 flex items-center gap-1.5">
              <Icon name="file" size={13} /> Báo cáo thực hiện chỉ đạo
            </div>
            <h3 className="text-lg font-bold text-white mb-2">{reportingTask.title}</h3>
            <p className="text-xs text-slate-400 mb-4">
              Chỉ huy ban hành: <strong>{reportingTask.commander_name}</strong> (
              {reportingTask.commander_role_label})
            </p>

            <form onSubmit={handleReportSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Nội dung báo cáo kết quả / tiến độ <span className="text-red-400">*</span>
                </label>
                <textarea
                  rows={6}
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  placeholder="Ghi rõ tiến độ, số lượng khí tài đã kiểm tra, quân số tham gia, kết quả xử lý hoặc các vướng mắc nếu có..."
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-3 text-sm focus:border-amber-400 focus:outline-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setReportingTask(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm cursor-pointer"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={submittingReport}
                  className="px-5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-sm shadow-md cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Icon name="send" size={14} /> Nộp Báo cáo lên Ban Chỉ huy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: BÚT PHÊ & ĐÁNH GIÁ CỦA CHỈ HUY (ROLE <= 2) */}
      {/* ========================================================================= */}
      {reviewingTask && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-emerald-500/40 rounded-2xl w-full max-w-xl shadow-2xl p-6 relative">
            <button
              type="button"
              onClick={() => setReviewingTask(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white cursor-pointer"
            >
              <Icon name="x" size={18} />
            </button>

            <div className="text-xs text-emerald-400 font-semibold uppercase mb-1 flex items-center gap-1.5">
              <Icon name="clipboard" size={13} /> Thẩm quyền Ban Chỉ huy
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Đánh giá &amp; Bút phê Kết luận</h3>
            <p className="text-xs text-slate-300 mb-4 bg-slate-800/60 p-2 rounded">
              Nhiệm vụ: <strong>{reviewingTask.title}</strong>
            </p>

            {reviewingTask.report_content && (
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs mb-4">
                <span className="text-slate-400 block mb-1">
                  Báo cáo của {reviewingTask.reported_by_name} ({fmtDateTime(reviewingTask.reported_at)}):
                </span>
                <p className="text-slate-200">{reviewingTask.report_content}</p>
              </div>
            )}

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Kết luận trạng thái nhiệm vụ <span className="text-red-400">*</span>
                </label>
                {/* openapi v8.0.0: bút phê chỉ có 2 kết luận — da_hoan_thanh | can_bo_sung */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setReviewStatus('da_hoan_thanh')}
                    className={`p-2 rounded-lg text-xs font-semibold border text-center transition cursor-pointer ${
                      reviewStatus === 'da_hoan_thanh'
                        ? 'bg-emerald-600/30 border-emerald-400 text-emerald-300'
                        : 'bg-slate-800 border-slate-700 text-slate-400'
                    }`}
                  >
                    Hoàn thành
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewStatus('can_bo_sung')}
                    className={`p-2 rounded-lg text-xs font-semibold border text-center transition cursor-pointer ${
                      reviewStatus === 'can_bo_sung'
                        ? 'bg-rose-600/30 border-rose-400 text-rose-300'
                        : 'bg-slate-800 border-slate-700 text-slate-400'
                    }`}
                  >
                    Cần bổ sung
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Bút phê / Ý kiến chỉ đạo kết luận của Chỉ huy{' '}
                  <span className="text-red-400">*</span>
                </label>
                <textarea
                  rows={4}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  required
                  minLength={2}
                  placeholder="Ví dụ: Đã kiểm tra đạt yêu cầu; Biểu dương tinh thần SSCĐ của đơn vị..."
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-3 text-sm focus:border-emerald-400 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setReviewingTask(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm cursor-pointer"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-md cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Icon name="check" size={14} /> Ký &amp; Lưu bút phê
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 4: XEM CHI TIẾT TOÀN BỘ CHỈ ĐẠO & DÒNG THỜI GIAN */}
      {/* ========================================================================= */}
      {detailTask && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl shadow-2xl p-6 relative">
            <button
              type="button"
              onClick={() => setDetailTask(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white cursor-pointer"
            >
              <Icon name="x" size={18} />
            </button>

            <div className="flex items-center gap-2 mb-2">
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                  TASK_URGENCY_META[detailTask.urgency]?.badgeClass
                }`}
              >
                {TASK_URGENCY_META[detailTask.urgency]?.label}
              </span>
              <span className="text-xs text-slate-400 font-mono">ID: #{detailTask.id}</span>
            </div>

            <h3 className="text-xl font-bold text-white mb-2">{detailTask.title}</h3>
            <div className="text-xs text-slate-400 mb-4">
              Người chỉ đạo: <strong className="text-amber-300">{detailTask.commander_name}</strong>{' '}
              ({detailTask.commander_role_label}) · Ban hành lúc {fmtDateTime(detailTask.created_at)}
            </div>

            <div className="space-y-4">
              <div>
                <span className="text-xs text-slate-500 font-semibold block uppercase mb-1">
                  Nội dung Mệnh lệnh / Yêu cầu:
                </span>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-sm text-slate-200 whitespace-pre-wrap">
                  {detailTask.content}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs bg-slate-800/40 p-3 rounded-lg">
                <div>
                  <span className="text-slate-500 block">Khối ngành:</span>
                  <strong className="text-slate-200">
                    {detailTask.target_branch_label || detailTask.target_branch}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Đơn vị nhận giao việc:</span>
                  <strong className="text-slate-200">
                    {detailTask.assigned_unit_name || 'Toàn Lữ đoàn'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Hạn hoàn thành:</span>
                  <strong className="text-amber-400">{fmtDate(detailTask.deadline)}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Trạng thái hiện tại:</span>
                  <strong className="text-slate-200">{detailTask.status_label}</strong>
                </div>
              </div>

              {detailTask.report_content && (
                <div>
                  <span className="text-xs text-emerald-400 font-semibold block uppercase mb-1 flex items-center gap-1">
                    <Icon name="check" size={11} /> Báo cáo thực hiện từ đơn vị (
                    {detailTask.reported_by_name} lúc {fmtDateTime(detailTask.reported_at)}):
                  </span>
                  <div className="bg-emerald-950/20 border border-emerald-500/30 p-3 rounded-lg text-xs text-slate-200 whitespace-pre-wrap">
                    {detailTask.report_content}
                  </div>
                </div>
              )}

              {detailTask.review_note && (
                <div>
                  <span className="text-xs text-amber-400 font-semibold block uppercase mb-1 flex items-center gap-1">
                    <Icon name="clipboard" size={11} /> Bút phê kết luận của Ban Chỉ huy (lúc{' '}
                    {fmtDateTime(detailTask.reviewed_at)}):
                  </span>
                  <div className="bg-amber-950/20 border border-amber-500/30 p-3 rounded-lg text-xs text-amber-200 italic whitespace-pre-wrap">
                    "{detailTask.review_note}"
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end pt-5 mt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setDetailTask(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs cursor-pointer"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
