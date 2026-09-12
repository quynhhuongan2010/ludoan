import { absolutizeContentImages, sanitizeContentHtml } from '../utils/richContent'

/** Hien thi noi dung dang (co the chua HTML: in dam/nghieng/danh sach/anh chen
 * giua bai do RichContentEditor sinh ra) - da loc XSS + doi duong dan anh
 * tuong doi thanh tuyet doi truoc khi render. */
export function RichContent({ html, className }: { html: string; className?: string }) {
  const safe = sanitizeContentHtml(absolutizeContentImages(html || ''))
  return (
    <div
      className={className ? `rich-content ${className}` : 'rich-content'}
      dangerouslySetInnerHTML={{ __html: safe }}
    />
  )
}
