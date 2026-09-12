import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type ClipboardEvent,
  type DragEvent,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
} from 'react'
import { ApiError } from '../api/client'
import { uploadsApi } from '../api/uploads'
import { useConfirm } from '../context/ConfirmContext'
import { usePrompt } from '../context/PromptContext'
import {
  absolutizeContentImages,
  isInternalHref,
  relativizeContentImages,
  sanitizeContentHtml,
} from '../utils/richContent'
import { Icon } from './Icon'

const IMAGE_ACCEPT = '.jpg,.jpeg,.png,.gif,.webp'
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
const MAX_IMAGE_MB = 20

const VIDEO_ACCEPT = '.mp4,.webm,.ogg,.mov,.m4v'
const VIDEO_EXTENSIONS = ['.mp4', '.webm', '.ogg', '.mov', '.m4v']
const MAX_VIDEO_MB = 200

const EMPTY_HTML = '<p><br></p>'
/** Phan tu khoi khong nen dung o dau o soan (khong dat duoc con tro phia truoc). */
const LEAD_EDGE = /^(TABLE|FIGURE|HR|VIDEO|IMG)$/
/** Phan tu khoi khong nen dung o cuoi o soan (khong dat duoc con tro phia sau). */
const TAIL_EDGE = /^(TABLE|FIGURE|HR|VIDEO|IMG)$/
const HISTORY_LIMIT = 120

type BlockKind = 'image' | 'video' | null

interface RichContentEditorProps {
  /** Noi dung dang luu tru (duong dan anh/video o dang tuong doi /static/...). */
  value: string
  /** Goi lai voi noi dung moi, da chuyen anh/video ve duong dan tuong doi. */
  onChange: (html: string) => void
  placeholder?: string
  disabled?: boolean
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** Van ban thuan -> cac doan <p> (giu xuong dong don bang <br>). */
function textToHtml(text: string): string {
  return text
    .replace(/\r\n?/g, '\n')
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => `<p>${escapeHtml(block).replace(/\n/g, '<br>')}</p>`)
    .join('')
}

/**
 * Lam sach HTML dan tu Word / trinh duyet / chat: bo style/class/id, go span,
 * doi div->p, ha H1/H4+ ve H2/H3, va — QUAN TRONG cho mang noi bo — go moi
 * anh/lien ket tro ra Internet. Tra chuoi rong neu khong con noi dung.
 */
function cleanPastedHtml(raw: string): string {
  const safe = sanitizeContentHtml(raw)
  const doc = new DOMParser().parseFromString(safe, 'text/html')
  const root = doc.body

  root.querySelectorAll('span, font').forEach((s) => {
    const parent = s.parentNode
    if (!parent) return
    while (s.firstChild) parent.insertBefore(s.firstChild, s)
    parent.removeChild(s)
  })

  root.querySelectorAll('div, h1, h4, h5, h6').forEach((n) => {
    const tag = n.tagName === 'DIV' ? 'p' : n.tagName === 'H1' ? 'h2' : 'h3'
    const repl = doc.createElement(tag)
    while (n.firstChild) repl.appendChild(n.firstChild)
    n.replaceWith(repl)
  })

  root.querySelectorAll('*').forEach((n) => {
    const keep =
      n.tagName === 'A' ? ['href'] : n.tagName === 'IMG' ? ['src', 'alt'] : []
    Array.from(n.attributes).forEach((a) => {
      if (!keep.includes(a.name.toLowerCase())) n.removeAttribute(a.name)
    })
    if (n.tagName === 'A') {
      const href = n.getAttribute('href') || ''
      if (!isInternalHref(href)) {
        const parent = n.parentNode
        if (parent) {
          while (n.firstChild) parent.insertBefore(n.firstChild, n)
          parent.removeChild(n)
        }
      }
    }
  })

  root.querySelectorAll('p, h2, h3, blockquote, li').forEach((n) => {
    if (!n.textContent?.trim() && !n.querySelector('img, br')) n.remove()
  })

  return root.innerHTML.trim()
}

/**
 * O soan thao noi dung dang trang bao (contentEditable). Toan bo tinh nang
 * chay noi bo, KHONG keo tai nguyen tu Internet:
 *   - Chu: dam / nghieng / gach chan / gach ngang / tieu de / trich dan / danh
 *     sach / can le / bo dinh dang.
 *   - Anh & video: tai tu may len server noi bo (dan Ctrl+V, keo-tha, hoac nut).
 *     Anh dang chon co thanh cong cu: doi kich thuoc, can le, va DI CHUYEN
 *     len/xuong trong bai.
 *   - Bang: chen 3x3 roi them/bot hang - cot ngay tren thanh cong cu bang.
 *   - Hoan tac / Lam lai rieng cua o soan (Ctrl+Z / Ctrl+Y) - khong phu thuoc
 *     lich su chap va cua trinh duyet von hay hong sau khi chen khoi.
 *   - Lien ket chi nhan duong dan noi bo (tu choi lien ket ra Internet).
 */
