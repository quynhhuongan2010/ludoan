import { useEffect, useState } from 'react'

interface SafeImageProps {
  src: string | null | undefined
  alt?: string
  /** Class cho phần tử ảnh / khung dự phòng (kích thước + bo góc do nơi gọi quyết định). */
  className?: string
  /** Cỡ biểu trưng vẽ trong khung dự phòng. */
  emblemSize?: number
}

/**
 * Ảnh đại diện "an toàn" cho Tin tức / Giáo dục chính trị.
 *
 * Khi `src` rỗng, ảnh trả 404 hoặc mất kết nối trong mạng LAN, component tự thay
 * bằng KHUNG BIỂU TRƯNG QUÂN SỰ nội bộ (SVG vẽ thẳng, không tải tài nguyên từ
 * mạng) thay vì để trình duyệt hiện icon file xám mặc định làm vỡ bố cục.
 *
 * Tỉ lệ khung ảnh (aspect-ratio) và bo góc do class ở nơi gọi quy định; ở đây
 * chỉ đảm bảo `object-fit: cover` để ảnh không méo.
 */
export function SafeImage({ src, alt = '', className, emblemSize = 52 }: SafeImageProps) {
  const [failed, setFailed] = useState(false)

  // src đổi (component được tái sử dụng cho bài khác) thì thử tải lại từ đầu.
  useEffect(() => {
    setFailed(false)
  }, [src])

  if (!src || failed) {
    return (
      <span className={`safe-img safe-img--fallback ${className ?? ''}`} aria-hidden="true">
        <EmblemMark size={emblemSize} />
      </span>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className={`safe-img ${className ?? ''}`}
      onError={() => setFailed(true)}
    />
  )
}

/** Biểu trưng dự phòng: khiên + ngôi sao, tông xanh rêu quân sự và vàng truyền thống. */
function EmblemMark({ size }: { size: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M32 4 8 12v18c0 15 10.4 24.3 24 30 13.6-5.7 24-15 24-30V12L32 4Z"
        fill="var(--primary-green, #2c6540)"
        stroke="var(--primary-dark-green, #1f4c30)"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      <path
        d="M32 17l3.7 7.6 8.3 1.2-6 5.9 1.4 8.3L32 43.2l-7.4 3.9 1.4-8.3-6-5.9 8.3-1.2L32 17Z"
        fill="var(--accent-gold, #ffcc00)"
      />
    </svg>
  )
}
