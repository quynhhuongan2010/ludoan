import { useEffect, useRef } from 'react'

/**
 * Tu dong luu ban nhap (autosave draft) vao localStorage cho cac form soan
 * thao dai (chi thi, bao cao, tin nhan trong kenh chi dao/chi huy...) de
 * tranh mat noi dung khi tai lai trang, mat dien / mat mang LAN dot ngot
 * truoc khi kip gui.
 *
 * - Khi `key` thay doi (vd chuyen sang luong/nhiem vu khac) hoac lan dau
 *   mount: neu localStorage co ban nhap va gia tri hien tai dang "rong"
 *   (theo `isEmpty`) thi tu dong khoi phuc bang `setValue`.
 * - Moi khi `value` thay doi va khong rong: luu xuong localStorage (debounce
 *   nhe de khong ghi lien tuc theo tung ky tu go).
 * - Goi `clearDraft()` sau khi gui/luu thanh cong de xoa ban nhap, tranh boi
 *   lai noi dung cu vao lan soan thao sau.
 * - `key = null` -> tat hoan toan (vd khi chua chon luong/doi tuong nao).
 *
 * localStorage la rieng cua tung may trinh duyet, khong dong bo giua cac
 * nguoi dung / thiet bi va khong thay the viec luu vao CSDL qua API — day
 * chi la luoi an toan tam thoi cho nguoi dang go noi dung.
 */
export function useDraftAutosave<T>(
  key: string | null,
  value: T,
  setValue: (v: T) => void,
  options?: { isEmpty?: (v: T) => boolean; debounceMs?: number },
): { clearDraft: () => void } {
  const isEmpty = options?.isEmpty ?? defaultIsEmpty
  const debounceMs = options?.debounceMs ?? 400
  const storageKey = key ? `draft:${key}` : null
  const restoredKeyRef = useRef<string | null>(null)

  // Khoi phuc ban nhap khi key thay doi (hoac lan dau mount)
  useEffect(() => {
    if (!storageKey) return
    if (restoredKeyRef.current === storageKey) return
    restoredKeyRef.current = storageKey
    try {
      const raw = window.localStorage.getItem(storageKey)
      if (raw && isEmpty(value)) {
        setValue(JSON.parse(raw) as T)
      }
    } catch {
      // localStorage khong kha dung (che do rieng tu, trinh duyet chan...) -
      // bo qua, khong lam gian doan giao dien
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey])

  // Tu dong luu ban nhap khi noi dung thay doi
  useEffect(() => {
    if (!storageKey) return
    const timer = window.setTimeout(() => {
      try {
        if (isEmpty(value)) {
          window.localStorage.removeItem(storageKey)
        } else {
          window.localStorage.setItem(storageKey, JSON.stringify(value))
        }
      } catch {
        // het dung luong luu tru / bi chan - bo qua, khong lam gian doan nhap lieu
      }
    }, debounceMs)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey, value, debounceMs])

  function clearDraft() {
    if (!storageKey) return
    try {
      window.localStorage.removeItem(storageKey)
    } catch {
      // ignore
    }
  }

  return { clearDraft }
}

function defaultIsEmpty(value: unknown): boolean {
  if (value == null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') {
    return Object.values(value as Record<string, unknown>).every((v) => defaultIsEmpty(v))
  }
  return false
}
