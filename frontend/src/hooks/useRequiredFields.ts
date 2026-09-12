import { useCallback, useState } from 'react'

/** Thông báo chuẩn cho trường bắt buộc bị bỏ trống. */
export const REQUIRED_MESSAGE = 'Trường này là bắt buộc'

function isBlank(value: unknown): boolean {
  if (value === undefined || value === null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  return false
}

/**
 * Quản lý lỗi "bắt buộc" cho một tập field trong form.
 *
 * - `mark(key, value)`   : gọi ở `onBlur` — đặt / xoá lỗi của riêng field đó.
 * - `validate(values)`   : gọi ở đầu `handleSubmit` — kiểm tất cả, trả `true` nếu hợp lệ.
 * - `errors[key]`        : chuỗi lỗi để truyền vào `<Field error={...}>`.
 * - `clear(key)`         : xoá lỗi 1 field (VD ngay khi người dùng gõ lại).
 * - `reset()`            : xoá toàn bộ lỗi.
 *
 * @param requiredKeys danh sách key bắt buộc (nên khai báo `as const`).
 */
export function useRequiredFields<K extends string>(requiredKeys: readonly K[]) {
  const [errors, setErrors] = useState<Partial<Record<K, string>>>({})

  const mark = useCallback((key: K, value: unknown) => {
    setErrors((prev) => {
      const blank = isBlank(value)
      if (blank === Boolean(prev[key])) return prev
      const next = { ...prev }
      if (blank) next[key] = REQUIRED_MESSAGE
      else delete next[key]
      return next
    })
  }, [])

  const clear = useCallback((key: K) => {
    setErrors((prev) => {
      if (!prev[key]) return prev
      const next = { ...prev }
      delete next[key]
      return next
    })
  }, [])

  const reset = useCallback(() => setErrors({}), [])

  const validate = useCallback(
    (values: Partial<Record<K, unknown>>) => {
      const next: Partial<Record<K, string>> = {}
      for (const key of requiredKeys) {
        if (isBlank(values[key])) next[key] = REQUIRED_MESSAGE
      }
      setErrors(next)
      return Object.keys(next).length === 0
    },
    [requiredKeys],
  )

  return { errors, mark, clear, reset, validate, setErrors }
}
