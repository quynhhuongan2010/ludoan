import { useEffect, useMemo, useRef, useState } from 'react'
import './BangTinModule.css'

/* ============================================================================
 * Module "Bảng tin / Giáo dục chính trị" — bố cục Master / Detail
 * ----------------------------------------------------------------------------
 *  - Vùng trái  (Master) : tìm kiếm + lọc chuyên mục + danh sách bài (cuộn riêng)
 *                          + nút "Tạo bài viết mới" (chỉ ADMIN / EDITOR).
 *  - Vùng phải  (Detail) : thanh công cụ Sửa/Xoá (chỉ ADMIN / EDITOR)
 *                          + breadcrumb + tiêu đề (render 1 lần) + meta
 *                          + thân bài + ảnh có chú thích + tài liệu đính kèm.
 *  - Font tiếng Việt được ép về dạng chuẩn (NFC) để không bị "tách dấu thanh".
 *  - CSS đóng gói trong BangTinModule.css, mọi class mang tiền tố `bt-`.
 * ========================================================================== */

/* ------------------------------------------------------------------ KIỂU DỮ LIỆU */

export type ArticleCategory =
  | 'tuyen_truyen'
  | 'van_ban_chi_dao'
  | 'hoat_dong'
  | 'lich_su_truyen_thong'

export type ArticleStatus = 'da_duyet' | 'cho_duyet' | 'nhap'

export type UserRole = 'ADMIN' | 'EDITOR' | 'VIEWER'

export interface CurrentUser {
  name: string
  role: UserRole
  /** Cờ ghi đè: nếu set, quyết định quyền viết bài thay cho `role`. */
  canCreatePost?: boolean
}

/** Một khối nội dung trong thân bài — dựng có cấu trúc, không nhúng HTML thô. */
export type ArticleBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; level: 2 | 3; text: string }
  | { type: 'list'; ordered?: boolean; items: string[] }
  | { type: 'quote'; text: string }
  | { type: 'image'; src: string; alt: string; caption?: string }

export interface Attachment {
  id: string
  name: string
  /** Đường dẫn tải về (tương đối `/static/...` hoặc tuyệt đối). */
  url: string
  /** Kích thước hiển thị, ví dụ "1,2 MB". */
  size?: string
}

export interface Article {
  id: number
  title: string
  category: ArticleCategory
  /** Ngày phát hành dạng ISO (yyyy-mm-dd). */
  publishedAt: string
  /** Cơ quan / người đăng bài. */
  author: string
  status: ArticleStatus
  isPinned?: boolean
  /** Tóm tắt ngắn hiển thị ở card danh sách. */
  summary?: string
  body: ArticleBlock[]
  attachments?: Attachment[]
}

/* ------------------------------------------------------------------ HẰNG SỐ */

export const CATEGORY_LABELS: Record<ArticleCategory, string> = {
  tuyen_truyen: 'Tuyên truyền',
  van_ban_chi_dao: 'Văn bản chỉ đạo',
  hoat_dong: 'Hoạt động đơn vị',
  lich_su_truyen_thong: 'Lịch sử – Truyền thống',
}

const CATEGORY_KEYS = Object.keys(CATEGORY_LABELS) as ArticleCategory[]

const STATUS_LABELS: Record<ArticleStatus, string> = {
  da_duyet: 'Đã duyệt',
  cho_duyet: 'Chờ duyệt',
  nhap: 'Bản nháp',
}

const STATUS_CLASS: Record<ArticleStatus, string> = {
  da_duyet: 'bt-status-approved',
  cho_duyet: 'bt-status-pending',
  nhap: 'bt-status-draft',
}

/** Bài đăng trong vòng 7 ngày gần nhất được coi là "MỚI". */
const NEW_WINDOW_MS = 7 * 24 * 60 * 60 * 1000

/* ------------------------------------------------------------------ TIỆN ÍCH */

/**
 * Chuẩn hoá chuỗi tiếng Việt về Unicode NFC.
 * Dữ liệu copy từ Word / gõ Telex cũ / API đôi khi ở dạng NFD (dấu thanh nằm
 * rời thành ký tự tổ hợp) khiến trình duyệt hiển thị "TRUYỀ`N THỐ`NG".
 * `normalize('NFC')` ghép lại thành ký tự dựng sẵn.
 */
