import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { contactsApi } from '../api/contacts'
import { EmptyState } from '../components/EmptyState'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { Modal } from '../components/Modal'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { REQUIRED_MESSAGE } from '../hooks/useRequiredFields'
import type { Contact, ContactBook, ContactPage } from '../types/contact'

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function DanhBaPage() {
  const navigate = useNavigate()
  const { isCommander, isAdmin } = useAuth()
  const confirm = useConfirm()
  const canManage = isCommander || isAdmin

  const [books, setBooks] = useState<ContactBook[]>([])
  const [activeBookId, setActiveBookId] = useState<number | null>(null)
  const [page, setPage] = useState<ContactPage | null>(null)
  const [loadingBooks, setLoadingBooks] = useState(true)
  const [loadingRows, setLoadingRows] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [pageIndex, setPageIndex] = useState(0)
  const [pageSize, setPageSize] = useState(20)

  // Tim kiem + phan trang danh sach bo danh ba (client-side, so bo thuong nho).
  const [bookSearch, setBookSearch] = useState('')
  const [bookPageIndex, setBookPageIndex] = useState(0)
  const [bookPageSize, setBookPageSize] = useState(10)

  const [showImport, setShowImport] = useState(false)
  const [impFile, setImpFile] = useState<File | null>(null)
  const [impFileErr, setImpFileErr] = useState<string | null>(null)
  const [impName, setImpName] = useState('')
  const [impDesc, setImpDesc] = useState('')
  const [importing, setImporting] = useState(false)

  const [detailContact, setDetailContact] = useState<Contact | null>(null)

  const activeBook = useMemo(
    () => books.find((b) => b.id === activeBookId) ?? null,
    [books, activeBookId],
  )

  const filteredBooks = useMemo(() => {
    const kw = bookSearch.trim().toLowerCase()
    if (!kw) return books
    return books.filter(
      (b) => b.name.toLowerCase().includes(kw) || (b.description ?? '').toLowerCase().includes(kw),
    )
  }, [books, bookSearch])

  const bookTotal = filteredBooks.length
  const bookPageCount = Math.max(1, Math.ceil(bookTotal / bookPageSize))
  const bookPage = Math.min(bookPageIndex, bookPageCount - 1)
  const bookPageItems = filteredBooks.slice(
    bookPage * bookPageSize,
    bookPage * bookPageSize + bookPageSize,
  )

  useEffect(() => {
    setBookPageIndex(0)
  }, [bookSearch, bookPageSize])

  function loadBooks(selectId?: number) {
    setLoadingBooks(true)
    contactsApi
      .listBooks()
      .then((bs) => {
        setBooks(bs)
        if (selectId != null) setActiveBookId(selectId)
        else if (activeBookId == null && bs.length > 0) setActiveBookId(bs[0].id)
      })
      .catch((e: unknown) =>
        setError(e instanceof ApiError ? e.message : 'Không tải được danh sách danh bạ'),
      )
      .finally(() => setLoadingBooks(false))
  }

  useEffect(loadBooks, [])

  // Nap dong danh ba khi doi bo / tu khoa / trang / kich thuoc trang (debounce nhe).
  useEffect(() => {
    if (activeBookId == null) {
      setPage(null)
      return
    }
    setLoadingRows(true)
    const handle = setTimeout(() => {
      contactsApi
        .listContacts(activeBookId, {
          q: search.trim() || undefined,
          skip: pageIndex * pageSize,
          limit: pageSize,
        })
        .then(setPage)
        .catch((e: unknown) =>
          setError(e instanceof ApiError ? e.message : 'Không tra cứu được danh bạ'),
        )
        .finally(() => setLoadingRows(false))
    }, 250)
    return () => clearTimeout(handle)
  }, [activeBookId, search, pageIndex, pageSize])

  useEffect(() => {
    setPageIndex(0)
  }, [activeBookId, search, pageSize])

  async function handleImport(e: FormEvent) {
    e.preventDefault()
    if (!impFile) {
      setImpFileErr(REQUIRED_MESSAGE)
      return
    }
    setImporting(true)
    setError(null)
    try {
      const book = await contactsApi.importBook(impFile, impName.trim(), impDesc.trim())
      setShowImport(false)
      setImpFile(null)
      setImpName('')
      setImpDesc('')
      setSearch('')
      loadBooks(book.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không nhập được file danh bạ')
    } finally {
      setImporting(false)
    }
  }

  async function handleDeleteBook() {
    if (!activeBook) return
    const ok = await confirm({
      title: 'Xác nhận xoá bộ danh bạ',
      message: (
        <>
          Xoá bộ danh bạ <strong>{activeBook.name}</strong> ({activeBook.row_count} bản ghi)? Thao tác
          này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await contactsApi.removeBook(activeBook.id)
      setActiveBookId(null)
      loadBooks()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không xoá được bộ danh bạ')
    }
  }

  const total = page?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const columns = page?.columns ?? activeBook?.column_headers ?? []

  return (
    <section>
      <div className="crumb-bar">
        <button type="button" className="btn-back" onClick={() => navigate(-1)}>
          <Icon name="arrow-left" size={16} /> Quay lại
        </button>
        <nav className="breadcrumb" aria-label="breadcrumb">
          <span>Bản tin</span>
          <Icon name="chevron-right" size={12} />
          <span className="current">Danh bạ điện thoại</span>
        </nav>
      </div>

      <h1>Danh bạ điện thoại</h1>
      <p className="state-note">
        Nhập file danh bạ (Excel <code>.xlsx</code> hoặc <code>.csv</code>) của đơn vị / Bộ đội
        Biên phòng / toàn quân. Hệ thống giữ nguyên mọi cột của file và cho tra cứu nhanh trên
        tất cả các trường.
      </p>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      <div className="list-toolbar">
        <input
          type="search"
          placeholder="Tìm bộ danh bạ theo tên, mô tả..."
          value={bookSearch}
          onChange={(e) => setBookSearch(e.target.value)}
        />
        {canManage ? (
          <button type="button" className="btn-create" onClick={() => setShowImport(true)}>
            <Icon name="upload" size={16} /> Nhập danh bạ
          </button>
        ) : null}
      </div>

      {loadingBooks ? (
        <p className="state-note">Đang tải...</p>
      ) : books.length === 0 ? (
        <EmptyState icon="users" message="Chưa có bộ danh bạ nào được nhập" />
      ) : bookTotal === 0 ? (
        <EmptyState icon="search" message="Không có bộ danh bạ nào khớp từ khoá" />
      ) : (
        <>
          <div className="book-tabs">
            {bookPageItems.map((b) => (
              <button
                key={b.id}
                type="button"
                className={b.id === activeBookId ? 'book-tab active' : 'book-tab'}
                onClick={() => setActiveBookId(b.id)}
              >
                {b.name} <span className="book-tab-count">{b.row_count}</span>
              </button>
            ))}
          </div>
          {bookTotal > bookPageSize ? (
            <Pagination
              page={bookPage}
              pageCount={bookPageCount}
              total={bookTotal}
              pageSize={bookPageSize}
              onPage={setBookPageIndex}
              onPageSize={setBookPageSize}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              itemLabel="bộ danh bạ"
            />
          ) : null}
        </>
      )}

      {!activeBook ? (
        <EmptyState icon="users" message="Chọn hoặc nhập một bộ danh bạ để tra cứu" />
      ) : (
        <>
          <div className="block-section contact-book-meta">
            <div>
              <strong>{activeBook.name}</strong>
              {activeBook.description ? <p className="state-note">{activeBook.description}</p> : null}
              <p className="thread-meta">
                {activeBook.source_file_name ? `${activeBook.source_file_name} · ` : ''}
                {activeBook.row_count} bản ghi · nhập bởi {activeBook.created_by_full_name} ·{' '}
                {fmtDateTime(activeBook.created_at)}
              </p>
            </div>
            {canManage ? (
              <button type="button" className="btn-cancel" onClick={handleDeleteBook}>
                Xoá bộ danh bạ
              </button>
            ) : null}
          </div>

          <div className="list-toolbar">
            <input
              type="search"
              placeholder="Tra cứu theo tên, đơn vị, chức vụ, số điện thoại..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {loadingRows && !page ? (
            <p className="state-note">Đang tải...</p>
          ) : total === 0 ? (
            <EmptyState
              icon="search"
              message={
                search.trim()
                  ? 'Không tìm thấy bản ghi nào khớp từ khoá'
                  : 'Bộ danh bạ này chưa có bản ghi'
              }
            />
          ) : (
            <>
              <div className="table-scroll">
                <table className="users-table contact-table">
                  <thead>
                    <tr>
                      <th className="col-idx">#</th>
                      {columns.map((c) => (
                        <th key={c}>{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {page?.items.map((row) => (
                      <tr
                        key={row.id}
                        className="contact-row"
                        onClick={() => setDetailContact(row)}
                      >
                        <td className="col-idx">{row.row_index + 1}</td>
                        {columns.map((c) => (
                          <td key={c}>{row.extra[c] ?? ''}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={pageIndex}
                pageCount={pageCount}
                total={total}
                pageSize={pageSize}
                onPage={setPageIndex}
                onPageSize={setPageSize}
                pageSizeOptions={PAGE_SIZE_OPTIONS}
                itemLabel="bản ghi"
              />
            </>
          )}
        </>
      )}

      {showImport ? (
        <Modal title="Nhập file danh bạ" onClose={() => setShowImport(false)}>
          <form onSubmit={handleImport} className="entity-form">
            <label>
              Tên bộ danh bạ (bỏ trống = lấy tên file)
              <input
                type="text"
                maxLength={255}
                value={impName}
                onChange={(e) => setImpName(e.target.value)}
                placeholder="VD: Danh bạ BĐBP 2026"
              />
            </label>
            <label>
              Mô tả (tuỳ chọn)
              <input
                type="text"
                maxLength={500}
                value={impDesc}
                onChange={(e) => setImpDesc(e.target.value)}
              />
            </label>
            <Field
              label="File danh bạ (.xlsx hoặc .csv) — dòng đầu là tiêu đề cột"
              required
              error={impFileErr}
            >
              <input
                type="file"
                accept=".xlsx,.csv"
                required
                onChange={(e) => {
                  setImpFile(e.target.files?.[0] ?? null)
                  setImpFileErr(null)
                }}
              />
            </Field>
            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={importing || !impFile}>
                {importing ? 'Đang nhập...' : 'Nhập danh bạ'}
              </button>
              <button type="button" className="btn-cancel" onClick={() => setShowImport(false)}>
                Huỷ
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {detailContact ? (
        <Modal
          title={detailContact.full_name || `Bản ghi #${detailContact.row_index + 1}`}
          onClose={() => setDetailContact(null)}
        >
          <dl className="contact-detail">
            {columns.map((c) => (
              <div key={c} className="contact-detail-row">
                <dt>{c}</dt>
                <dd>{detailContact.extra[c] || '—'}</dd>
              </div>
            ))}
          </dl>
        </Modal>
      ) : null}
    </section>
  )
}
