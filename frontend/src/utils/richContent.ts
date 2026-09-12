// Tien ich xu ly noi dung dang (Tin tuc, Giao duc chinh tri) co the chua HTML
// kieu trang bao: in dam/nghieng, tieu de muc, trich dan, danh sach, ANH va
// VIDEO chen dung vi tri giua bai - do RichContentEditor sinh ra.
//
// Quy uoc luu tru: duong dan file (anh / video) trong `content` LUON o dang
// TUONG DOI (`/static/...`), giong `cover_image_url`/`attachment_url` o cac
// module khac - de portable giua cac may/IP LAN. Chi doi thanh URL tuyet doi
// (kem API_BASE) luc HIEN THI (edit preview hoac render cho nguoi doc).
//
// AN TOAN MANG NOI BO: noi dung KHONG duoc keo tai nguyen tu Internet vao.
//   - KHONG cho nhung <iframe> (YouTube/Vimeo...) -> loai bo hoan toan.
//   - <img>/<video>/<source> chi chap nhan `src` noi bo (`/static/...` hoac host
//     LAN) -> src ngoai bi go bo khoi noi dung khi hien thi.
//   - <a href> chi giu lien ket noi bo (duong dan tuong doi, neo #, host LAN,
//     mailto/tel) -> lien ket ra Internet bi ha thanh van ban thuong.
import DOMPurify from 'dompurify'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

/** "/static/..." -> "{API_BASE}/static/..." - dung cho 1 URL don le (anh
 * bia, tep dinh kem...), khac voi absolutizeContentImages xu ly ca doan HTML. */
export function absolutizeStaticUrl(url: string): string {
  return url && url.startsWith('/static') ? `${API_BASE}${url}` : url
}

/** src/poster="/static/..." -> "{API_BASE}/static/..." (dung khi hien thi).
 * Ap cho <img>, <video>, <source> va thuoc tinh poster cua <video>. */
