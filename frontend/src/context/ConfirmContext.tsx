import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import { Icon } from '../components/Icon'
import { Modal } from '../components/Modal'

interface ConfirmOptions {
  /** Tiêu đề hộp thoại. Mặc định: "Xác nhận xoá". */
  title?: string
  /** Nội dung cảnh báo (chuỗi hoặc JSX). */
  message: ReactNode
  /** Nhãn nút xác nhận. Mặc định: "Xoá". */
  confirmText?: string
  /** Nhãn nút huỷ. Mặc định: "Huỷ". */
  cancelText?: string
  /** 'danger' (đỏ, mặc định) cho xoá; 'default' (xanh) cho thao tác không phá huỷ. */
  tone?: 'danger' | 'default'
}

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>

const ConfirmContext = createContext<ConfirmFn | null>(null)

/**
 * Cổng xác nhận dùng chung: mọi thao tác xoá phải mở modal cảnh báo trước khi gọi API.
 * Bọc một lần quanh <App />; các trang gọi `const confirm = useConfirm()` rồi
 * `if (!(await confirm({ message: '...' }))) return`.
 */
export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [options, setOptions] = useState<ConfirmOptions | null>(null)
  const resolverRef = useRef<((value: boolean) => void) | null>(null)

  const confirm = useCallback<ConfirmFn>((opts) => {
    setOptions(opts)
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve
    })
  }, [])

  const settle = useCallback((value: boolean) => {
    resolverRef.current?.(value)
    resolverRef.current = null
    setOptions(null)
  }, [])

  const tone = options?.tone ?? 'danger'

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {options ? (
        <Modal title={options.title ?? 'Xác nhận xoá'} onClose={() => settle(false)}>
          <div className="confirm-dialog">
            <span className={`confirm-icon${tone === 'default' ? ' is-default' : ''}`}>
              <Icon name="alert-triangle" size={22} />
            </span>
            <div className="confirm-message">{options.message}</div>
          </div>
          <div className="confirm-actions">
            <button type="button" className="btn-cancel" onClick={() => settle(false)}>
              {options.cancelText ?? 'Huỷ'}
            </button>
            <button
              type="button"
              className={tone === 'default' ? 'btn-edit' : 'btn-delete'}
              autoFocus
              onClick={() => settle(true)}
            >
              {options.confirmText ?? 'Xoá'}
            </button>
          </div>
        </Modal>
      ) : null}
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext)
  if (!ctx) throw new Error('useConfirm phải nằm trong <ConfirmProvider>')
  return ctx
}