export function normalizeVI(input: string): string {
  return typeof input === 'string' ? input.normalize('NFC') : input
}

/** Định dạng ngày kiểu Việt Nam: 03/09/2026. */
function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function isNew(iso: string): boolean {
  const t = new Date(iso).getTime()
  return !Number.isNaN(t) && Date.now() - t <= NEW_WINDOW_MS
}

/** Bỏ dấu để so khớp tìm kiếm không phân biệt dấu / hoa thường. */
function foldText(s: string): string {
  return normalizeVI(s)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // bỏ dấu thanh (combining marks)
    .replace(/đ/g, 'd')
}

/** Kiểm tra quyền viết / sửa / xoá bài. */
function canWrite(user?: CurrentUser | null): boolean {
  if (!user) return false
  if (typeof user.canCreatePost === 'boolean') return user.canCreatePost
  return user.role === 'ADMIN' || user.role === 'EDITOR'
}

/* ---- Chuyển đổi thân bài <-> văn bản thô cho form soạn thảo đơn giản ---- */

/** Khối cấu trúc -> văn bản dạng markdown rút gọn để hiển thị trong <textarea>. */
function blocksToText(blocks: ArticleBlock[]): string {
  return blocks
    .filter((b) => b.type !== 'image')
    .map((b) => {
      switch (b.type) {
        case 'heading':
          return `${b.level === 2 ? '##' : '###'} ${b.text}`
        case 'list':
          return b.items.map((it) => `${b.ordered ? '1.' : '-'} ${it}`).join('\n')
        case 'quote':
          return `> ${b.text}`
        default:
          return b.text
      }
    })
    .join('\n\n')
}

/**
 * Văn bản thô -> khối cấu trúc. Cú pháp hỗ trợ:
 *   "## "  tiêu đề mục lớn      | "### " tiêu đề mục nhỏ
 *   "- "   gạch đầu dòng        | "1. "  danh sách đánh số
 *   "> "   trích dẫn            | dòng thường -> đoạn văn
 */
function textToBlocks(text: string): ArticleBlock[] {
  const lines = normalizeVI(text).replace(/\r\n/g, '\n').split('\n')
  const blocks: ArticleBlock[] = []
  let listBuf: { ordered: boolean; items: string[] } | null = null

  const flushList = () => {
    if (listBuf && listBuf.items.length) {
      blocks.push({ type: 'list', ordered: listBuf.ordered, items: listBuf.items })
    }
    listBuf = null
  }

  for (const raw of lines) {
    const line = raw.trim()
    if (!line) {
      flushList()
      continue
    }
    const ul = line.match(/^[-*]\s+(.*)$/)
    const ol = line.match(/^\d+[.)]\s+(.*)$/)
    if (ul || ol) {
      const ordered = !!ol
      if (!listBuf || listBuf.ordered !== ordered) {
        flushList()
        listBuf = { ordered, items: [] }
      }
      listBuf.items.push((ul ?? ol)![1])
      continue
    }
    flushList()
    if (line.startsWith('### ')) blocks.push({ type: 'heading', level: 3, text: line.slice(4) })
    else if (line.startsWith('## ')) blocks.push({ type: 'heading', level: 2, text: line.slice(3) })
    else if (line.startsWith('> ')) blocks.push({ type: 'quote', text: line.slice(2) })
    else blocks.push({ type: 'paragraph', text: line })
  }
  flushList()
  return blocks
}

/* ------------------------------------------------------------------ ICON (SVG nội tuyến) */

function IconSearch() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="7" />
      <line x1="16.5" y1="16.5" x2="21" y2="21" />
    </svg>
  )
}
function IconCalendar() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="4.5" width="18" height="16" rx="2" />
      <line x1="3" y1="9" x2="21" y2="9" />
      <line x1="8" y1="2.5" x2="8" y2="6.5" />
      <line x1="16" y1="2.5" x2="16" y2="6.5" />
    </svg>
  )
}
function IconUser() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
    </svg>
  )
}
function IconDoc() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
    </svg>
  )
}
function IconInbox() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 13l3-8h12l3 8" />
      <path d="M3 13v6a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-6" />
      <path d="M3 13h5l2 3h4l2-3h5" />
    </svg>
  )
}
function IconPlus() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  )
}
function IconEdit() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
    </svg>
  )
}
function IconTrash() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 6h18" />
      <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
      <path d="M6 6l1 14a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-14" />
    </svg>
  )
}