export function RichContentEditor({ value, onChange, placeholder, disabled }: RichContentEditorProps) {
  const prompt = usePrompt()
  const confirm = useConfirm()
  const editorRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoInputRef = useRef<HTMLInputElement>(null)
  const savedRangeRef = useRef<Range | null>(null)
  const selectedRef = useRef<HTMLElement | null>(null)
  /** HTML (dang tuong doi) lan cuoi o nay phat ra ngoai - de phan biet thay doi
   * do chinh o gay ra (bo qua) voi thay doi tu ben ngoai (nap lai). */
  const lastHtmlRef = useRef<string>(value || '')
  const historyRef = useRef<{ stack: string[]; index: number }>({ stack: [], index: -1 })
  const pendingHistoryRef = useRef<number | null>(null)

  const [uploading, setUploading] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [selKind, setSelKind] = useState<BlockKind>(null)
  const [tableActive, setTableActive] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [hist, setHist] = useState({ undo: false, redo: false })
  const [counts, setCounts] = useState({ words: 0, chars: 0 })

  const IMG_SIZES = ['rc-w-25', 'rc-w-50', 'rc-w-75', 'rc-w-100'] as const
  const IMG_ALIGNS = ['rc-left', 'rc-center', 'rc-right', 'rc-float-left', 'rc-float-right'] as const

  // ---- Dem tu / ky tu -------------------------------------------------------
  function refreshCounts() {
    const el = editorRef.current
    if (!el) return
    const text = (el.textContent || '').replace(/ /g, ' ').trim()
    setCounts({ chars: text.length, words: text ? text.split(/\s+/).length : 0 })
  }

  // ---- Lich su hoan tac / lam lai -----------------------------------------
  function syncHistFlags() {
    const h = historyRef.current
    setHist({ undo: h.index > 0, redo: h.index < h.stack.length - 1 })
  }
  function seedHistory(rel: string) {
    historyRef.current = { stack: [rel], index: 0 }
    syncHistFlags()
  }
  function commitHistory(rel: string) {
    const h = historyRef.current
    if (h.stack[h.index] === rel) return
    h.stack = h.stack.slice(0, h.index + 1)
    h.stack.push(rel)
    if (h.stack.length > HISTORY_LIMIT) h.stack.shift()
    h.index = h.stack.length - 1
    syncHistFlags()
  }
  function scheduleHistory(rel: string) {
    if (pendingHistoryRef.current) window.clearTimeout(pendingHistoryRef.current)
    pendingHistoryRef.current = window.setTimeout(() => {
      pendingHistoryRef.current = null
      commitHistory(rel)
    }, 450)
  }
  /** Chot ngay diem lich su hien tai (goi truoc moi thao tac chen/xoa khoi). */
  function flushHistory() {
    if (pendingHistoryRef.current) {
      window.clearTimeout(pendingHistoryRef.current)
      pendingHistoryRef.current = null
    }
    const el = editorRef.current
    if (el) commitHistory(relativizeContentImages(el.innerHTML.replace(/\s*\brc-selected\b/g, '')))
  }
  function applyHistory(dir: -1 | 1) {
    const el = editorRef.current
    if (!el) return
    if (pendingHistoryRef.current) {
      window.clearTimeout(pendingHistoryRef.current)
      pendingHistoryRef.current = null
    }
    const h = historyRef.current
    const next = h.index + dir
    if (next < 0 || next >= h.stack.length) return
    h.index = next
    const rel = h.stack[next]
    el.innerHTML = absolutizeContentImages(rel) || EMPTY_HTML
    clearBlockSelection()
    setTableActive(false)
    lastHtmlRef.current = rel
    onChange(rel)
    refreshCounts()
    syncHistFlags()
    el.focus()
    placeCaretAtEnd(el)
  }

  // ---- Nap noi dung ban dau + dong bo tu ngoai --------------------------
  useEffect(() => {
    const el = editorRef.current
    if (!el) return
    el.innerHTML = absolutizeContentImages(value || '') || EMPTY_HTML
    lastHtmlRef.current = value || ''
    seedHistory(relativizeContentImages(el.innerHTML.replace(/\s*\brc-selected\b/g, '')))
    refreshCounts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const el = editorRef.current
    if (!el) return
    if ((value || '') === lastHtmlRef.current) return // thay doi do chinh o gay ra
    const incoming = absolutizeContentImages(value || '') || EMPTY_HTML
    const current = el.innerHTML.replace(/\s*\brc-selected\b/g, '')
    if (current === incoming) {
      lastHtmlRef.current = value || ''
      return
    }
    // Noi dung khac han tu ben ngoai (vd chuyen sang sua bai khac) -> nap lai.
    el.innerHTML = incoming
    lastHtmlRef.current = value || ''
    clearBlockSelection()
    setTableActive(false)
    seedHistory(relativizeContentImages(incoming))
    refreshCounts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  useEffect(() => {
    function onSelChange() {
      if (document.activeElement === editorRef.current) updateTableTools()
    }
    document.addEventListener('selectionchange', onSelChange)
    return () => {
      document.removeEventListener('selectionchange', onSelChange)
      if (pendingHistoryRef.current) window.clearTimeout(pendingHistoryRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /**
   * Doi `style="text-align:..."` (do lenh canh le / dan tu Word sinh ra) thanh
   * lop `rc-align-*` va go MOI thuoc tinh style con lai - vi bo loc hien thi
   * khong giu `style` (tranh CSS ngoai luon vao). Giu canh le duoi dang lop.
   */
  function normalizeInlineStyles() {
    const el = editorRef.current
    if (!el) return
    el.querySelectorAll('[style]').forEach((node) => {
      const n = node as HTMLElement
      const ta = n.style.textAlign
      n.classList.remove('rc-align-left', 'rc-align-center', 'rc-align-right')
      if (ta === 'center') n.classList.add('rc-align-center')
      else if (ta === 'right') n.classList.add('rc-align-right')
      else if (ta === 'left' || ta === 'start') n.classList.add('rc-align-left')
      n.removeAttribute('style')
    })
  }

  // ---- Phat thay doi ra ngoai --------------------------------------------
  function emitChange() {
    const el = editorRef.current
    if (!el) return
    normalizeInlineStyles()
    // "rc-selected" chi la lop danh dau anh dang chon - khong luu vao bai viet.
    const html = el.innerHTML.replace(/\s*\brc-selected\b/g, '')
    const rel = relativizeContentImages(html)
    lastHtmlRef.current = rel
    onChange(rel)
    scheduleHistory(rel)
    refreshCounts()
  }

  // ---- Con tro / vung chon ---------------------------------------------
  function placeCaretAtEnd(el: HTMLElement) {
    const range = document.createRange()
    range.selectNodeContents(el)
    range.collapse(false)
    const sel = window.getSelection()
    sel?.removeAllRanges()
    sel?.addRange(range)
  }
  function saveSelection() {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0 && editorRef.current?.contains(sel.anchorNode)) {
      savedRangeRef.current = sel.getRangeAt(0).cloneRange()
    }
  }
  function restoreSelection() {
    const sel = window.getSelection()
    if (!sel || !savedRangeRef.current) return
    sel.removeAllRanges()
    sel.addRange(savedRangeRef.current)
  }
  /** Vung chon da luu (`savedRangeRef`) co con dung duoc khong: hai dau vung
   * van con trong DOM va nam gon trong o soan. */
  function savedRangeUsable(el: HTMLElement): boolean {
    const r = savedRangeRef.current
    if (!r) return false
    try {
      return (
        r.startContainer.isConnected &&
        r.endContainer.isConnected &&
        el.contains(r.startContainer) &&
        el.contains(r.endContainer)
      )
    } catch {
      return false
    }
  }
  /** Range cua vung chon dang song NEU no nam gon trong o soan, nguoc lai null. */
  function liveCaretRange(el: HTMLElement): Range | null {
    const sel = window.getSelection()
    if (!sel || sel.rangeCount === 0) return null
    const r = sel.getRangeAt(0)
    if (!el.contains(r.startContainer) || !el.contains(r.endContainer)) return null
    return r
  }
  function closestInEditor(selector: string): HTMLElement | null {
    const sel = window.getSelection()
    let node: Node | null = sel && sel.rangeCount ? sel.getRangeAt(0).startContainer : null
    if (node && node.nodeType === 3) node = node.parentNode
    const el = node as HTMLElement | null
    if (!el || !editorRef.current?.contains(el)) return null
    return el.closest(selector)
  }

  /** Bao dam luon co doan van co the go chu o dau va cuoi o soan. */
  function ensureEditableEdges() {
    const el = editorRef.current
    if (!el) return
    if (!el.firstChild) {
      el.innerHTML = EMPTY_HTML
      return
    }
    const first = el.firstElementChild
    if (first && LEAD_EDGE.test(first.tagName)) {
      const p = document.createElement('p')
      p.innerHTML = '<br>'
      el.insertBefore(p, first)
    }
    const last = el.lastElementChild
    if (!last || TAIL_EDGE.test(last.tagName)) {
      const p = document.createElement('p')
      p.innerHTML = '<br>'
      el.appendChild(p)
    }
  }

  // ---- Chen HTML tai con tro -------------------------------------------
  /**
   * Chen `html` tai con tro.
   *
   * `collapseFirst = true` cho cac thao tac CHEN KHOI (anh / video / bang /
   * duong ke): luon THU GON vung chon ve con tro truoc khi chen. Ly do: sau khi
   * `el.focus()` (quay lai tu hop thoai chon tep, hoac bam nut tren thanh cong
   * cu) mot so trinh duyet tu boi den TOAN BO noi dung o soan; ma
   * `execCommand('insertHTML')` xoa phan dang boi den truoc khi chen => mat
   * sach chu. Uu tien dung lai vung chon nguoi dung da luu (`saveSelection`)
   * truoc khi roi o. Rieng dan (paste) giu hanh vi "chen de len vung dang chon".
   */
  function insertHtmlAtCursor(html: string, collapseFirst = false) {
    const el = editorRef.current
    if (!el) return
    flushHistory()
    el.focus()
    const sel = window.getSelection()

    let target: Range | null = null
    if (savedRangeUsable(el)) target = savedRangeRef.current!.cloneRange()
    else {
      const live = liveCaretRange(el)
      if (live) target = live.cloneRange()
    }
    if (target && collapseFirst) target.collapse(true)

    if (target) {
      try {
        sel?.removeAllRanges()
        sel?.addRange(target)
      } catch {
        placeCaretAtEnd(el)
      }
    } else if (collapseFirst || !liveCaretRange(el)) {
      placeCaretAtEnd(el)
    }

    const ok = document.execCommand('insertHTML', false, html)
    if (!ok) {
      const liveSel = window.getSelection()
      const frag = document.createRange().createContextualFragment(html)
      const r = liveSel && liveSel.rangeCount > 0 ? liveSel.getRangeAt(0) : null
      if (r && el.contains(r.startContainer)) {
        if (collapseFirst) r.collapse(true)
        r.insertNode(frag)
      } else {
        el.appendChild(frag)
      }
    }
    ensureEditableEdges()
    emitChange()
  }

  function insertImageAtCursor(relativeUrl: string) {
    const absoluteUrl = absolutizeContentImages(relativeUrl)
    insertHtmlAtCursor(
      `<p><img src="${absoluteUrl}" alt="" class="rc-img rc-w-100 rc-center" /></p><p><br></p>`,
      true,
    )
  }
  function insertVideoAtCursor(relativeUrl: string) {
    const absoluteUrl = absolutizeContentImages(relativeUrl)
    insertHtmlAtCursor(
      `<p><video controls preload="metadata" src="${absoluteUrl}"></video></p><p><br></p>`,
      true,
    )
  }

  /** Chen bang 3x3 (hang dau la tieu de) vao dung vi tri con tro. */
  function insertTable() {
    const cols = 3
    const rows = 3
    const head = `<tr>${Array.from({ length: cols }, (_, i) => `<th>Cột ${i + 1}</th>`).join('')}</tr>`
    const bodyRows = Array.from(
      { length: rows - 1 },
      () => `<tr>${Array.from({ length: cols }, () => '<td>&nbsp;</td>').join('')}</tr>`,
    ).join('')
    insertHtmlAtCursor(
      `<table class="rc-table"><thead>${head}</thead><tbody>${bodyRows}</tbody></table><p><br></p>`,
      true,
    )
  }

  function insertHr() {
    insertHtmlAtCursor('<hr><p><br></p>', true)
  }

  // ---- Lien ket (chi noi bo) ------------------------------------------
  async function handleLink() {
    saveSelection()
    const res = await prompt({
      title: 'Chèn liên kết nội bộ',
      message:
        'Chỉ nhận đường dẫn trong mạng nội bộ: bắt đầu bằng “/” (vd /van-ban), neo “#…”, hoặc địa chỉ máy chủ LAN. Liên kết ra Internet sẽ bị từ chối.',
      fields: [{ name: 'url', label: 'Đường dẫn', placeholder: '/tin-tuc/…', maxLength: 500 }],
      confirmText: 'Chèn liên kết',
    })
    if (!res || !res.url.trim()) return
    const url = res.url.trim()
    if (!isInternalHref(url)) {
      setNotice('Liên kết bị từ chối: chỉ cho phép đường dẫn trong phạm vi mạng nội bộ.')
      return
    }
    setNotice(null)
    editorRef.current?.focus()
    restoreSelection()
    document.execCommand('createLink', false, url)
    emitChange()
  }
  function handleUnlink() {
    editorRef.current?.focus()
    document.execCommand('unlink')
    emitChange()
  }

  // ---- Tai anh / video len (server noi bo) ---------------------------
  async function uploadAndInsert(file: File, kind: 'image' | 'video') {
    setNotice(null)
    const ext = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`
    const allowed = kind === 'image' ? IMAGE_EXTENSIONS : VIDEO_EXTENSIONS
    const maxMb = kind === 'image' ? MAX_IMAGE_MB : MAX_VIDEO_MB
    if (!allowed.includes(ext)) {
      setNotice(
        `Định dạng '${ext}' không được phép. Chỉ chấp nhận ${
          kind === 'image' ? 'ảnh' : 'video'
        }: ${allowed.join(', ')}`,
      )
      return
    }
    if (file.size > maxMb * 1024 * 1024) {
      setNotice(`${kind === 'image' ? 'Ảnh' : 'Video'} vượt quá giới hạn ${maxMb} MB`)
      return
    }
    setUploading(true)
    try {
      const result = await uploadsApi.upload(file)
      if (kind === 'image') insertImageAtCursor(result.url)
      else insertVideoAtCursor(result.url)
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : 'Tải tệp lên thất bại')
    } finally {
      setUploading(false)
    }
  }

  function handlePickImage() {
    saveSelection()
    fileInputRef.current?.click()
  }
  function handlePickVideo() {
    saveSelection()
    videoInputRef.current?.click()
  }
  function handleImageChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (file) void uploadAndInsert(file, 'image')
  }
  function handleVideoChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (file) void uploadAndInsert(file, 'video')
  }

  function handlePaste(e: ClipboardEvent<HTMLDivElement>) {
    const dt = e.clipboardData
    if (!dt) return
    const items = dt.items
    for (let i = 0; i < (items?.length ?? 0); i += 1) {
      if (items[i].type.startsWith('image/')) {
        e.preventDefault()
        const file = items[i].getAsFile()
        saveSelection()
        if (file) void uploadAndInsert(file, 'image')
        return
      }
    }
    const html = dt.getData('text/html')
    const text = dt.getData('text/plain')
    if (!html && !text) return
    e.preventDefault()
    const cleaned = html ? cleanPastedHtml(html) : ''
    const out = cleaned || textToHtml(text)
    if (!out) return
    saveSelection()
    insertHtmlAtCursor(out)
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    const file = e.dataTransfer?.files?.[0]
    if (!file) return
    if (file.type.startsWith('image/')) {
      e.preventDefault()
      saveSelection()
      void uploadAndInsert(file, 'image')
    } else if (file.type.startsWith('video/')) {
      e.preventDefault()
      saveSelection()
      void uploadAndInsert(file, 'video')
    }
  }

  // ---- Lenh dinh dang -----------------------------------------------
  function exec(command: string, valueArg?: string) {
    editorRef.current?.focus()
    document.execCommand(command, false, valueArg)
    emitChange()
  }
  function execBlock(tag: string) {
    editorRef.current?.focus()
    document.execCommand('formatBlock', false, tag)
    emitChange()
  }
  function clearFormatting() {
    editorRef.current?.focus()
    document.execCommand('removeFormat')
    document.execCommand('unlink')
    emitChange()
  }

  async function handleClearAll() {
    if (disabled) return
    const ok = await confirm({
      title: 'Xoá toàn bộ nội dung',
      message: 'Toàn bộ nội dung đang soạn trong ô này sẽ bị xoá. Bạn có chắc chắn?',
      confirmText: 'Xoá hết',
    })
    if (!ok) return
    const el = editorRef.current
    if (!el) return
    flushHistory()
    el.innerHTML = EMPTY_HTML
    clearBlockSelection()
    setTableActive(false)
    el.focus()
    placeCaretAtEnd(el)
    emitChange()
  }

  function handleKeyDown(e: ReactKeyboardEvent<HTMLDivElement>) {
    const mod = e.ctrlKey || e.metaKey
    const key = e.key.toLowerCase()
    if (mod && key === 'z') {
      e.preventDefault()
      applyHistory(e.shiftKey ? 1 : -1)
      return
    }
    if (mod && key === 'y') {
      e.preventDefault()
      applyHistory(1)
      return
    }
    if (mod && key === 'k') {
      e.preventDefault()
      saveSelection()
      void handleLink()
      return
    }
    if (e.key === 'Tab') {
      e.preventDefault()
      if (closestInEditor('li')) {
        document.execCommand(e.shiftKey ? 'outdent' : 'indent')
      } else if (!e.shiftKey) {
        document.execCommand('insertText', false, '    ')
      }
      emitChange()
    }
  }

  // ---- Chon khoi (anh / video) + thanh cong cu -----------------------
  function clearBlockSelection() {
    editorRef.current
      ?.querySelectorAll('.rc-selected')
      .forEach((n) => n.classList.remove('rc-selected'))
    selectedRef.current = null
    setSelKind(null)
  }
  function selectBlock(el: HTMLElement, kind: Exclude<BlockKind, null>) {
    clearBlockSelection()
    el.classList.add('rc-selected')
    selectedRef.current = el
    setSelKind(kind)
  }
  function updateTableTools() {
    if (disabled) return
    setTableActive(!!closestInEditor('table'))
  }
  function handleBodyClick(e: ReactMouseEvent<HTMLDivElement>) {
    if (disabled) return
    const t = e.target as HTMLElement
    const img = t.closest('img') as HTMLElement | null
    const video = t.closest('video') as HTMLElement | null
    if (img && editorRef.current?.contains(img)) {
      selectBlock(img, 'image')
    } else if (video && editorRef.current?.contains(video)) {
      selectBlock(video, 'video')
    } else if (selKind) {
      clearBlockSelection()
    }
    updateTableTools()
  }

  /** Ap 1 lop kich thuoc / can le cho anh dang chon (chi giu 1 lop moi nhom). */
  function applyImgClass(group: 'size' | 'align', token: string) {
    const img = selectedRef.current
    if (!img) return
    const drop = group === 'size' ? IMG_SIZES : IMG_ALIGNS
    drop.forEach((c) => img.classList.remove(c))
    img.classList.add(token)
    if (!img.classList.contains('rc-img')) img.classList.add('rc-img')
    emitChange()
  }

  /** Di chuyen khoi (anh/video) dang chon len/xuong 1 vi tri trong bai. */
  function moveSelectedBlock(dir: -1 | 1) {
    const node = selectedRef.current
    if (!node) return
    const block = (node.closest('p, figure') as HTMLElement | null) ?? node
    const parent = block.parentElement
    if (!parent) return
    flushHistory()
    if (dir === -1 && block.previousElementSibling) {
      parent.insertBefore(block, block.previousElementSibling)
    } else if (dir === 1 && block.nextElementSibling) {
      parent.insertBefore(block.nextElementSibling, block)
    }
    ensureEditableEdges()
    emitChange()
    node.scrollIntoView({ block: 'nearest' })
  }

  async function deleteSelectedBlock() {
    const node = selectedRef.current
    if (!node) return
    const ok = await confirm({
      title: selKind === 'image' ? 'Xoá ảnh' : 'Xoá video',
      message: `Xoá ${selKind === 'image' ? 'ảnh' : 'video'} này khỏi bài viết?`,
      confirmText: 'Xoá',
    })
    if (!ok) return
    flushHistory()
    const holder = node.closest('p, figure') as HTMLElement | null
    const removeTarget =
      holder && holder !== editorRef.current && (holder.textContent || '').trim() === ''
        ? holder
        : node
    removeTarget.remove()
    clearBlockSelection()
    ensureEditableEdges()
    emitChange()
  }

  // ---- Thao tac bang -------------------------------------------------
  function currentCell(): HTMLTableCellElement | null {
    return (closestInEditor('td, th') as HTMLTableCellElement | null) ?? null
  }
  function tableOp(op: 'row-below' | 'col-right' | 'row-del' | 'col-del' | 'table-del') {
    const cell = currentCell()
    if (!cell) return
    const row = cell.parentElement as HTMLTableRowElement
    const table = cell.closest('table') as HTMLTableElement
    const colIdx = Array.from(row.cells).indexOf(cell)
    flushHistory()
    if (op === 'row-below') {
      const nr = row.cloneNode(true) as HTMLTableRowElement
      Array.from(nr.cells).forEach((c) => {
        c.innerHTML = '&nbsp;'
      })
      row.after(nr)
    } else if (op === 'col-right') {
      Array.from(table.rows).forEach((r) => {
        const ref = r.cells[colIdx]
        const isHead = ref?.tagName === 'TH'
        const cellNew = document.createElement(isHead ? 'th' : 'td')
        cellNew.innerHTML = isHead ? 'Cột' : '&nbsp;'
        if (ref) ref.after(cellNew)
        else r.appendChild(cellNew)
      })
    } else if (op === 'row-del') {
      if (table.rows.length > 1) row.remove()
    } else if (op === 'col-del') {
      Array.from(table.rows).forEach((r) => {
        if (r.cells.length > 1) r.deleteCell(colIdx)
      })
    } else if (op === 'table-del') {
      const wrap = table.closest('p')
      const target = wrap && (wrap.textContent || '').trim() === '' ? wrap : table
      target.remove()
      setTableActive(false)
    }
    ensureEditableEdges()
    emitChange()
    updateTableTools()
  }

  const stopFocusSteal = (e: ReactMouseEvent) => e.preventDefault()

  return (
    <div
      className={`rich-editor${disabled ? ' rich-editor-disabled' : ''}${
        expanded ? ' rich-editor-expanded' : ''
      }`}
    >
      <div className="rich-editor-toolbar" onMouseDown={stopFocusSteal}>
        <button
          type="button"
          onClick={() => applyHistory(-1)}
          title="Hoàn tác (Ctrl+Z)"
          disabled={disabled || !hist.undo}
        >
          <Icon name="undo" size={13} />
        </button>
        <button
          type="button"
          onClick={() => applyHistory(1)}
          title="Làm lại (Ctrl+Y)"
          disabled={disabled || !hist.redo}
        >
          <span className="rc-flip">
            <Icon name="undo" size={13} />
          </span>
        </button>

        <span className="rich-editor-sep" />

        <button type="button" onClick={() => exec('bold')} title="In đậm (Ctrl+B)" disabled={disabled}>
          <b>B</b>
        </button>
        <button
          type="button"
          onClick={() => exec('italic')}
          title="In nghiêng (Ctrl+I)"
          disabled={disabled}
        >
          <i>I</i>
        </button>
        <button
          type="button"
          onClick={() => exec('underline')}
          title="Gạch chân (Ctrl+U)"
          disabled={disabled}
        >
          <u>U</u>
        </button>
        <button
          type="button"
          onClick={() => exec('strikeThrough')}
          title="Gạch ngang chữ"
          disabled={disabled}
        >
          <s>S</s>
        </button>
        <button
          type="button"
          onClick={clearFormatting}
          title="Xoá định dạng đoạn đang bôi đen"
          disabled={disabled}
        >
          <span style={{ textDecoration: 'line-through' }}>A</span>
        </button>

        <span className="rich-editor-sep" />

        <button type="button" onClick={() => execBlock('h2')} title="Tiêu đề lớn (H2)" disabled={disabled}>
          <b>H2</b>
        </button>
        <button type="button" onClick={() => execBlock('h3')} title="Tiêu đề nhỏ (H3)" disabled={disabled}>
          <b>H3</b>
        </button>
        <button type="button" onClick={() => execBlock('p')} title="Đoạn văn thường" disabled={disabled}>
          ¶
        </button>
        <button
          type="button"
          onClick={() => execBlock('blockquote')}
          title="Trích dẫn"
          disabled={disabled}
        >
          &ldquo; &rdquo;
        </button>
        <button
          type="button"
          onClick={() => exec('insertUnorderedList')}
          title="Danh sách gạch đầu dòng"
          disabled={disabled}
        >
          ≡
        </button>
        <button
          type="button"
          onClick={() => exec('insertOrderedList')}
          title="Danh sách đánh số"
          disabled={disabled}
        >
          1.
        </button>
        <button
          type="button"
          onMouseDown={(e) => {
            e.preventDefault()
            saveSelection()
          }}
          onClick={insertHr}
          title="Đường kẻ ngang"
          disabled={disabled}
        >
          ―
        </button>

        <span className="rich-editor-sep" />

        <button type="button" onClick={() => exec('justifyLeft')} title="Canh trái" disabled={disabled}>
          ⬅
        </button>
        <button
          type="button"
          onClick={() => exec('justifyCenter')}
          title="Canh giữa"
          disabled={disabled}
        >
          ⬌
        </button>
        <button type="button" onClick={() => exec('justifyRight')} title="Canh phải" disabled={disabled}>
          ➡
        </button>

        <span className="rich-editor-sep" />

        <button
          type="button"
          onMouseDown={(e) => {
            e.preventDefault()
            saveSelection()
          }}
          onClick={handleLink}
          title="Chèn liên kết nội bộ cho đoạn đang bôi đen (Ctrl+K)"
          disabled={disabled}
        >
          <Icon name="link" size={13} />
        </button>
        <button type="button" onClick={handleUnlink} title="Bỏ liên kết" disabled={disabled}>
          <span className="rc-strike-wrap">
            <Icon name="link" size={13} />
          </span>
        </button>
        <button
          type="button"
          onMouseDown={(e) => {
            e.preventDefault()
            saveSelection()
          }}
          onClick={insertTable}
          title="Chèn bảng 3×3"
          disabled={disabled}
        >
          ▦
        </button>

        <span className="rich-editor-sep" />

        <button
          type="button"
          className="rich-editor-danger"
          onClick={handleClearAll}
          title="Xoá toàn bộ nội dung trong ô soạn"
          disabled={disabled}
        >
          <Icon name="trash" size={13} /> Xoá hết
        </button>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          title={expanded ? 'Thu gọn ô soạn' : 'Mở rộng ô soạn'}
        >
          {expanded ? 'Thu gọn' : 'Mở rộng'}
        </button>

        <span className="rich-editor-insert-group">
          <button
            type="button"
            className="rich-editor-insert"
            onClick={handlePickImage}
            disabled={disabled || uploading}
            title="Tải ảnh từ máy lên máy chủ nội bộ, chèn tại vị trí con trỏ"
          >
            <Icon name="upload" size={13} /> Ảnh
          </button>
          <button
            type="button"
            className="rich-editor-insert"
            onClick={handlePickVideo}
            disabled={disabled || uploading}
            title="Tải video từ máy lên máy chủ nội bộ, chèn tại vị trí con trỏ"
          >
            <Icon name="upload" size={13} /> Video
          </button>
        </span>

        <input ref={fileInputRef} type="file" accept={IMAGE_ACCEPT} hidden onChange={handleImageChange} />
        <input ref={videoInputRef} type="file" accept={VIDEO_ACCEPT} hidden onChange={handleVideoChange} />
      </div>

      {selKind ? (
        <div className="rich-editor-imgbar" onMouseDown={stopFocusSteal}>
          <span className="rich-editor-imgbar-label">
            {selKind === 'image' ? 'Ảnh đang chọn:' : 'Video đang chọn:'}
          </span>
          {selKind === 'image' ? (
            <>
              <span className="rich-editor-imgbar-group">
                <button type="button" onClick={() => applyImgClass('size', 'rc-w-25')} title="Nhỏ (25%)">
                  25%
                </button>
                <button type="button" onClick={() => applyImgClass('size', 'rc-w-50')} title="Vừa (50%)">
                  50%
                </button>
                <button type="button" onClick={() => applyImgClass('size', 'rc-w-75')} title="Lớn (75%)">
                  75%
                </button>
                <button
                  type="button"
                  onClick={() => applyImgClass('size', 'rc-w-100')}
                  title="Tràn khung (100%)"
                >
                  100%
                </button>
              </span>
              <span className="rich-editor-imgbar-group">
                <button type="button" onClick={() => applyImgClass('align', 'rc-left')} title="Canh trái">
                  ⬅
                </button>
                <button
                  type="button"
                  onClick={() => applyImgClass('align', 'rc-center')}
                  title="Canh giữa"
                >
                  ⬍
                </button>
                <button type="button" onClick={() => applyImgClass('align', 'rc-right')} title="Canh phải">
                  ➡
                </button>
                <button
                  type="button"
                  onClick={() => applyImgClass('align', 'rc-float-left')}
                  title="Ảnh bên trái, chữ bao bên phải"
                >
                  ⧉◀
                </button>
                <button
                  type="button"
                  onClick={() => applyImgClass('align', 'rc-float-right')}
                  title="Ảnh bên phải, chữ bao bên trái"
                >
                  ▶⧉
                </button>
              </span>
            </>
          ) : null}
          <span className="rich-editor-imgbar-group">
            <button type="button" onClick={() => moveSelectedBlock(-1)} title="Di chuyển lên trên">
              ▲ Lên
            </button>
            <button type="button" onClick={() => moveSelectedBlock(1)} title="Di chuyển xuống dưới">
              ▼ Xuống
            </button>
          </span>
          <button
            type="button"
            className="rich-editor-imgbar-del"
            onClick={deleteSelectedBlock}
            title={selKind === 'image' ? 'Xoá ảnh' : 'Xoá video'}
          >
            <Icon name="x" size={12} /> {selKind === 'image' ? 'Xoá ảnh' : 'Xoá video'}
          </button>
        </div>
      ) : null}

      {tableActive && !selKind ? (
        <div className="rich-editor-imgbar" onMouseDown={stopFocusSteal}>
          <span className="rich-editor-imgbar-label">Bảng:</span>
          <span className="rich-editor-imgbar-group">
            <button type="button" onClick={() => tableOp('row-below')} title="Thêm hàng phía dưới">
              + Hàng
            </button>
            <button type="button" onClick={() => tableOp('col-right')} title="Thêm cột bên phải">
              + Cột
            </button>
            <button type="button" onClick={() => tableOp('row-del')} title="Xoá hàng hiện tại">
              − Hàng
            </button>
            <button type="button" onClick={() => tableOp('col-del')} title="Xoá cột hiện tại">
              − Cột
            </button>
          </span>
          <button
            type="button"
            className="rich-editor-imgbar-del"
            onClick={() => tableOp('table-del')}
            title="Xoá cả bảng"
          >
            <Icon name="x" size={12} /> Xoá bảng
          </button>
        </div>
      ) : null}

      <div
        ref={editorRef}
        className="rich-editor-body"
        contentEditable={!disabled}
        role="textbox"
        aria-multiline="true"
        data-placeholder={placeholder}
        onInput={emitChange}
        onKeyDown={handleKeyDown}
        onClick={handleBodyClick}
        onBlur={() => {
          saveSelection()
          emitChange()
        }}
        onPaste={handlePaste}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        suppressContentEditableWarning
      />

      <span className="state-note">
        {uploading
          ? 'Đang tải tệp lên máy chủ nội bộ…'
          : 'Viết như một bài báo: chèn tiêu đề mục, ảnh và video ngay tại vị trí con trỏ. Dán ảnh (Ctrl+V) hoặc kéo-thả ảnh/video vào khung. Ctrl+Z để hoàn tác. Nội dung chỉ dùng tài nguyên trong mạng nội bộ.'}
        {' · '}
        <b>{counts.words}</b> từ · <b>{counts.chars}</b> ký tự
      </span>
      {notice ? (
        <span role="alert" className="form-note form-error">
          {notice}
        </span>
      ) : null}
    </div>
  )
}
