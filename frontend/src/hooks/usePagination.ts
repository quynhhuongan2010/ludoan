import { useEffect, useMemo, useState } from 'react'

/**
 * Phan trang phia client cho mot mang da tai ve (giong cach DanhBaPage /
 * KenhChiHuyPage dang lam) - tranh render hang loat the/dong khi co nhieu ban ghi.
 *
 * `resetKey` doi -> ve trang dau (vd khi doi bo loc danh muc / tu khoa).
 */
export function usePagination<T>(items: T[], initialSize = 10, resetKey?: unknown) {
  const [pageIndex, setPageIndex] = useState(0)
  const [pageSize, setPageSize] = useState(initialSize)

  useEffect(() => {
    setPageIndex(0)
  }, [resetKey, pageSize])

  const total = items.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const page = Math.min(pageIndex, pageCount - 1)

  const pageItems = useMemo(
    () => items.slice(page * pageSize, page * pageSize + pageSize),
    [items, page, pageSize],
  )

  return {
    page,
    pageSize,
    pageCount,
    total,
    pageItems,
    setPageIndex,
    setPageSize,
    /** true khi so ban ghi vuot 1 trang -> nen hien thanh phan trang. */
    showPagination: total > pageSize,
  }
}