export function absolutizeContentImages(html: string): string {
  if (!html) return html
  return html.replace(/((?:src|poster)=["'])\/static\//g, `$1${API_BASE}/static/`)
}

/** Nguoc lai voi absolutizeContentImages - dung truoc khi luu xuong server. */
export function relativizeContentImages(html: string): string {
  if (!html || !API_BASE) return html
  return html.split(`${API_BASE}/static/`).join('/static/')
}

/** Anh <img> dau tien tro toi tep noi bo (`/static/...`) trong noi dung bai -
 * dung lam anh minh hoa tu dong khi tac gia chua chon anh bia rieng. Tra ve URL
 * TUYET DOI da san sang hien thi (kem API_BASE), hoac null neu bai khong co anh. */
export function firstContentImage(html: string): string | null {
  if (!html) return null
  const doc = new DOMParser().parseFromString(html, 'text/html')
  for (const img of Array.from(doc.images)) {
    const src = img.getAttribute('src') || ''
    const idx = src.indexOf('/static/')
    if (idx !== -1) return `${API_BASE}${src.slice(idx)}`
  }
  return null
}

// ---------------------------------------------------------------------------
// Kiem soat pham vi mang noi bo
// ---------------------------------------------------------------------------

/** Dai dia chi IP LAN cho phep (khop cau hinh CORS cua backend). */
const LAN_HOST_RE =
  /^(localhost|127\.0\.0\.1|\[::1\]|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})$/i

function apiBaseHost(): string {
  try {
    return new URL(API_BASE).hostname
  } catch {
    return ''
  }
}

/** Host co thuoc mang noi bo khong (host cua trang, host backend, hoac dai LAN). */
function isInternalHost(host: string): boolean {
  if (!host) return false
  if (typeof window !== 'undefined' && host === window.location.hostname) return true
  if (host === apiBaseHost()) return true
  return LAN_HOST_RE.test(host)
}

/**
 * `href` co phai lien ket noi bo khong.
 *   - Cho phep: `/duong-dan`, `#neo`, `mailto:`, `tel:`, va URL http(s) tro toi
 *     host noi bo (trang / backend / dai IP LAN).
 *   - Chan: `http(s)` ra Internet, `//host`, `javascript:`, `data:`, `file:`...
 */
export function isInternalHref(raw: string): boolean {
  const href = (raw || '').trim()
  if (!href) return false
  if (href.startsWith('//')) return false
  if (/^(#|\/)/.test(href)) return true
  if (/^(mailto:|tel:)/i.test(href)) return true
  if (/^(javascript:|data:|vbscript:|file:|blob:)/i.test(href)) return false
  try {
    const u = new URL(href, typeof window !== 'undefined' ? window.location.origin : API_BASE)
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return false
    return isInternalHost(u.hostname)
  } catch {
    return false
  }
}

/** `src` cua anh/video co tro toi tai nguyen noi bo khong (`/static`, `data:`
 * base64 anh dan truc tiep bi coi la ngoai vi -> khong cho, chi nhan file da
 * tai len server). */
export function isInternalMediaSrc(raw: string): boolean {
  const src = (raw || '').trim()
  if (!src) return false
  if (src.startsWith('/')) return true
  try {
    const u = new URL(src, typeof window !== 'undefined' ? window.location.origin : API_BASE)
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return false
    return isInternalHost(u.hostname)
  } catch {
    return false
  }
}

// ---------------------------------------------------------------------------
// Loc HTML truoc khi render
// ---------------------------------------------------------------------------

const ALLOWED_TAGS = [
  'b', 'strong', 'i', 'em', 'u', 's', 'p', 'br', 'div', 'span', 'hr',
  'ul', 'ol', 'li', 'h2', 'h3', 'h4', 'blockquote', 'a',
  'table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption',
  'img', 'figure', 'figcaption', 'video', 'source',
]
const ALLOWED_ATTR = [
  'src', 'alt', 'href', 'target', 'rel', 'title', 'class',
  // bang
  'colspan', 'rowspan', 'scope',
  // media (chi phat tep noi bo)
  'controls', 'poster', 'preload', 'muted', 'playsinline', 'loop', 'type',
  'width', 'height',
]

let hooksRegistered = false
function registerHooks(): void {
  if (hooksRegistered) return
  hooksRegistered = true
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    const el = node as Element
    const tag = el.tagName

    // Chan moi <iframe> / doi tuong nhung ngoai - khong bao gio giu lai.
    if (tag === 'IFRAME' || tag === 'OBJECT' || tag === 'EMBED') {
      el.remove()
      return
    }

    // Anh / video: chi giu neu nguon noi bo, nguoc lai go bo phan tu.
    if (tag === 'IMG' || tag === 'VIDEO' || tag === 'SOURCE') {
      const src = el.getAttribute('src') || ''
      if (src && !isInternalMediaSrc(src)) {
        el.remove()
        return
      }
      const poster = el.getAttribute('poster') || ''
      if (poster && !isInternalMediaSrc(poster)) el.removeAttribute('poster')
      if (tag === 'VIDEO') {
        el.setAttribute('controls', '')
        el.setAttribute('preload', 'metadata')
      }
      return
    }

    // Lien ket: ra Internet -> go the <a>, giu lai noi dung ben trong.
    if (tag === 'A') {
      const href = el.getAttribute('href') || ''
      if (!isInternalHref(href)) {
        const parent = el.parentNode
        if (parent) {
          while (el.firstChild) parent.insertBefore(el.firstChild, el)
          parent.removeChild(el)
        }
        return
      }
      if (/^https?:\/\//i.test(href)) {
        el.setAttribute('target', '_blank')
        el.setAttribute('rel', 'noopener noreferrer')
      }
    }
  })
}

/** Loc HTML nguoi dung nhap truoc khi render bang dangerouslySetInnerHTML -
 * chi giu the/thuoc tinh trong danh sach cho phep, loai bo script + thuoc tinh
 * su kien (onClick...) + link javascript:, chan moi <iframe> va moi tai nguyen
 * anh/video/lien ket tro ra ngoai mang noi bo. */
export function sanitizeContentHtml(html: string): string {
  registerHooks()
  return DOMPurify.sanitize(html || '', {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    FORBID_TAGS: ['iframe', 'object', 'embed', 'script', 'style'],
  })
}

/** Bo toan bo the HTML - dung cho doan trich (excerpt) o Trang chu. */
export function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || ''
}

/** Doan trich ngan gon tu noi dung HTML (dung cho danh sach bai kieu trang bao). */
export function excerptFromHtml(html: string, max = 200): string {
  const clean = stripHtml(html).replace(/\s+/g, ' ').trim()
  return clean.length > max ? `${clean.slice(0, max).replace(/[\s,.;:]+\S*$/, '')}…` : clean
}
