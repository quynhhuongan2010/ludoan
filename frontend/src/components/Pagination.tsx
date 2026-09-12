interface PaginationProps {
  /** Trang hien tai (0-based). */
  page: number
  /** Tong so trang (>= 1). */
  pageCount: number
  /** Tong so ban ghi (sau khi loc). */
  total: number
  pageSize: number
  onPage: (p: number) => void
  onPageSize: (n: number) => void
  pageSizeOptions?: number[]
  /** Ten don vi ban ghi, vd "cuộc họp". */
  itemLabel?: string
}

const WINDOW = 5

export function Pagination({
  page,
  pageCount,
  total,
  pageSize,
  onPage,
  onPageSize,
  pageSizeOptions = [5, 10, 20],
  itemLabel = 'bản ghi',
}: PaginationProps) {
  const start = total === 0 ? 0 : page * pageSize + 1
  const end = Math.min(total, (page + 1) * pageSize)

  let from = Math.max(0, page - Math.floor(WINDOW / 2))
  const to = Math.min(pageCount, from + WINDOW)
  from = Math.max(0, to - WINDOW)
  const nums: number[] = []
  for (let i = from; i < to; i++) nums.push(i)

  const atFirst = page <= 0
  const atLast = page >= pageCount - 1

  return (
    <div className="pagination-bar">
      <span className="pagination-info">
        Hiển thị <strong>{start}</strong> – <strong>{end}</strong> trên tổng số{' '}
        <strong>{total}</strong> {itemLabel}
      </span>

      <div className="pagination-controls">
        <label className="pagination-size">
          Hiển thị
          <select value={pageSize} onChange={(e) => onPageSize(Number(e.target.value))}>
            {pageSizeOptions.map((n) => (
              <option key={n} value={n}>
                {n} / trang
              </option>
            ))}
          </select>
        </label>

        <div className="pagination-pages">
          <button
            type="button"
            className="pg-btn"
            title="Trang đầu"
            disabled={atFirst}
            onClick={() => onPage(0)}
          >
            «
          </button>
          <button
            type="button"
            className="pg-btn"
            title="Trang trước"
            disabled={atFirst}
            onClick={() => onPage(page - 1)}
          >
            ‹
          </button>
          {nums.map((n) => (
            <button
              key={n}
              type="button"
              className={n === page ? 'page-num active' : 'page-num'}
              aria-current={n === page ? 'page' : undefined}
              onClick={() => onPage(n)}
            >
              {n + 1}
            </button>
          ))}
          <button
            type="button"
            className="pg-btn"
            title="Trang tiếp"
            disabled={atLast}
            onClick={() => onPage(page + 1)}
          >
            ›
          </button>
          <button
            type="button"
            className="pg-btn"
            title="Trang cuối"
            disabled={atLast}
            onClick={() => onPage(pageCount - 1)}
          >
            »
          </button>
        </div>
      </div>
    </div>
  )
}
