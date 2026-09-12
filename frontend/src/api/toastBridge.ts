/**
 * Cầu nối toast cho tầng không phải React (apiClient).
 * <ToastProvider> đăng ký handler khi mount; các module thuần (client.ts) gọi
 * `emitToast(...)` để hiện thông báo mà không cần hook React.
 */
export type ToastKind = 'success' | 'error' | 'info'

type ToastHandler = (kind: ToastKind, message: string) => void

let handler: ToastHandler | null = null

export function setToastHandler(fn: ToastHandler | null): void {
  handler = fn
}

export function emitToast(kind: ToastKind, message: string): void {
  handler?.(kind, message)
}
