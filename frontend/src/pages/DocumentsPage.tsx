import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { documentsApi } from '../api/documents'
import { ClassificationBadge } from '../components/ClassificationBadge'
import { EmptyState } from '../components/EmptyState'
import { FileViewerModal } from '../components/FileViewer'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { usePagination } from '../hooks/usePagination'
import { canPreviewFile, openFileForView } from '../utils/fileKind'
import { DOCUMENT_CATEGORY_LABELS, type DocumentCategory, type DocumentItem } from '../types/document'

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

const categories = Object.keys(DOCUMENT_CATEGORY_LABELS) as DocumentCategory[]

function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN')
}

export function DocumentsPage() {
  const { role } = useAuth()
  const navigate = useNavigate()
  const confirm = useConfirm()

  // Trang Văn bản: chỉ role 0, 1, 2 mới được tải lên / sửa / xoá tài liệu.
  const canEdit = role !== null && role <= 2

  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState<DocumentCategory | ''>('')
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [viewing, setViewing] = useState<DocumentItem | null>(null)

  const {
    page,
    pageSize,
    pageCount,
    total,
    pageItems,
    setPageIndex,
    setPageSize,
    showPagination,
  } = usePagination(docs, 20, filterCategory)

  function loadDocs() {
    setLoading(true)
    documentsApi
      .list(filterCategory ? { category: filterCategory } : undefined)
      .then(setDocs)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách tài liệu'),
      )
      .finally(() => setLoading(false))
  }

  useEffect(loadDocs, [filterCategory])

  async function handleDelete(id: number) {
    const doc = docs.find((d) => d.id === id)
    const ok = await confirm({
      message: (
        <>
          Xoá tài liệu <strong>{doc?.title ?? `#${id}`}</strong>? Tệp đính kèm sẽ bị xoá và không thể
          khôi phục.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await documentsApi.remove(id)
      setDocs((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá tài liệu')
    }
  }

  function handleView(doc: DocumentItem) {
    // PDF: mo tab moi xem truc tiep. Con lai: mo modal dung thu vien.
    if (!openFileForView(doc.file_name, doc.file_url)) setViewing(doc)
  }

  async function handleDownload(doc: DocumentItem) {
    setError(null)
    setDownloadingId(doc.id)
    try {
      const blob = await documentsApi.download(doc.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.file_name
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể tải tệp về')
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <section>
      <h1>Văn bản – Tài liệu – Biểu mẫu</h1>

      <div className="post-toolbar">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value as DocumentCategory | '')}
        >
          <option value="">Tất cả loại văn bản</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {DOCUMENT_CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>

        {canEdit ? (
          <button
            type="button"
            className="btn-create"
            onClick={() => navigate('/van-ban/moi')}
          >
            <Icon name="upload" size={16} /> Tải lên tài liệu
          </button>
        ) : null}
      </div>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : docs.length === 0 ? (
        <EmptyState message="Chưa có tài liệu nào." />
      ) : (
        <>
        <div className="post-list">
          {pageItems.map((doc) => (
            <article key={doc.id} className="post-card">
              <div className="post-card-body">
                <div className="badge-row">
                  <span className="post-category">{DOCUMENT_CATEGORY_LABELS[doc.category]}</span>
                  <ClassificationBadge value={doc.classification} />
                </div>
                <h2>{doc.title}</h2>
                <p className="post-meta">
                  {doc.uploaded_by_full_name} · {formatDate(doc.created_at)} · {doc.file_name} ·{' '}
                  {fileSize(doc.file_size)}
                </p>
                {doc.description ? <p style={{ whiteSpace: 'pre-wrap' }}>{doc.description}</p> : null}
                <div className="row-actions">
                  {canPreviewFile(doc.file_name) ? (
                    <button type="button" className="btn-view" onClick={() => handleView(doc)}>
                      <Icon name="eye" /> Xem
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="btn-approve"
                    onClick={() => handleDownload(doc)}
                    disabled={downloadingId === doc.id}
                  >
                    <Icon name="download" size={13} />{' '}
                    {downloadingId === doc.id ? 'Đang tải...' : 'Tải về'}
                  </button>
                  {canEdit ? (
                    <>
                      <button type="button" className="btn-edit" onClick={() => navigate(`/van-ban/${doc.id}/sua`)}>
                        <Icon name="edit" /> Sửa
                      </button>
                      <button type="button" className="btn-delete" onClick={() => handleDelete(doc.id)}>
                        <Icon name="trash" /> Xoá
                      </button>
                    </>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </div>
        {showPagination ? (
          <Pagination
            page={page}
            pageCount={pageCount}
            total={total}
            pageSize={pageSize}
            onPage={setPageIndex}
            onPageSize={setPageSize}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
            itemLabel="tài liệu"
          />
        ) : null}
        </>
      )}

      {viewing ? (
        <FileViewerModal
          fileName={viewing.file_name}
          fileUrl={viewing.file_url}
          title={viewing.title}
          onClose={() => setViewing(null)}
        />
      ) : null}
    </section>
  )
}
