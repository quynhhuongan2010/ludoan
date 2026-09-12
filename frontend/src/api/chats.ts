import { apiClient } from './client'
import type {
  ArchivePayload,
  ChatAddMemberPayload,
  ChatConversation,
  ChatForwardPayload,
  ChatMessage,
  ChatMessageCreatePayload,
  ChatMessageEditPayload,
  ChatMessagePinPayload,
  ChatReactionPayload,
  ChatReadReceipt,
  ChatUnreadCountResponse,
  DirectChatCreatePayload,
  GroupChatCreatePayload,
  GroupRenamePayload,
  GroupReviewPayload,
  MemberRolePayload,
  MutePayload,
} from '../types/chat'

// Các thao tác lặp lại liên tục trong khi chat (gửi tin, gửi tệp, đánh dấu đã
// đọc, reaction...) không hiện toast "Thao tác thành công" cho đỡ nhiễu.
const SILENT = { silent: true } as const

export const chatsApi = {
  list: (params?: { archived?: boolean }) => {
    const qs = params?.archived ? '?archived=true' : ''
    return apiClient.get<ChatConversation[]>(`/chats${qs}`)
  },

  getUnreadCount: () => {
    return apiClient.get<ChatUnreadCountResponse>('/chats/unread-count')
  },

  createDirect: (data: DirectChatCreatePayload) => {
    return apiClient.post<ChatConversation>('/chats/direct', data, SILENT)
  },

  createGroup: (data: GroupChatCreatePayload) => {
    return apiClient.post<ChatConversation>('/chats/group', data, SILENT)
  },

  /** Danh sách nhóm chờ duyệt — chỉ role 0-1 (Quản trị / Lữ trưởng - Chính uỷ), khác → 403. */
  listPendingGroups: () => {
    return apiClient.get<ChatConversation[]>('/chats/pending-groups')
  },

  /** Duyệt / từ chối nhóm chờ. `note` bắt buộc khi `approve = false`. */
  reviewGroup: (conversationId: number, data: GroupReviewPayload) => {
    return apiClient.post<ChatConversation>(`/chats/${conversationId}/review`, data)
  },

  /** Xoá cứng nhóm chat (kèm tin nhắn + tệp). Chỉ người tạo nhóm hoặc admin (role 0). */
  deleteGroup: (conversationId: number) => {
    return apiClient.delete<void>(`/chats/${conversationId}`)
  },

  /** Đổi tên nhóm — quản trị viên nhóm hoặc Ban chỉ huy. */
  renameGroup: (conversationId: number, data: GroupRenamePayload) => {
    return apiClient.patch<ChatConversation>(`/chats/${conversationId}`, data)
  },

  getMessages: (conversationId: number, params?: { skip?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    const qs = q.toString()
    return apiClient.get<ChatMessage[]>(`/chats/${conversationId}/messages${qs ? `?${qs}` : ''}`)
  },

  sendMessage: (conversationId: number, data: ChatMessageCreatePayload) => {
    return apiClient.post<ChatMessage>(`/chats/${conversationId}/messages`, data, SILENT)
  },

  /** Gửi tin nhắn kèm tệp đính kèm (ảnh / tài liệu / video). `content` là chú thích tuỳ chọn. */
  sendFile: (
    conversationId: number,
    file: File,
    content = '',
    replyToId?: number | null,
  ) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('content', content)
    if (replyToId != null) fd.append('reply_to_id', String(replyToId))
    return apiClient.postForm<ChatMessage>(`/chats/${conversationId}/messages/upload`, fd, SILENT)
  },

  /** Sửa nội dung tin nhắn (chỉ người gửi). */
  editMessage: (conversationId: number, messageId: number, data: ChatMessageEditPayload) => {
    return apiClient.patch<ChatMessage>(
      `/chats/${conversationId}/messages/${messageId}`,
      data,
      SILENT,
    )
  },

  /** Thu hồi tin nhắn (người gửi / quản trị viên nhóm / Ban chỉ huy). */
  recallMessage: (conversationId: number, messageId: number) => {
    return apiClient.delete<void>(
      `/chats/${conversationId}/messages/${messageId}`,
      SILENT,
    )
  },

  /** Thả một biểu tượng cảm xúc lên tin nhắn (idempotent). */
  react: (conversationId: number, messageId: number, data: ChatReactionPayload) => {
    return apiClient.post<ChatMessage>(
      `/chats/${conversationId}/messages/${messageId}/reactions`,
      data,
      SILENT,
    )
  },

  /** Gỡ biểu tượng cảm xúc đã thả. */
  unreact: (conversationId: number, messageId: number, emoji: string) => {
    return apiClient.delete<ChatMessage>(
      `/chats/${conversationId}/messages/${messageId}/reactions?emoji=${encodeURIComponent(emoji)}`,
      SILENT,
    )
  },

  /** Ghim / bỏ ghim tin nhắn. */
  pinMessage: (conversationId: number, messageId: number, data: ChatMessagePinPayload) => {
    return apiClient.post<ChatMessage>(
      `/chats/${conversationId}/messages/${messageId}/pin`,
      data,
    )
  },

  /** Danh sách tin nhắn đã ghim trong hội thoại. */
  getPinned: (conversationId: number) => {
    return apiClient.get<ChatMessage[]>(`/chats/${conversationId}/pinned`)
  },

  /** Chuyển tiếp tin nhắn sang hội thoại đích (thành viên cả hai). */
  forwardMessage: (conversationId: number, messageId: number, data: ChatForwardPayload) => {
    return apiClient.post<ChatMessage>(
      `/chats/${conversationId}/messages/${messageId}/forward`,
      data,
    )
  },

  /** Tìm tin nhắn trong một hội thoại. */
  searchInConversation: (
    conversationId: number,
    q: string,
    params?: { skip?: number; limit?: number },
  ) => {
    const sp = new URLSearchParams({ q })
    if (params?.skip !== undefined) sp.set('skip', String(params.skip))
    if (params?.limit !== undefined) sp.set('limit', String(params.limit))
    return apiClient.get<ChatMessage[]>(
      `/chats/${conversationId}/messages/search?${sp.toString()}`,
    )
  },

  /** Tìm tin nhắn trên mọi hội thoại người dùng tham gia. */
  searchAll: (q: string, limit = 50) => {
    const sp = new URLSearchParams({ q, limit: String(limit) })
    return apiClient.get<ChatMessage[]>(`/chats/search?${sp.toString()}`)
  },

  markAsRead: (conversationId: number) => {
    return apiClient.post<{ ok: boolean; last_read_message_id: number }>(
      `/chats/${conversationId}/read`,
      {},
      SILENT,
    )
  },

  /** Mốc đọc của từng thành viên (hiển thị "Đã xem"). */
  getReceipts: (conversationId: number) => {
    return apiClient.get<ChatReadReceipt[]>(`/chats/${conversationId}/receipts`)
  },

  /** Tắt / bật thông báo hội thoại cho chính người gọi. */
  setMute: (conversationId: number, data: MutePayload) => {
    return apiClient.post<{ ok: boolean; is_muted: boolean }>(
      `/chats/${conversationId}/mute`,
      data,
      SILENT,
    )
  },

  /** Lưu trữ / bỏ lưu trữ hội thoại cho chính người gọi. */
  setArchive: (conversationId: number, data: ArchivePayload) => {
    return apiClient.post<{ ok: boolean; is_archived: boolean }>(
      `/chats/${conversationId}/archive`,
      data,
    )
  },

  addMember: (conversationId: number, data: ChatAddMemberPayload) => {
    return apiClient.post<ChatConversation>(`/chats/${conversationId}/members`, data)
  },

  removeMember: (conversationId: number, userId: number) => {
    return apiClient.delete<{ ok: boolean }>(`/chats/${conversationId}/members/${userId}`)
  },

  /** Phong / gỡ quản trị viên nhóm — người tạo nhóm hoặc Ban chỉ huy. */
  setMemberRole: (conversationId: number, userId: number, data: MemberRolePayload) => {
    return apiClient.patch<ChatConversation>(
      `/chats/${conversationId}/members/${userId}/role`,
      data,
    )
  },
}
