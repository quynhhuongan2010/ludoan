/**
 * Client WebSocket cho kênh Tin nhắn Tác chiến thời gian thực.
 *
 * Hợp đồng: openapi.CHANGELOG.md v7.10.0 (gốc), v8.1.0 (sự kiện mở rộng).
 * - Server → client: ready | message:new | message:edit | message:recall |
 *   message:react | message:pin | read | typing | presence | pong
 * - Client → server: chuỗi "ping" (heartbeat ~25s); JSON {type:'typing',conversation_id}.
 *
 * Tự nối lại (backoff luỹ thừa, tối đa 15s) khi rớt; `close()` để dừng hẳn.
 */
import type { ChatSocketEvent } from '../types/chat'
import { getToken } from './client'

// VITE_API_BASE_URL: RỖNG ở bản phát hành (backend phục vụ luôn SPA -> cùng
// origin). Chỉ có giá trị khi chạy dev tách cổng (Vite :5173 + backend :8000).
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').trim()

const HEARTBEAT_MS = 25_000
const MAX_BACKOFF_MS = 15_000

/**
 * Dựng URL WebSocket cho kênh chat thời gian thực.
 *
 * Quy tắc:
 *  - Mặc định dùng ĐÚNG host của trang đang mở (window.location) — khớp với mô
 *    hình 1 cổng: backend phục vụ luôn SPA, kể cả khi truy cập qua IP LAN,
 *    tên miền, hay tunnel ngrok/cloudflare.
 *  - Chỉ đổi host khi `VITE_API_BASE_URL` trỏ tới host khác (dev tách cổng).
 *  - Trang chạy HTTPS (ngrok, TLS) thì LUÔN dùng `wss://` — không bao giờ mở
 *    `ws://` từ trang https. Đây chính là nguyên nhân lỗi
 *    "WebSocket is closed before the connection is established": trình duyệt
 *    chặn kết nối ws:// (mixed content / insecure) trên trang https.
 */
function buildWsUrl(): string {
  const token = getToken() ?? ''
  const loc = window.location

  let host = loc.host
  if (API_BASE_URL) {
    try {
      const u = new URL(API_BASE_URL, loc.href)
      if (u.host) host = u.host
    } catch {
      /* base không hợp lệ -> giữ host của trang */
    }
  }

  const proto = loc.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${host}/chats/ws?token=${encodeURIComponent(token)}`
}

export interface ChatSocketHandle {
  /** Đóng kết nối và huỷ mọi lịch nối lại. */
  close: () => void
  /** Báo "đang soạn tin" trong một hội thoại (tự tiết lưu ~2s/lần). */
  sendTyping: (conversationId: number) => void
}

// Khoảng cách tối thiểu giữa 2 lần gửi tín hiệu "đang soạn tin" (ms).
const TYPING_THROTTLE_MS = 2_000

export interface ChatSocketOptions {
  onEvent: (evt: ChatSocketEvent) => void
  /** Báo trạng thái kết nối (true = đang mở, false = mất/đang nối lại). */
  onStatusChange?: (connected: boolean) => void
}

export function createChatSocket(opts: ChatSocketOptions): ChatSocketHandle {
  let ws: WebSocket | null = null
  let stopped = false
  let attempts = 0
  let heartbeat: ReturnType<typeof setInterval> | null = null
  let retry: ReturnType<typeof setTimeout> | null = null
  let lastTypingSentAt = 0

  const clearTimers = () => {
    if (heartbeat) {
      clearInterval(heartbeat)
      heartbeat = null
    }
    if (retry) {
      clearTimeout(retry)
      retry = null
    }
  }

  const scheduleReconnect = () => {
    if (stopped || retry) return
    attempts += 1
    const delay = Math.min(1000 * 2 ** (attempts - 1), MAX_BACKOFF_MS)
    retry = setTimeout(() => {
      retry = null
      connect()
    }, delay)
  }

  const connect = () => {
    if (stopped) return
    if (!getToken()) {
      // Chưa đăng nhập — thử lại sau, phòng khi token vừa được đặt.
      scheduleReconnect()
      return
    }

    try {
      ws = new WebSocket(buildWsUrl())
    } catch {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      attempts = 0
      opts.onStatusChange?.(true)
      heartbeat = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) ws.send('ping')
      }, HEARTBEAT_MS)
    }

    ws.onmessage = (e) => {
      let data: ChatSocketEvent
      try {
        data = JSON.parse(e.data as string) as ChatSocketEvent
      } catch {
        return
      }
      if (data && data.type === 'pong') return
      opts.onEvent(data)
    }

    ws.onclose = () => {
      clearTimers()
      opts.onStatusChange?.(false)
      scheduleReconnect()
    }

    ws.onerror = () => {
      // để onclose lo phần nối lại
      ws?.close()
    }
  }

  connect()

  return {
    close: () => {
      stopped = true
      clearTimers()
      if (ws) {
        ws.onclose = null
        ws.onerror = null
        ws.onmessage = null
        ws.onopen = null
        try {
          ws.close()
        } catch {
          /* bỏ qua */
        }
        ws = null
      }
      opts.onStatusChange?.(false)
    },
    sendTyping: (conversationId: number) => {
      const now = Date.now()
      if (now - lastTypingSentAt < TYPING_THROTTLE_MS) return
      if (ws?.readyState !== WebSocket.OPEN) return
      lastTypingSentAt = now
      try {
        ws.send(JSON.stringify({ type: 'typing', conversation_id: conversationId }))
      } catch {
        /* bỏ qua - onclose se lo phan noi lai */
      }
    },
  }
}
