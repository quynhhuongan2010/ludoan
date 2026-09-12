import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { Icon } from '../components/Icon'
import { setToastHandler, type ToastKind } from '../api/toastBridge'

interface Toast {
  id: number
  kind: ToastKind
  message: string
}

interface ToastApi {
  /** Toast xanh — báo tác vụ (POST/PUT...) đã thành công. */
  success: (message: string) => void
  /** Toast đỏ — báo lỗi khi gọi API thất bại. */
  error: (message: string) => void
  /** Toast trung tính. */
  info: (message: string) => void
  notify: (kind: ToastKind, message: string) => void
}

const AUTO_DISMISS_MS: Record<ToastKind, number> = {
  success: 3500,
  info: 4000,
  error: 6000,
}
const MAX_TOASTS = 4

const ToastContext = createContext<ToastApi | null>(null)

/**
 * Hàng thông báo nổi dùng chung. Bọc một lần quanh <App />.
 * `apiClient` tự bắn toast qua `toastBridge` cho mọi POST/PUT/PATCH/DELETE:
 * thành công → toast xanh, thất bại → toast đỏ (kèm `detail` từ backend).
 * Trang nào cần thông báo thủ công thì `const toast = useToast()`.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const seq = useRef(0)
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map())

  const dismiss = useCallback((id: number) => {
    setToasts((list) => list.filter((t) => t.id !== id))
    const handle = timers.current.get(id)
    if (handle) {
      clearTimeout(handle)
      timers.current.delete(id)
    }
  }, [])

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const text = (message ?? '').trim() || (kind === 'error' ? 'Đã xảy ra lỗi' : 'Thành công')
      const id = ++seq.current
      setToasts((list) => [...list, { id, kind, message: text }].slice(-MAX_TOASTS))
      const handle = setTimeout(() => dismiss(id), AUTO_DISMISS_MS[kind])
      timers.current.set(id, handle)
    },
    [dismiss],
  )

  useEffect(() => {
    setToastHandler(push)
    return () => setToastHandler(null)
  }, [push])

  useEffect(() => {
    const map = timers.current
    return () => {
      map.forEach((handle) => clearTimeout(handle))
      map.clear()
    }
  }, [])

  const api = useMemo<ToastApi>(
    () => ({
      success: (m) => push('success', m),
      error: (m) => push('error', m),
      info: (m) => push('info', m),
      notify: (k, m) => push(k, m),
    }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      {toasts.length > 0 ? (
        <div className="toast-stack" role="region" aria-live="polite" aria-label="Thông báo">
          {toasts.map((t) => (
            <div key={t.id} className={`toast toast-${t.kind}`} role="status">
              <span className="toast-icon">
                <Icon name={t.kind === 'success' ? 'check' : t.kind === 'error' ? 'alert-triangle' : 'bullhorn'} size={18} />
              </span>
              <p className="toast-msg">{t.message}</p>
              <button
                type="button"
                className="toast-close"
                aria-label="Đóng thông báo"
                onClick={() => dismiss(t.id)}
              >
                <Icon name="x" size={14} />
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast phải nằm trong <ToastProvider>')
  return ctx
}
