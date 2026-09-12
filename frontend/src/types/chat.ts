/**
 * Types cho Hệ thống Tin nhắn Tác chiến Nội bộ (Chat 1-1 & Chat Nhóm).
 * Hợp đồng: openapi.CHANGELOG.md — v7.8.0 (gốc), v7.12.0 (duyệt nhóm),
 * v8.1.0 (trả lời / sửa / thu hồi / ghim / chuyển tiếp / tin hệ thống, thả cảm
 * xúc, tìm kiếm, tắt thông báo, lưu trữ, biên nhận đã đọc, realtime nâng cao).
 */

export type ConversationType = 'direct' | 'group'

/** Trạng thái duyệt nhóm (direct luôn `da_duyet`). */
export type ChatGroupStatus = 'da_duyet' | 'cho_duyet' | 'tu_choi'

export const CHAT_GROUP_STATUS_LABELS: Record<ChatGroupStatus, string> = {
  da_duyet: 'Đã duyệt',
  cho_duyet: 'Chờ duyệt',
  tu_choi: 'Bị từ chối',
}

/** Loại tin nhắn (v8.1.0). `system` = tin hệ thống, căn giữa, không có bong bóng. */
export type ChatMessageType = 'user' | 'system'

export interface ChatParticipant {
  user_id: number
  username: string
  full_name?: string | null
  rank?: string | null
  position?: string | null
  unit_id?: number | null
  unit_name?: string | null
  is_admin: boolean
  joined_at: string
  is_online: boolean
}

/** Gộp một loại emoji trên 1 tin nhắn (v8.1.0). */
export interface ChatReaction {
  emoji: string
  count: number
  user_ids: number[]
  mine: boolean
}

/** Bản xem trước tin được trả lời / được chuyển tiếp (v8.1.0). */
export interface ChatReplyPreview {
  id: number
  sender_id: number
  sender_name: string
  content: string
  is_recalled: boolean
}

export interface ChatMessage {
  id: number
  conversation_id: number
  sender_id: number
  sender_name: string
  sender_rank?: string | null
  sender_position?: string | null
  content: string
  attachment_url?: string | null
  attachment_name?: string | null
  created_at: string
  is_me: boolean
  // v8.1.0
  message_type: ChatMessageType
  reply_to?: ChatReplyPreview | null
  forwarded_from?: ChatReplyPreview | null
  reactions: ChatReaction[]
  is_edited: boolean
  edited_at?: string | null
  is_recalled: boolean
  recalled_at?: string | null
  is_pinned: boolean
  pinned_at?: string | null
}

export interface ChatConversation {
  id: number
  type: ConversationType
  name?: string | null
  created_by_id: number
  created_at: string
  last_message_at?: string | null
  last_message_preview?: string | null
  unread_count: number
  status: ChatGroupStatus
  review_note?: string | null
  reviewed_by_id?: number | null
  participants: ChatParticipant[]
  other_user?: ChatParticipant | null
  // v8.1.0
  is_muted: boolean
  is_archived: boolean
  other_user_online: boolean
}

/** Mốc đọc của một thành viên (v8.1.0) — để hiển thị "Đã xem". */
export interface ChatReadReceipt {
  user_id: number
  full_name?: string | null
  rank?: string | null
  last_read_message_id: number
  last_read_at?: string | null
}

/** Body cho POST /chats/{id}/review. `note` bắt buộc khi `approve = false`. */
export interface GroupReviewPayload {
  approve: boolean
  note?: string
}

export interface DirectChatCreatePayload {
  recipient_id: number
}

export interface GroupChatCreatePayload {
  name: string
  member_ids: number[]
}

export interface ChatMessageCreatePayload {
  content: string
  attachment_url?: string | null
  attachment_name?: string | null
  reply_to_id?: number | null
}

export interface ChatAddMemberPayload {
  user_id: number
}

export interface ChatUnreadCountResponse {
  total_unread: number
}

// --------------------------------------------------------------- v8.1.0 payloads

export interface ChatMessageEditPayload {
  content: string
}

export interface ChatReactionPayload {
  emoji: string
}

export interface ChatMessagePinPayload {
  pinned: boolean
}

export interface ChatForwardPayload {
  target_conversation_id: number
}

export interface GroupRenamePayload {
  name: string
}

export interface MemberRolePayload {
  is_admin: boolean
}

export interface MutePayload {
  muted: boolean
}

export interface ArchivePayload {
  archived: boolean
}

/** Bảng emoji gợi ý dùng chung cho ô soạn tin + popover cảm xúc. */
export const CHAT_EMOJIS = [
  '🫡', '🚩', '🎖️', '⚡', '🤝', '👍', '👏', '🎯',
  '📋', '🛡️', '✅', '📻', '📡', '📞', '💻', '🔒', '🚨', '🇻🇳',
] as const

/** Bộ emoji rút gọn cho thanh reaction nhanh. */
export const CHAT_QUICK_REACTIONS = ['👍', '🫡', '✅', '❤️', '😮', '🎯'] as const

/**
 * Sự kiện đẩy qua WebSocket `WS /chats/ws` (hợp đồng openapi.CHANGELOG.md
 * v7.10.0, mở rộng v8.1.0). `message.is_me` từ server luôn `false` — client tự
 * tính lại theo `sender_id`.
 */
export type ChatSocketEvent =
  | { type: 'ready'; user_id: number }
  | { type: 'pong' }
  | { type: 'message:new'; message: ChatMessage }
  | { type: 'message:edit'; message: ChatMessage }
  | { type: 'message:recall'; conversation_id: number; message_id: number }
  | {
      type: 'message:react'
      conversation_id: number
      message_id: number
      reactions: ChatReaction[]
    }
  | {
      type: 'message:pin'
      conversation_id: number
      message_id: number
      is_pinned: boolean
    }
  | {
      type: 'read'
      conversation_id: number
      user_id: number
      user_name: string
      last_read_message_id: number
    }
  | {
      type: 'typing'
      conversation_id: number
      user_id: number
      user_name: string
    }
  | { type: 'presence'; user_id: number; online: boolean }
