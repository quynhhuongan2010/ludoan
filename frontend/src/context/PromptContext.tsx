import {
  createContext,
  useCallback,
  useContext,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react'
import { Icon } from '../components/Icon'
import { Modal } from '../components/Modal'

export interface PromptField {
  /** Khoá của trường trong object kết quả. */
  name: string
  /** Nhãn hiển thị phía trên ô nhập. */
  label: ReactNode
  type?: 'text' | 'password'
  defaultValue?: string
  placeholder?: string
  maxLength?: number
  /** Mặc định true — bỏ trắng sẽ chặn nút xác nhận. */
  required?: boolean
}

interface PromptOptions {
  title: string
  /** Dòng mô tả phía trên các ô nhập (tuỳ chọn). */
  message?: ReactNode
  fields: PromptField[]
  /** Nhãn nút xác nhận. Mặc định "Xác nhận". */
  confirmText?: string
  /** Nhãn nút huỷ. Mặc định "Huỷ". */
  cancelText?: string
}

interface AlertOptions {
  /** Mặc định "Thông báo". */
  title?: string
  message: ReactNode
  /** Nhãn nút đóng. Mặc định "Đã hiểu". */
  confirmText?: string
  tone?: 'success' | 'info' | 'danger'
}

type PromptFn = (options: PromptOptions) => Promise<Record<string, string> | null>
type AlertFn = (options: AlertOptions) => Promise<void>

const PromptContext = createContext<PromptFn | null>(null)
const AlertContext = createContext<AlertFn | null>(null)

/**
 * Cổng nhập liệu / thông báo dùng chung — thay cho `window.prompt` và
 * `window.alert`. Bọc một lần quanh <App /> (bên trong <ConfirmProvider>).
 *   const prompt = usePrompt()
 *   const res = await prompt({ title: '...', fields: [{ name: 'url', label: '...' }] })
 *   if (!res) return   // người dùng bấm Huỷ
 */
export function PromptProvider({ children }: { children: ReactNode }) {
  const [prompt, setPrompt] = useState<{
    options: PromptOptions
    resolve: (value: Record<string, string> | null) => void
  } | null>(null)
  const [alert, setAlert] = useState<{ options: AlertOptions; resolve: () => void } | null>(null)

  const promptFn = useCallback<PromptFn>(
    (options) => new Promise((resolve) => setPrompt({ options, resolve })),
    [],
  )
  const alertFn = useCallback<AlertFn>(
    (options) => new Promise((resolve) => setAlert({ options, resolve })),
    [],
  )

  function settlePrompt(value: Record<string, string> | null) {
    prompt?.resolve(value)
    setPrompt(null)
  }

  function settleAlert() {
    alert?.resolve()
    setAlert(null)
  }

  const alertTone = alert?.options.tone ?? 'info'

  return (
    <PromptContext.Provider value={promptFn}>
      <AlertContext.Provider value={alertFn}>
        {children}

        {prompt ? (
          <PromptDialog
            options={prompt.options}
            onCancel={() => settlePrompt(null)}
            onSubmit={(values) => settlePrompt(values)}
          />
        ) : null}

        {alert ? (
          <Modal title={alert.options.title ?? 'Thông báo'} onClose={settleAlert}>
            <div className="confirm-dialog">
              <span className={`confirm-icon${alertTone === 'danger' ? '' : ' is-default'}`}>
                <Icon name={alertTone === 'success' ? 'check' : 'alert-triangle'} size={22} />
              </span>
              <div className="confirm-message">{alert.options.message}</div>
            </div>
            <div className="confirm-actions">
              <button type="button" className="btn-edit" autoFocus onClick={settleAlert}>
                {alert.options.confirmText ?? 'Đã hiểu'}
              </button>
            </div>
          </Modal>
        ) : null}
      </AlertContext.Provider>
    </PromptContext.Provider>
  )
}

function PromptDialog({
  options,
  onCancel,
  onSubmit,
}: {
  options: PromptOptions
  onCancel: () => void
  onSubmit: (values: Record<string, string>) => void
}) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(options.fields.map((f) => [f.name, f.defaultValue ?? ''])),
  )
  const [touched, setTouched] = useState(false)

  const missing = options.fields.some(
    (f) => f.required !== false && (values[f.name] ?? '').trim() === '',
  )

  function submit(e: FormEvent) {
    e.preventDefault()
    if (missing) {
      setTouched(true)
      return
    }
    onSubmit(Object.fromEntries(options.fields.map((f) => [f.name, (values[f.name] ?? '').trim()])))
  }

  return (
    <Modal title={options.title} onClose={onCancel} closeOnOverlayClick={false}>
      <form onSubmit={submit} className="entity-form">
        {options.message ? <p className="state-note">{options.message}</p> : null}
        {options.fields.map((f, i) => (
          <label key={f.name}>
            {f.label}
            <input
              type={f.type ?? 'text'}
              autoFocus={i === 0}
              value={values[f.name] ?? ''}
              placeholder={f.placeholder}
              maxLength={f.maxLength}
              onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
            />
          </label>
        ))}
        {touched && missing ? (
          <p role="alert" className="form-note form-error">
            Vui lòng nhập đủ các trường bắt buộc.
          </p>
        ) : null}
        <div className="form-actions">
          <button type="submit" className="btn-submit" disabled={missing}>
            {options.confirmText ?? 'Xác nhận'}
          </button>
          <button type="button" className="btn-cancel" onClick={onCancel}>
            {options.cancelText ?? 'Huỷ'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export function usePrompt() {
  const ctx = useContext(PromptContext)
  if (!ctx) throw new Error('usePrompt phải nằm trong <PromptProvider>')
  return ctx
}

export function useAlert() {
  const ctx = useContext(AlertContext)
  if (!ctx) throw new Error('useAlert phải nằm trong <PromptProvider>')
  return ctx
}
