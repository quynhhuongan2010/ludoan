import type { ReactNode, SyntheticEvent } from 'react'

/** Hình dạng tối thiểu của giá trị trả về từ `useRequiredFields` mà Field cần. */
interface RequiredFieldsLike<K extends string> {
  errors: Partial<Record<K, string>>
  mark: (name: K, value: unknown) => void
}

interface FieldProps<K extends string = string> {
  /** Nhãn hiển thị phía trên field. */
  label: ReactNode
  /** Trường bắt buộc → thêm dấu * đỏ vào nhãn. */
  required?: boolean
  /**
   * Hook `useRequiredFields` + `name` của field này. Khi truyền cặp này, Field tự:
   *  - lấy lỗi hiển thị từ `req.errors[name]`;
   *  - gọi `req.mark(name, value)` NGAY khi người dùng gõ/xoá (`onInput`) và khi rời field (`onBlur`)
   *    → xoá hết dữ liệu là báo "Trường này là bắt buộc" luôn.
   */
  req?: RequiredFieldsLike<K>
  name?: K
  /** Lỗi tự quản (dùng khi không qua `useRequiredFields`, VD field chọn tệp). Ghi đè `req.errors`. */
  error?: string | null
  /** Ghi chú phụ dưới field (không phải lỗi). */
  hint?: ReactNode
  /** Class thêm cho <label> bọc ngoài (VD "checkbox-row"). */
  className?: string
  children: ReactNode
}

function controlValue(target: EventTarget): string | null {
  if (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement
  ) {
    return target.value
  }
  return null
}

/**
 * Bọc một field trong form: nhãn (kèm dấu * nếu bắt buộc) + control + dòng lỗi.
 *
 * Dùng chung cho mọi form của cổng thông tin để chuẩn hoá:
 *  - trường bắt buộc luôn có dấu `*` đỏ ở nhãn;
 *  - lỗi "Trường này là bắt buộc" hiện ngay dưới field, cập nhật realtime khi gõ/xoá.
 */
export function Field<K extends string = string>({
  label,
  required,
  req,
  name,
  error,
  hint,
  className,
  children,
}: FieldProps<K>) {
  const shownError = error ?? (req && name != null ? req.errors[name] : undefined)

  const liveCheck =
    req && name != null
      ? (e: SyntheticEvent) => {
          const value = controlValue(e.target)
          if (value !== null) req.mark(name, value)
        }
      : undefined

  const classes = ['field']
  if (className) classes.push(className)
  if (shownError) classes.push('field--invalid')

  return (
    <label className={classes.join(' ')} onInput={liveCheck} onBlur={liveCheck}>
      <span className="field-label">
        {label}
        {required ? (
          <span className="req-mark" aria-hidden="true">
            {' '}
            *
          </span>
        ) : null}
      </span>
      {children}
      {hint ? <span className="field-hint">{hint}</span> : null}
      {shownError ? (
        <span className="field-error" role="alert">
          {shownError}
        </span>
      ) : null}
    </label>
  )
}
