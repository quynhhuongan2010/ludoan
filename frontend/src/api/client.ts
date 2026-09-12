import { emitToast } from './toastBridge'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const TOKEN_STORAGE_KEY = 'quynh_web.access_token'
const ROLE_STORAGE_KEY = 'quynh_web.role'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** Tuỳ chọn toast cho một lời gọi ghi dữ liệu (POST/PUT/PATCH/DELETE...). */
export interface MutationMeta {
  /** Không hiện toast "thành công" (toast lỗi vẫn hiện). */
  silent?: boolean
  /** Câu thông báo thành công tuỳ biến thay cho câu mặc định theo method. */
  successMessage?: string
}

const DEFAULT_SUCCESS: Record<string, string> = {
  POST: 'Thao tác thành công',
  PUT: 'Cập nhật thành công',
  PATCH: 'Cập nhật thành công',
  DELETE: 'Đã xoá thành công',
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(ROLE_STORAGE_KEY)
}

/** Vai trò (số nguyên 0..5) trả về từ POST /users/login, lưu để dùng lại. */
export function getStoredRole(): number | null {
  const raw = localStorage.getItem(ROLE_STORAGE_KEY)
  if (raw === null || raw === '') return null
  const value = Number(raw)
  return Number.isInteger(value) ? value : null
}

export function setStoredRole(role: number): void {
  localStorage.setItem(ROLE_STORAGE_KEY, String(role))
}

/** Câu lỗi tiếng Việt mặc định theo mã HTTP khi máy chủ không kèm `detail`. */
const STATUS_MESSAGE_VI: Record<number, string> = {
  400: 'Yêu cầu không hợp lệ',
  401: 'Phiên đăng nhập đã hết hạn — vui lòng đăng nhập lại',
  403: 'Bạn không có quyền thực hiện thao tác này',
  404: 'Không tìm thấy dữ liệu',
  409: 'Thao tác bị xung đột với dữ liệu hiện có',
  413: 'Tệp tải lên vượt quá dung lượng cho phép',
  422: 'Dữ liệu nhập chưa hợp lệ',
  500: 'Máy chủ gặp lỗi, vui lòng thử lại sau',
  502: 'Máy chủ tạm thời không phản hồi',
  503: 'Máy chủ đang bảo trì, vui lòng thử lại sau',
}

/**
 * Chuẩn hoá `detail` của FastAPI thành 1 câu tiếng Việt.
 * - Chuỗi (HTTPException của mình — đã là tiếng Việt): dùng nguyên văn.
 * - Mảng lỗi 422 của Pydantic (msg tiếng Anh): thay bằng câu tiếng Việt gọn.
 * - Không có detail: tra câu mặc định theo mã HTTP.
 */
function extractErrorMessage(detail: unknown, status: number): string {
  if (typeof detail === 'string' && detail.trim() !== '') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const fields = (detail as Array<{ loc?: unknown[] }>)
      .map((item) => (Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : ''))
      .filter((name): name is string => typeof name === 'string' && name !== '' && name !== 'body')
    return fields.length > 0
      ? `Dữ liệu nhập chưa hợp lệ ở: ${[...new Set(fields)].join(', ')}`
      : 'Dữ liệu nhập chưa hợp lệ'
  }
  return STATUS_MESSAGE_VI[status] ?? 'Đã xảy ra lỗi, vui lòng thử lại'
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  meta?: MutationMeta,
): Promise<T> {
  const token = getToken()
  const isFormData = options.body instanceof FormData
  const method = (options.method ?? 'GET').toUpperCase()
  const isMutation = method in DEFAULT_SUCCESS

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        // Voi FormData de trinh duyet tu set Content-Type kem boundary
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    if (isMutation) emitToast('error', 'Không kết nối được máy chủ')
    throw new ApiError(0, 'Không kết nối được máy chủ — kiểm tra lại đường truyền')
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message = extractErrorMessage(body?.detail, response.status)
    if (isMutation) emitToast('error', message)
    throw new ApiError(response.status, message)
  }

  if (isMutation && !meta?.silent) {
    emitToast('success', meta?.successMessage ?? DEFAULT_SUCCESS[method])
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body: unknown, meta?: MutationMeta) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }, meta),
  put: <T>(path: string, body: unknown, meta?: MutationMeta) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }, meta),
  patch: <T>(path: string, body: unknown, meta?: MutationMeta) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }, meta),
  delete: <T>(path: string, meta?: MutationMeta) =>
    request<T>(path, { method: 'DELETE' }, meta),

  /** Gửi multipart/form-data (upload file). */
  postForm: <T>(path: string, form: FormData, meta?: MutationMeta) =>
    request<T>(path, { method: 'POST', body: form }, meta),
  putForm: <T>(path: string, form: FormData, meta?: MutationMeta) =>
    request<T>(path, { method: 'PUT', body: form }, meta),
}
