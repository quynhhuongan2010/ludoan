/**
 * Types cho Bàn làm việc Chỉ đạo Ban Chỉ huy Lữ đoàn.
 * Đồng bộ openapi v8.0.0 (2026-09-10) — chuẩn hoá mô hình trạng thái + siết enum.
 */

export type CommanderRole =
  | 'lu_truong'
  | 'chinh_uy'
  | 'lu_pho_tmt'
  | 'lu_pho_hckt'
  | 'pho_chinh_uy';

export type CommanderBranch =
  | 'tham_muu'
  | 'chinh_tri'
  | 'hau_can_ky_thuat'
  | 'toan_lu_doan';

export type TaskUrgency = 'thuong' | 'khan' | 'hoa_toc';

/**
 * Trạng thái chỉ đạo (v8.0.0 — 4 giá trị). Vòng đời:
 *   dang_thuc_hien → (đơn vị nộp báo cáo) da_bao_cao
 *   da_bao_cao → (BCH bút phê) da_hoan_thanh | can_bo_sung
 *   can_bo_sung → (nộp lại) da_bao_cao
 */
export type TaskStatus =
  | 'dang_thuc_hien'
  | 'da_bao_cao'
  | 'da_hoan_thanh'
  | 'can_bo_sung';

/** Kết luận bút phê — body POST /leadership-tasks/{id}/review (v8.0.0). */
export type LeadershipReviewStatus = 'da_hoan_thanh' | 'can_bo_sung';

export interface LeadershipTask {
  id: number;
  commander_role: CommanderRole;
  commander_role_label?: string;
  commander_id: number;
  commander_name: string;
  title: string;
  content: string;
  target_branch: CommanderBranch;
  target_branch_label?: string;
  assigned_unit_id?: number | null;
  assigned_unit_name?: string | null;
  urgency: TaskUrgency;
  urgency_label?: string;
  deadline?: string | null;
  status: TaskStatus;
  status_label?: string;
  report_content?: string | null;
  reported_by_id?: number | null;
  reported_by_name?: string | null;
  reported_at?: string | null;
  review_note?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface LeadershipTaskCreatePayload {
  commander_role: CommanderRole;
  title: string;
  content: string;
  target_branch?: CommanderBranch;
  assigned_unit_id?: number | null;
  urgency?: TaskUrgency;
  deadline?: string | null;
}

export interface LeadershipTaskReportPayload {
  /** Tối thiểu 5 ký tự (openapi v8.0.0). */
  report_content: string;
}

export interface LeadershipTaskReviewPayload {
  /** Mặc định backend: da_hoan_thanh (openapi v8.0.0). */
  status?: LeadershipReviewStatus;
  /** Bắt buộc, tối thiểu 2 ký tự (openapi v8.0.0). */
  review_note: string;
}

export interface LeadershipTaskListResponse {
  items: LeadershipTask[];
  total: number;
}

import type { IconName } from '../components/Icon'

export const COMMANDER_ROLE_META: Record<
  CommanderRole,
  { label: string; title: string; desc: string; icon: IconName; badgeClass: string }
> = {
  lu_truong: {
    label: 'Lữ đoàn trưởng',
    title: 'Đồng chí Lữ đoàn trưởng',
    desc: 'Chỉ đạo chung mọi mặt về Chính quyền (Quân sự · Tác chiến · Kế hoạch SSCĐ)',
    icon: 'star',
    badgeClass: 'bg-red-700 text-amber-300 border-amber-400/30',
  },
  chinh_uy: {
    label: 'Chính uỷ Lữ đoàn',
    title: 'Đồng chí Chính uỷ Lữ đoàn',
    desc: 'Chỉ đạo chung mọi mặt bên Đảng (Đảng uỷ · Cấp uỷ · CTĐ - CTCT · Cán bộ)',
    icon: 'shield',
    badgeClass: 'bg-rose-800 text-rose-100 border-rose-500/30',
  },
  lu_pho_tmt: {
    label: 'Phó Lữ trưởng kiêm TMT',
    title: 'Phó Lữ đoàn trưởng kiêm Tham mưu trưởng',
    desc: 'Chỉ đạo chuyên ngành Tham mưu · Tác chiến · Huấn luyện · TTLL SSCĐ (d1, d2)',
    icon: 'layers',
    badgeClass: 'bg-blue-800 text-blue-100 border-blue-400/30',
  },
  lu_pho_hckt: {
    label: 'Phó Lữ trưởng HC-KT',
    title: 'Phó Lữ đoàn trưởng Hậu cần – Kỹ thuật',
    desc: 'Chỉ đạo chuyên ngành Hậu cần – Kỹ thuật · VKTB · Khí tài TTLL · Xe máy (c5, Trạm)',
    icon: 'clipboard',
    badgeClass: 'bg-amber-800 text-amber-100 border-amber-400/30',
  },
  pho_chinh_uy: {
    label: 'Phó Chính uỷ',
    title: 'Đồng chí Phó Chính uỷ Lữ đoàn',
    desc: 'Điều hành các Tổ chức Quần chúng (Đoàn TN, Hội PN, Công đoàn) & Tổ chức Đảng',
    icon: 'users',
    badgeClass: 'bg-emerald-800 text-emerald-100 border-emerald-400/30',
  },
};

export const TASK_URGENCY_META: Record<
  TaskUrgency,
  { label: string; badgeClass: string }
> = {
  hoa_toc: {
    label: 'Hoả tốc',
    badgeClass: 'bg-red-600 text-white animate-pulse border-red-300',
  },
  khan: {
    label: 'Khẩn',
    badgeClass: 'bg-amber-500 text-slate-900 font-bold border-amber-300',
  },
  thuong: {
    label: 'Thường',
    badgeClass: 'bg-slate-700 text-slate-200 border-slate-600',
  },
};

export const TASK_STATUS_META: Record<
  TaskStatus,
  { label: string; badgeClass: string; icon: IconName }
> = {
  dang_thuc_hien: {
    label: 'Đang triển khai',
    badgeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    icon: 'layers',
  },
  da_bao_cao: {
    label: 'Đã báo cáo, chờ bút phê',
    badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    icon: 'file',
  },
  da_hoan_thanh: {
    label: 'Đã hoàn thành',
    badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    icon: 'check',
  },
  can_bo_sung: {
    label: 'Cần bổ sung',
    badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    icon: 'alert-triangle',
  },
};