/* ------------------------------------------------------------------ THÂN BÀI */

function ArticleBody({ blocks }: { blocks: ArticleBlock[] }) {
  return (
    <div className="bt-body">
      {blocks.map((block, i) => {
        switch (block.type) {
          case 'heading': {
            const Tag = block.level === 2 ? 'h2' : 'h3'
            return <Tag key={i}>{normalizeVI(block.text)}</Tag>
          }
          case 'list':
            return block.ordered ? (
              <ol key={i}>
                {block.items.map((it, j) => (
                  <li key={j}>{normalizeVI(it)}</li>
                ))}
              </ol>
            ) : (
              <ul key={i}>
                {block.items.map((it, j) => (
                  <li key={j}>{normalizeVI(it)}</li>
                ))}
              </ul>
            )
          case 'quote':
            return <blockquote key={i}>{normalizeVI(block.text)}</blockquote>
          case 'image':
            return (
              <figure key={i} className="bt-figure">
                <img src={block.src} alt={normalizeVI(block.alt)} loading="lazy" />
                {block.caption ? <figcaption>{normalizeVI(block.caption)}</figcaption> : null}
              </figure>
            )
          case 'paragraph':
          default:
            return <p key={i}>{normalizeVI(block.text)}</p>
        }
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ FORM SOẠN THẢO */

interface DraftForm {
  title: string
  category: ArticleCategory
  summary: string
  content: string
  imageUrl: string
  imageCaption: string
  attachmentName: string
  attachmentUrl: string
}

const EMPTY_DRAFT: DraftForm = {
  title: '',
  category: 'tuyen_truyen',
  summary: '',
  content: '',
  imageUrl: '',
  imageCaption: '',
  attachmentName: '',
  attachmentUrl: '',
}

/** Nạp một bài viết có sẵn vào form (chế độ Sửa). */
function articleToDraft(a: Article): DraftForm {
  const img = a.body.find((b): b is Extract<ArticleBlock, { type: 'image' }> => b.type === 'image')
  const firstAttach = a.attachments?.[0]
  return {
    title: a.title,
    category: a.category,
    summary: a.summary ?? '',
    content: blocksToText(a.body),
    imageUrl: img?.src ?? '',
    imageCaption: img?.caption ?? '',
    attachmentName: firstAttach?.name ?? '',
    attachmentUrl: firstAttach?.url ?? '',
  }
}

function EditorModal({
  mode,
  initial,
  onCancel,
  onSubmit,
}: {
  mode: 'create' | 'edit'
  initial: DraftForm
  onCancel: () => void
  onSubmit: (draft: DraftForm) => void
}) {
  const [form, setForm] = useState<DraftForm>(initial)
  const [error, setError] = useState<string | null>(null)
  const firstFieldRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    firstFieldRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onCancel])

  function set<K extends keyof DraftForm>(key: K, value: DraftForm[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) return setError('Vui lòng nhập tiêu đề bài viết.')
    if (!form.content.trim()) return setError('Vui lòng nhập nội dung chính.')
    setError(null)
    onSubmit({
      ...form,
      title: normalizeVI(form.title.trim()),
      summary: normalizeVI(form.summary.trim()),
      content: normalizeVI(form.content),
    })
  }

  return (
    <div className="bt-modal-overlay" role="dialog" aria-modal="true" aria-label="Soạn thảo bài viết">
      <form className="bt-modal" onSubmit={handleSubmit}>
        <div className="bt-modal-head">
          <h3>{mode === 'create' ? 'Tạo bài viết mới' : 'Chỉnh sửa bài viết'}</h3>
          <button type="button" className="bt-modal-close" onClick={onCancel} aria-label="Đóng">
            ×
          </button>
        </div>

        <div className="bt-modal-body">
          <div className="bt-field">
            <label htmlFor="bt-f-title">Tiêu đề</label>
            <input
              id="bt-f-title"
              ref={firstFieldRef}
              value={form.title}
              onChange={(e) => set('title', e.target.value)}
              placeholder="Nhập tiêu đề bài viết…"
            />
          </div>

          <div className="bt-field-row">
            <div className="bt-field">
              <label htmlFor="bt-f-cat">Chuyên mục</label>
              <select
                id="bt-f-cat"
                value={form.category}
                onChange={(e) => set('category', e.target.value as ArticleCategory)}
              >
                {CATEGORY_KEYS.map((c) => (
                  <option key={c} value={c}>
                    {CATEGORY_LABELS[c]}
                  </option>
                ))}
              </select>
            </div>
            <div className="bt-field">
              <label htmlFor="bt-f-img">
                Link / File ảnh <span className="bt-hint">(không bắt buộc)</span>
              </label>
              <input
                id="bt-f-img"
                value={form.imageUrl}
                onChange={(e) => set('imageUrl', e.target.value)}
                placeholder="https://… hoặc /static/…"
              />
            </div>
          </div>

          {form.imageUrl.trim() ? (
            <div className="bt-field">
              <label htmlFor="bt-f-cap">Chú thích ảnh</label>
              <input
                id="bt-f-cap"
                value={form.imageCaption}
                onChange={(e) => set('imageCaption', e.target.value)}
                placeholder="Mô tả ngắn cho ảnh…"
              />
            </div>
          ) : null}

          <div className="bt-field">
            <label htmlFor="bt-f-sum">
              Tóm tắt <span className="bt-hint">(hiển thị ở danh sách)</span>
            </label>
            <input
              id="bt-f-sum"
              value={form.summary}
              onChange={(e) => set('summary', e.target.value)}
              placeholder="Một câu tóm tắt nội dung…"
            />
          </div>

          <div className="bt-field">
            <label htmlFor="bt-f-body">Nội dung chính</label>
            <span className="bt-hint">
              Xuống dòng trống để tách đoạn. Cú pháp: <code>## Mục lớn</code>, <code>### Mục nhỏ</code>,{' '}
              <code>- gạch đầu dòng</code>, <code>1. đánh số</code>, <code>&gt; trích dẫn</code>.
            </span>
            <textarea
              id="bt-f-body"
              value={form.content}
              onChange={(e) => set('content', e.target.value)}
              rows={10}
              placeholder={'Nhập nội dung bài viết…'}
            />
          </div>

          <div className="bt-field-row">
            <div className="bt-field">
              <label htmlFor="bt-f-att-name">
                Tên tài liệu đính kèm <span className="bt-hint">(không bắt buộc)</span>
              </label>
              <input
                id="bt-f-att-name"
                value={form.attachmentName}
                onChange={(e) => set('attachmentName', e.target.value)}
                placeholder="VD: Ke-hoach.pdf"
              />
            </div>
            <div className="bt-field">
              <label htmlFor="bt-f-att-url">Link tải tài liệu</label>
              <input
                id="bt-f-att-url"
                value={form.attachmentUrl}
                onChange={(e) => set('attachmentUrl', e.target.value)}
                placeholder="/static/documents/…"
              />
            </div>
          </div>

          {error ? <p className="bt-form-error">{error}</p> : null}
        </div>

        <div className="bt-modal-foot">
          <button type="button" className="bt-btn bt-btn-ghost" onClick={onCancel}>
            Huỷ
          </button>
          <button type="submit" className="bt-btn bt-btn-primary">
            {mode === 'create' ? 'Đăng bài' : 'Lưu thay đổi'}
          </button>
        </div>
      </form>
    </div>
  )
}

/* ------------------------------------------------------------------ COMPONENT CHÍNH */

export interface BangTinModuleProps {
  /** Danh sách bài viết ban đầu. Không truyền -> dùng `mockArticles`. */
  articles?: Article[]
  /** Người dùng hiện tại — quyết định hiển thị nút Tạo / Sửa / Xoá. */
  currentUser?: CurrentUser | null
  /** Chiều cao Navbar phía trên (px) để module không chồng lên thanh điều hướng. */
  navbarOffset?: number
  /** Bề rộng panel danh sách (px), mặc định 340. */
  masterWidth?: number
  /** Bấm vào tài liệu đính kèm — mặc định mở tab mới. */
  onOpenAttachment?: (attachment: Attachment) => void
  /** Hook tích hợp API thật (nếu bỏ trống, thao tác chỉ cập nhật state cục bộ). */
  onCreate?: (article: Article) => void
  onUpdate?: (article: Article) => void
  onDelete?: (id: number) => void
}

export function BangTinModule({
  articles,
  currentUser = null,
  navbarOffset = 64,
  masterWidth = 340,
  onOpenAttachment,
  onCreate,
  onUpdate,
  onDelete,
}: BangTinModuleProps) {
  // Danh sách bài viết được quản lý trong state để Tạo / Sửa / Xoá hoạt động
  // ngay cả khi chưa nối API.
  const [list, setList] = useState<Article[]>(articles ?? mockArticles)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<ArticleCategory | 'all'>('all')
  const [activeId, setActiveId] = useState<number | null>(list[0]?.id ?? null)
  const [editor, setEditor] = useState<{ mode: 'create' | 'edit'; draft: DraftForm } | null>(null)

  const writable = canWrite(currentUser)

  // Đồng bộ khi prop `articles` thay đổi từ bên ngoài.
  useEffect(() => {
    if (articles) setList(articles)
  }, [articles])

  // Các chuyên mục thực sự có mặt trong dữ liệu -> dựng danh sách nút lọc.
  const availableCategories = useMemo(() => {
    const set = new Set<ArticleCategory>(list.map((a) => a.category))
    return CATEGORY_KEYS.filter((c) => set.has(c))
  }, [list])

  // Lọc theo chuyên mục + từ khoá (không phân biệt dấu), rồi sắp xếp.
  const filtered = useMemo(() => {
    const q = foldText(search.trim())
    return list
      .filter((a) => category === 'all' || a.category === category)
      .filter((a) => (q ? foldText(a.title).includes(q) : true))
      .sort((a, b) => {
        if (!!a.isPinned !== !!b.isPinned) return a.isPinned ? -1 : 1
        return b.publishedAt.localeCompare(a.publishedAt)
      })
  }, [list, category, search])

  const activeArticle =
    filtered.find((a) => a.id === activeId) ?? list.find((a) => a.id === activeId) ?? null

  function handleOpenAttachment(att: Attachment) {
    if (onOpenAttachment) onOpenAttachment(att)
    else window.open(att.url, '_blank', 'noopener,noreferrer')
  }

  /** Dựng đối tượng Article từ dữ liệu form. */
  function draftToArticle(draft: DraftForm, base?: Article): Article {
    const body = textToBlocks(draft.content)
    if (draft.imageUrl.trim()) {
      body.push({
        type: 'image',
        src: draft.imageUrl.trim(),
        alt: draft.imageCaption.trim() || draft.title,
        caption: draft.imageCaption.trim() || undefined,
      })
    }
    const attachments: Attachment[] = draft.attachmentUrl.trim()
      ? [
          {
            id: base?.attachments?.[0]?.id ?? `att-${Date.now()}`,
            name: draft.attachmentName.trim() || 'Tài liệu đính kèm',
            url: draft.attachmentUrl.trim(),
            size: base?.attachments?.[0]?.size,
          },
        ]
      : []
    return {
      id: base?.id ?? Date.now(),
      title: draft.title,
      category: draft.category,
      summary: draft.summary || undefined,
      publishedAt: base?.publishedAt ?? new Date().toISOString().slice(0, 10),
      author: base?.author ?? currentUser?.name ?? 'Không rõ',
      status: base?.status ?? (currentUser?.role === 'ADMIN' ? 'da_duyet' : 'cho_duyet'),
      isPinned: base?.isPinned,
      body,
      attachments,
    }
  }

  function handleSubmitEditor(draft: DraftForm) {
    if (!editor) return
    if (editor.mode === 'create') {
      const article = draftToArticle(draft)
      setList((prev) => [article, ...prev])
      setActiveId(article.id)
      onCreate?.(article)
    } else if (activeArticle) {
      const updated = draftToArticle(draft, activeArticle)
      setList((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
      onUpdate?.(updated)
    }
    setEditor(null)
  }

  function handleDelete() {
    if (!activeArticle) return
    const ok = window.confirm(
      `Xoá bài viết "${normalizeVI(activeArticle.title)}"? Thao tác này không thể hoàn tác.`,
    )
    if (!ok) return
    const id = activeArticle.id
    setList((prev) => prev.filter((a) => a.id !== id))
    setActiveId((cur) => (cur === id ? null : cur))
    onDelete?.(id)
  }

  return (
    <div
      className="bt-module"
      style={
        {
          '--bt-navbar-offset': `${navbarOffset}px`,
          '--bt-master-width': `${masterWidth}px`,
        } as React.CSSProperties
      }
    >
      {/* ============================ MASTER — danh sách bài viết ============================ */}
      <aside className="bt-master">
        <div className="bt-master-head">
          <h2 className="bt-master-title">Bảng tin đơn vị</h2>
          <div className="bt-search">
            <IconSearch />
            <input
              type="search"
              placeholder="Tìm theo tiêu đề bài viết…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Tìm kiếm bài viết"
            />
          </div>

          {/* Nút tạo mới — chỉ hiện với ADMIN / EDITOR */}
          {writable ? (
            <button
              type="button"
              className="bt-create-btn"
              onClick={() => setEditor({ mode: 'create', draft: { ...EMPTY_DRAFT } })}
            >
              <IconPlus /> Tạo bài viết mới
            </button>
          ) : null}
        </div>

        {/* Bộ lọc chuyên mục con */}
        <div className="bt-filters" role="tablist" aria-label="Lọc theo chuyên mục">
          <button
            type="button"
            role="tab"
            aria-selected={category === 'all'}
            className={`bt-filter${category === 'all' ? ' is-active' : ''}`}
            onClick={() => setCategory('all')}
          >
            Tất cả
          </button>
          {availableCategories.map((c) => (
            <button
              key={c}
              type="button"
              role="tab"
              aria-selected={category === c}
              className={`bt-filter${category === c ? ' is-active' : ''}`}
              onClick={() => setCategory(c)}
            >
              {CATEGORY_LABELS[c]}
            </button>
          ))}
        </div>

        {/* Danh sách tin — vùng cuộn độc lập */}
        {filtered.length === 0 ? (
          <p className="bt-list-empty">Không có bài viết phù hợp.</p>
        ) : (
          <ul className="bt-list">
            {filtered.map((a) => {
              const active = a.id === activeArticle?.id
              return (
                <li key={a.id}>
                  <button
                    type="button"
                    className={`bt-card${active ? ' is-active' : ''}`}
                    aria-current={active ? 'true' : undefined}
                    onClick={() => setActiveId(a.id)}
                  >
                    <div className="bt-card-badges">
                      <span className="bt-badge bt-badge-cat">{CATEGORY_LABELS[a.category]}</span>
                      {a.isPinned ? <span className="bt-badge bt-badge-pin">Ghim</span> : null}
                      {isNew(a.publishedAt) ? <span className="bt-badge bt-badge-new">Mới</span> : null}
                    </div>
                    <div className="bt-card-title">{normalizeVI(a.title)}</div>
                    <div className="bt-card-date">{formatDate(a.publishedAt)}</div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </aside>

      {/* ============================ DETAIL — chi tiết bài viết ============================ */}
      <main className="bt-detail">
        {!activeArticle ? (
          <div className="bt-detail-empty">
            <IconInbox />
            <p>Chọn một bài viết ở danh sách bên trái để xem nội dung.</p>
          </div>
        ) : (
          <article className="bt-detail-inner">
            {/* Thanh công cụ Sửa / Xoá — chỉ hiện với ADMIN / EDITOR */}
            {writable ? (
              <div className="bt-detail-toolbar">
                <button
                  type="button"
                  className="bt-btn"
                  onClick={() =>
                    setEditor({ mode: 'edit', draft: articleToDraft(activeArticle) })
                  }
                >
                  <IconEdit /> Chỉnh sửa
                </button>
                <button type="button" className="bt-btn bt-btn-danger" onClick={handleDelete}>
                  <IconTrash /> Xoá
                </button>
              </div>
            ) : null}

            {/* Breadcrumb điều hướng nội bộ */}
            <nav className="bt-breadcrumb" aria-label="Đường dẫn">
              <a href="#">Trang chủ</a>
              <span className="bt-crumb-sep">›</span>
              <a href="#">Bảng tin</a>
              <span className="bt-crumb-sep">›</span>
              <span className="bt-crumb-current">{CATEGORY_LABELS[activeArticle.category]}</span>
            </nav>

            {/* Tiêu đề — CHỈ 1 lần */}
            <h1 className="bt-detail-title">{normalizeVI(activeArticle.title)}</h1>

            {/* Meta-bar */}
            <div className="bt-meta">
              <span className="bt-meta-item">
                <IconCalendar />
                Ngày phát hành: <strong>{formatDate(activeArticle.publishedAt)}</strong>
              </span>
              <span className="bt-meta-item">
                <IconUser />
                <strong>{normalizeVI(activeArticle.author)}</strong>
              </span>
              <span className={`bt-status ${STATUS_CLASS[activeArticle.status]}`}>
                {STATUS_LABELS[activeArticle.status]}
              </span>
            </div>

            {/* Thân bài */}
            <ArticleBody blocks={activeArticle.body} />

            {/* Tài liệu đính kèm */}
            {activeArticle.attachments && activeArticle.attachments.length > 0 ? (
              <section className="bt-attachments">
                <h3>Tài liệu đính kèm</h3>
                <ul className="bt-attach-list">
                  {activeArticle.attachments.map((att) => (
                    <li key={att.id}>
                      <button
                        type="button"
                        className="bt-attach-item"
                        onClick={() => handleOpenAttachment(att)}
                      >
                        <span className="bt-attach-icon">
                          <IconDoc />
                        </span>
                        <span className="bt-attach-name">{normalizeVI(att.name)}</span>
                        {att.size ? <span className="bt-attach-size">{att.size}</span> : null}
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </article>
        )}
      </main>

      {/* ============================ MODAL SOẠN THẢO ============================ */}
      {editor && writable ? (
        <EditorModal
          mode={editor.mode}
          initial={editor.draft}
          onCancel={() => setEditor(null)}
          onSubmit={handleSubmitEditor}
        />
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ DỮ LIỆU MẪU */

/**
 * Dữ liệu mẫu để kiểm thử chuyển bài / active state / phân quyền khi chưa nối API.
 * Khi tích hợp thật: truyền prop `articles` (lấy từ `educationMaterialsApi`)
 * và `currentUser` (từ `AuthContext`).
 */
export const mockArticles: Article[] = [
  {
    id: 1,
    title: 'Phát huy truyền thống anh hùng, xây dựng đơn vị vững mạnh toàn diện',
    category: 'lich_su_truyen_thong',
    publishedAt: '2026-09-01',
    author: 'Phòng Chính trị',
    status: 'da_duyet',
    isPinned: true,
    summary: 'Ôn lại chặng đường xây dựng, chiến đấu và trưởng thành của đơn vị.',
    body: [
      {
        type: 'paragraph',
        text: 'Trải qua các thời kỳ xây dựng và trưởng thành, cán bộ, chiến sĩ đơn vị luôn nêu cao tinh thần trách nhiệm, đoàn kết, chủ động khắc phục khó khăn, hoàn thành tốt mọi nhiệm vụ được giao.',
      },
      { type: 'heading', level: 2, text: 'Những mốc son truyền thống' },
      {
        type: 'list',
        items: [
          'Bảo đảm thông tin liên lạc thông suốt trong mọi tình huống.',
          'Xây dựng đơn vị chính quy, mẫu mực, tiêu biểu.',
          'Chăm lo đời sống vật chất, tinh thần cho bộ đội.',
        ],
      },
      {
        type: 'image',
        src: 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=1000&q=80',
        alt: 'Cán bộ, chiến sĩ trong giờ huấn luyện',
        caption: 'Cán bộ, chiến sĩ đơn vị trong một buổi huấn luyện chuyên ngành thông tin.',
      },
      { type: 'heading', level: 2, text: 'Phương hướng thời gian tới' },
      {
        type: 'quote',
        text: 'Tiếp tục quán triệt sâu sắc nhiệm vụ, giữ vững kỷ luật, nâng cao chất lượng huấn luyện và sẵn sàng chiến đấu.',
      },
      {
        type: 'paragraph',
        text: 'Toàn đơn vị quyết tâm giữ vững và phát huy truyền thống, hoàn thành xuất sắc nhiệm vụ chính trị trung tâm năm 2026.',
      },
    ],
    attachments: [
      { id: 'a1', name: 'De-cuong-tuyen-truyen-truyen-thong.pdf', url: '#', size: '820 KB' },
    ],
  },
  {
    id: 2,
    title: 'Hướng dẫn học tập, quán triệt nghị quyết trong quý IV',
    category: 'van_ban_chi_dao',
    publishedAt: '2026-08-28',
    author: 'Ban Tuyên huấn',
    status: 'da_duyet',
    summary: 'Kế hoạch tổ chức đợt sinh hoạt chính trị sâu rộng trong toàn đơn vị.',
    body: [
      {
        type: 'paragraph',
        text: 'Nhằm nâng cao nhận thức và thống nhất hành động, các cơ quan, đơn vị tổ chức nghiên cứu, học tập theo đúng kế hoạch, bảo đảm nghiêm túc, thiết thực, hiệu quả.',
      },
      { type: 'heading', level: 3, text: '1. Đối tượng và thời gian' },
      {
        type: 'paragraph',
        text: 'Toàn thể cán bộ, đảng viên và quần chúng; hoàn thành trước ngày 30/10/2026.',
      },
      { type: 'heading', level: 3, text: '2. Hình thức tổ chức' },
      {
        type: 'list',
        ordered: true,
        items: [
          'Học tập tập trung theo cụm cơ quan, đơn vị.',
          'Thảo luận tại tổ, viết thu hoạch cá nhân.',
          'Kiểm tra, đánh giá kết quả và rút kinh nghiệm.',
        ],
      },
    ],
    attachments: [
      { id: 'a2', name: 'Ke-hoach-hoc-tap-quy-IV.doc', url: '#', size: '1,1 MB' },
      { id: 'a3', name: 'Mau-ban-thu-hoach.docx', url: '#', size: '48 KB' },
    ],
  },
  {
    id: 3,
    title: 'Sôi nổi phong trào thi đua chào mừng ngày truyền thống đơn vị',
    category: 'hoat_dong',
    publishedAt: '2026-09-02',
    author: 'Đại đội 5',
    status: 'da_duyet',
    summary: 'Nhiều hoạt động văn hoá, thể thao, lao động tạo khí thế thi đua sôi nổi.',
    body: [
      {
        type: 'paragraph',
        text: 'Hưởng ứng đợt thi đua cao điểm, các đơn vị đã tổ chức nhiều hoạt động thiết thực: ra quân làm công tác doanh trại, giao lưu thể thao, hội thi trang trí phòng Hồ Chí Minh.',
      },
      {
        type: 'image',
        src: 'https://images.unsplash.com/photo-1526976668912-1a811878dd37?w=1000&q=80',
        alt: 'Hoạt động thể thao của đơn vị',
        caption: 'Trận bóng chuyền giao hữu giữa các phân đội trong khuôn khổ đợt thi đua.',
      },
      {
        type: 'paragraph',
        text: 'Các hoạt động góp phần xây dựng môi trường văn hoá lành mạnh, tăng cường đoàn kết, gắn bó trong đơn vị.',
      },
    ],
  },
  {
    id: 4,
    title: 'Đẩy mạnh tuyên truyền phòng, chống thông tin xấu độc trên không gian mạng',
    category: 'tuyen_truyen',
    publishedAt: '2026-08-20',
    author: 'Phòng Chính trị',
    status: 'cho_duyet',
    summary: 'Nâng cao ý thức cảnh giác, kỹ năng nhận diện và ứng xử trên mạng xã hội.',
    body: [
      {
        type: 'paragraph',
        text: 'Mỗi quân nhân cần nêu cao tinh thần cảnh giác, không chia sẻ, lan truyền các thông tin chưa được kiểm chứng, có nội dung sai trái, thù địch.',
      },
      { type: 'heading', level: 2, text: 'Một số lưu ý khi sử dụng mạng xã hội' },
      {
        type: 'list',
        items: [
          'Kiểm chứng nguồn tin trước khi chia sẻ.',
          'Không bình luận, hưởng ứng nội dung tiêu cực.',
          'Báo cáo kịp thời với chỉ huy khi phát hiện dấu hiệu bất thường.',
        ],
      },
      {
        type: 'quote',
        text: 'Chủ động thông tin tích cực, lấy cái đẹp dẹp cái xấu, xây dựng không gian mạng lành mạnh.',
      },
    ],
    attachments: [
      { id: 'a4', name: 'Tai-lieu-tuyen-truyen-an-toan-thong-tin.pdf', url: '#', size: '2,4 MB' },
    ],
  },
]

export default BangTinModule
