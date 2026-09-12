import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { chatsApi } from '../api/chats'
import { createChatSocket, type ChatSocketHandle } from '../api/chatSocket'
import { usersApi } from '../api/users'
import { Icon } from '../components/Icon'
import { useAuth } from '../context/AuthContext'
import { useConfirm } from '../context/ConfirmContext'
import { usePrompt } from '../context/PromptContext'
import { useToast } from '../context/ToastContext'
import {
  CHAT_GROUP_STATUS_LABELS,
  CHAT_EMOJIS,
  CHAT_QUICK_REACTIONS,
  type ChatConversation,
  type ChatMessage,
  type ChatReadReceipt,
} from '../types/chat'
import type { User } from '../types/user'
import './TinNhanPage.css'

// Máy chủ API: khi VITE_API_BASE_URL rỗng (bản phát hành 1 cổng) thì /static/...
// là đường dẫn tương đối cùng origin với trang -> giữ nguyên.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

/** Ghép tiền tố máy chủ cho tệp tĩnh (/static/chat/...); URL tuyệt đối giữ nguyên. */
function resolveAsset(url: string | null | undefined): string {
  if (!url) return ''
  return url.startsWith('/static') ? `${API_BASE}${url}` : url
}

const IMAGE_EXT_RE = /\.(jpg|jpeg|png|webp|gif)$/i
// Định dạng tệp cho phép (khớp POST /chats/{id}/messages/upload ở backend)
const DOC_ACCEPT =
  '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.mp4,.webm,.ogg,.mov,.m4v,.zip,.rar,.7z,.tar,.gz,.bz2'

// Bảng emoji quân sự & tác chiến (dùng chung ở types/chat.ts)
const EMOJIS = CHAT_EMOJIS

// Sau bao lâu không nhận tín hiệu "đang soạn tin" thì ẩn dòng báo (ms).
const TYPING_TTL_MS = 4500

function fmtTimeFriendly(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const isToday =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear()

  if (isToday) {
    return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getInitials(name: string): string {
  if (!name) return 'QN'
  const words = name.trim().split(/\s+/)
  if (words.length === 1) return words[0].substring(0, 2).toUpperCase()
  return (words[words.length - 2][0] + words[words.length - 1][0]).toUpperCase()
}

/** Chuẩn hoá 1 tin nhắn từ server: is_me tính lại theo tài khoản đang đăng nhập. */
function normalizeMsg(m: ChatMessage, myId: number | null): ChatMessage {
  return { ...m, is_me: m.sender_id === myId }
}

export function TinNhanPage() {
  const { userId, role, isAdmin } = useAuth()
  const toast = useToast()
  const confirm = useConfirm()
  const prompt = usePrompt()

  const isCommander = role !== null && role <= 3
  // Role 0-1 (Quản trị hệ thống, Lữ trưởng - Chính uỷ) mới được duyệt nhóm chờ.
  const isApprover = role !== null && role <= 1

  // State hội thoại — nạp hoàn toàn từ máy chủ (không có dữ liệu mẫu)
  const [conversations, setConversations] = useState<ChatConversation[]>([])
  const [archivedConvs, setArchivedConvs] = useState<ChatConversation[]>([])
  const [selectedConvId, setSelectedConvId] = useState<number | null>(null)
  const [loadingList, setLoadingList] = useState(true)

  // Nhóm chờ duyệt (chỉ nạp cho người có quyền duyệt)
  const [pendingGroups, setPendingGroups] = useState<ChatConversation[]>([])
  const [showPending, setShowPending] = useState(true)

  // Bộ lọc bên trái (5 tabs)
  const [tabFilter, setTabFilter] = useState<'all' | 'direct' | 'group' | 'unread' | 'archived'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // State tin nhắn
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [isUrgent, setIsUrgent] = useState(false)
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)

  // v8.1.0 — tương tác tin nhắn
  const [replyingTo, setReplyingTo] = useState<ChatMessage | null>(null)
  const [editing, setEditing] = useState<{ id: number; text: string } | null>(null)
  const [reactionPickerFor, setReactionPickerFor] = useState<number | null>(null)
  const [pinnedMsgs, setPinnedMsgs] = useState<ChatMessage[]>([])
  const [showAllPinned, setShowAllPinned] = useState(false)
  const [forwardMsg, setForwardMsg] = useState<ChatMessage | null>(null)

  // v8.1.0 — realtime nâng cao
  const [onlineUsers, setOnlineUsers] = useState<Set<number>>(new Set())
  const [typingPeers, setTypingPeers] = useState<Record<number, { name: string; ts: number }>>({})
  const [receipts, setReceipts] = useState<ChatReadReceipt[]>([])

  // v8.1.0 — tìm trong hội thoại
  const [convSearchOpen, setConvSearchOpen] = useState(false)
  const [convSearchQuery, setConvSearchQuery] = useState('')
  const [convSearchResults, setConvSearchResults] = useState<ChatMessage[]>([])
  const [convSearching, setConvSearching] = useState(false)

  // Cột 3: Collapsible Drawer
  const [showDrawer, setShowDrawer] = useState(true)
  const [renamingGroup, setRenamingGroup] = useState(false)
  const [groupNameDraft, setGroupNameDraft] = useState('')

  // Lightbox xem ảnh to
  const [lightboxImg, setLightboxImg] = useState<string | null>(null)

  // Trạng thái kênh thời gian thực (WebSocket /chats/ws)
  const [socketConnected, setSocketConnected] = useState(false)

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const imageInputRef = useRef<HTMLInputElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const sockRef = useRef<ChatSocketHandle | null>(null)

  // Hội thoại đang mở + tập id đã biết — dùng trong callback WebSocket để tránh closure cũ
  const selectedConvIdRef = useRef<number | null>(selectedConvId)
  useEffect(() => {
    selectedConvIdRef.current = selectedConvId
  }, [selectedConvId])
  const conversationIdsRef = useRef<Set<number>>(new Set())
  useEffect(() => {
    conversationIdsRef.current = new Set(conversations.map((c) => c.id))
  }, [conversations])

  // Modals
  const [showDirectModal, setShowDirectModal] = useState(false)
  const [showGroupModal, setShowGroupModal] = useState(false)
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [userSearch, setUserSearch] = useState('')

  // Form tạo nhóm
  const [groupName, setGroupName] = useState('')
  const [selectedMemberIds, setSelectedMemberIds] = useState<number[]>([])
  const [creatingGroup, setCreatingGroup] = useState(false)

  // Tải danh sách người dùng cho modal
  useEffect(() => {
    usersApi
      .list({ limit: 100, active: true })
      .then((res) => setAllUsers(res.items))
      .catch((err) => console.warn('Không tải được danh sách người dùng:', err))
  }, [])

  // Tải hội thoại từ máy chủ
  const fetchConversations = useCallback(async () => {
    setLoadingList(true)
    try {
      const data = await chatsApi.list()
      setConversations(data)
      setSelectedConvId((cur) => cur ?? data[0]?.id ?? null)
    } catch {
      toast?.error('Không tải được danh sách hội thoại')
    } finally {
      setLoadingList(false)
    }
  }, [toast])

  const fetchArchived = useCallback(async () => {
    try {
      setArchivedConvs(await chatsApi.list({ archived: true }))
    } catch {
      /* im lặng */
    }
  }, [])

  // Tải nhóm chờ duyệt (chỉ người có quyền duyệt)
  const fetchPendingGroups = useCallback(async () => {
    if (!isApprover) {
      setPendingGroups([])
      return
    }
    try {
      setPendingGroups(await chatsApi.listPendingGroups())
    } catch {
      /* im lặng — không chặn màn hình chat */
    }
  }, [isApprover])

  useEffect(() => {
    fetchConversations()
    fetchPendingGroups()
  }, [fetchConversations, fetchPendingGroups])

  useEffect(() => {
    if (tabFilter === 'archived') fetchArchived()
  }, [tabFilter, fetchArchived])

  // Khi chuyển hội thoại — nạp lịch sử tin nhắn + tin ghim + biên nhận
  useEffect(() => {
    if (!selectedConvId) {
      setMessages([])
      setPinnedMsgs([])
      setReceipts([])
      return
    }
    const cid = selectedConvId
    setLoadingMessages(true)
    setEditing(null)
    setReplyingTo(null)
    setConvSearchOpen(false)
    setConvSearchResults([])

    chatsApi
      .getMessages(cid)
      .then((res) => setMessages(res.map((m) => normalizeMsg(m, userId))))
      .catch(() => setMessages([]))
      .finally(() => setLoadingMessages(false))

    chatsApi.getPinned(cid).then(setPinnedMsgs).catch(() => setPinnedMsgs([]))
    chatsApi.getReceipts(cid).then(setReceipts).catch(() => setReceipts([]))
    chatsApi.markAsRead(cid).catch(() => {})

    // Xoá unread count khi mở
    setConversations((prev) =>
      prev.map((c) => (c.id === cid ? { ...c, unread_count: 0 } : c)),
    )
  }, [selectedConvId, userId])

  // Dọn tín hiệu "đang soạn tin" quá hạn
  useEffect(() => {
    const t = setInterval(() => {
      setTypingPeers((prev) => {
        const now = Date.now()
        const next: typeof prev = {}
        let changed = false
        for (const [k, v] of Object.entries(prev)) {
          if (now - v.ts < TYPING_TTL_MS) next[Number(k)] = v
          else changed = true
        }
        return changed ? next : prev
      })
    }, 1500)
    return () => clearInterval(t)
  }, [])

  // Kênh thời gian thực: nhận mọi sự kiện chat ngay không cần F5 / polling.
  useEffect(() => {
    if (!userId) return

    const sortByRecent = (list: ChatConversation[]) =>
      [...list].sort((a, b) => {
        const ta = new Date(a.last_message_at || a.created_at).getTime()
        const tb = new Date(b.last_message_at || b.created_at).getTime()
        return tb - ta
      })

    const patchMsg = (mid: number, patch: Partial<ChatMessage>) =>
      setMessages((prev) => prev.map((x) => (x.id === mid ? { ...x, ...patch } : x)))

    const sock = createChatSocket({
      onStatusChange: setSocketConnected,
      onEvent: (evt) => {
        const openId = selectedConvIdRef.current

        if (evt.type === 'presence') {
          setOnlineUsers((prev) => {
            const next = new Set(prev)
            if (evt.online) next.add(evt.user_id)
            else next.delete(evt.user_id)
            return next
          })
          return
        }

        if (evt.type === 'typing') {
          if (evt.conversation_id !== openId || evt.user_id === userId) return
          setTypingPeers((prev) => ({
            ...prev,
            [evt.user_id]: { name: evt.user_name, ts: Date.now() },
          }))
          return
        }

        if (evt.type === 'read') {
          if (evt.conversation_id !== openId) return
          setReceipts((prev) => {
            const rest = prev.filter((r) => r.user_id !== evt.user_id)
            return [
              ...rest,
              {
                user_id: evt.user_id,
                full_name: evt.user_name,
                last_read_message_id: evt.last_read_message_id,
                last_read_at: new Date().toISOString(),
              },
            ]
          })
          return
        }

        if (evt.type === 'message:edit') {
          if (evt.message.conversation_id === openId) {
            patchMsg(evt.message.id, normalizeMsg(evt.message, userId))
          }
          return
        }

        if (evt.type === 'message:recall') {
          if (evt.conversation_id === openId) {
            patchMsg(evt.message_id, {
              is_recalled: true,
              content: '',
              attachment_url: null,
              attachment_name: null,
              is_pinned: false,
            })
          }
          setPinnedMsgs((prev) => prev.filter((p) => p.id !== evt.message_id))
          return
        }

        if (evt.type === 'message:react') {
          if (evt.conversation_id === openId) {
            patchMsg(evt.message_id, { reactions: evt.reactions })
          }
          return
        }

        if (evt.type === 'message:pin') {
          if (evt.conversation_id === openId) {
            patchMsg(evt.message_id, { is_pinned: evt.is_pinned })
            chatsApi.getPinned(openId).then(setPinnedMsgs).catch(() => {})
          }
          return
        }

        if (evt.type !== 'message:new') return

        const m = normalizeMsg(evt.message, userId)
        const isMe = m.is_me

        if (m.conversation_id === openId) {
          setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m]))
          if (!isMe) chatsApi.markAsRead(openId).catch(() => {})
        }

        if (!conversationIdsRef.current.has(m.conversation_id)) {
          fetchConversations()
          return
        }

        setConversations((prev) =>
          sortByRecent(
            prev.map((c) => {
              if (c.id !== m.conversation_id) return c
              const bumpUnread = !isMe && m.conversation_id !== openId && m.message_type !== 'system'
              return {
                ...c,
                last_message_preview: m.content || (m.is_recalled ? 'Tin nhắn đã được thu hồi' : c.last_message_preview),
                last_message_at: m.created_at,
                unread_count: bumpUnread ? c.unread_count + 1 : c.unread_count,
              }
            }),
          ),
        )
      },
    })
    sockRef.current = sock

    return () => {
      sock.close()
      sockRef.current = null
    }
  }, [userId, fetchConversations])

  // Tự động cuộn xuống đáy
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Ô nhập tự giãn chiều cao theo nội dung (tối đa ~200px rồi cuộn trong)
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [inputText])

  // Hội thoại đang chọn
  const activeConv = useMemo(() => {
    const pool = tabFilter === 'archived' ? [...conversations, ...archivedConvs] : conversations
    return pool.find((c) => c.id === selectedConvId) || conversations[0] || null
  }, [conversations, archivedConvs, tabFilter, selectedConvId])

  const myPart = useMemo(
    () => activeConv?.participants.find((p) => p.user_id === userId) || null,
    [activeConv, userId],
  )
  const canManageGroup = Boolean(
    activeConv &&
      activeConv.type === 'group' &&
      (isCommander || myPart?.is_admin || activeConv.created_by_id === userId),
  )

  // Trạng thái online của 1 quân nhân (ưu tiên tín hiệu realtime, fallback snapshot server)
  const isUserOnline = useCallback(
    (uid: number | null | undefined, snapshot?: boolean) => {
      if (uid == null) return false
      if (onlineUsers.has(uid)) return true
      return Boolean(snapshot)
    },
    [onlineUsers],
  )

  // Danh sách tệp đính kèm trong hội thoại đang chọn
  const sharedAttachments = useMemo(() => {
    return messages.filter(
      (m) => !m.is_recalled && Boolean(m.attachment_name || m.attachment_url),
    )
  }, [messages])

  // Lọc danh sách hội thoại cột trái
  const filteredConversations = useMemo(() => {
    const base = tabFilter === 'archived' ? archivedConvs : conversations
    return base.filter((c) => {
      if (tabFilter === 'direct' && c.type !== 'direct') return false
      if (tabFilter === 'group' && c.type !== 'group') return false
      if (tabFilter === 'unread' && c.unread_count === 0) return false

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchName = (c.name || '').toLowerCase().includes(q)
        const matchPreview = (c.last_message_preview || '').toLowerCase().includes(q)
        const matchOther = c.other_user?.full_name?.toLowerCase().includes(q) || false
        return matchName || matchPreview || matchOther
      }
      return true
    })
  }, [conversations, archivedConvs, tabFilter, searchQuery])

  const typingLabel = useMemo(() => {
    const names = Object.values(typingPeers).map((v) => v.name)
    if (names.length === 0) return ''
    if (names.length === 1) return `${names[0]} đang soạn tin…`
    if (names.length === 2) return `${names[0]} và ${names[1]} đang soạn tin…`
    return `${names[0]} và ${names.length - 1} đồng chí khác đang soạn tin…`
  }, [typingPeers])

  // id tin nhắn cuối cùng của MÌNH — dùng cho hiển thị "Đã xem"
  const lastMyMsgId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].is_me && messages[i].message_type !== 'system') return messages[i].id
    }
    return 0
  }, [messages])

  const seenBy = useMemo(() => {
    if (!activeConv || !lastMyMsgId) return []
    return receipts
      .filter((r) => r.user_id !== userId && r.last_read_message_id >= lastMyMsgId)
      .map((r) => r.full_name || `#${r.user_id}`)
  }, [receipts, activeConv, lastMyMsgId, userId])

  // ------------------------------------------------------------------ Gửi tin
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!inputText.trim() || sending || !selectedConvId) return

    const rawContent = inputText.trim()
    const content = isUrgent ? `⚡ [KHẨN] ${rawContent}` : rawContent
    const replyId = replyingTo?.id ?? null

    setInputText('')
    setIsUrgent(false)
    setShowEmojiPicker(false)
    setReplyingTo(null)
    setSending(true)

    try {
      const res = await chatsApi.sendMessage(selectedConvId, {
        content,
        reply_to_id: replyId,
      })
      const m = normalizeMsg(res, userId)
      setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m]))
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedConvId
            ? { ...c, last_message_preview: content, last_message_at: new Date().toISOString() }
            : c,
        ),
      )
    } catch {
      toast?.error('Không thể gửi tin nhắn qua máy chủ')
      setInputText(rawContent)
    } finally {
      setSending(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || sending || !selectedConvId) return

    const caption = inputText.trim()
    const replyId = replyingTo?.id ?? null
    setSending(true)
    try {
      const res = await chatsApi.sendFile(selectedConvId, file, caption, replyId)
      const m = normalizeMsg(res, userId)
      setInputText('')
      setReplyingTo(null)
      setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m]))
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedConvId
            ? { ...c, last_message_preview: res.content, last_message_at: res.created_at }
            : c,
        ),
      )
    } catch {
      /* apiClient đã hiện toast lỗi */
    } finally {
      setSending(false)
    }
  }

  const handleTextChange = (v: string) => {
    setInputText(v)
    if (selectedConvId) sockRef.current?.sendTyping(selectedConvId)
  }

  // ------------------------------------------------------------------ Tương tác tin
  const applyMsgFromServer = (m: ChatMessage) => {
    const nm = normalizeMsg(m, userId)
    setMessages((prev) => prev.map((x) => (x.id === nm.id ? nm : x)))
  }

  const handleSaveEdit = async () => {
    if (!editing || !selectedConvId) return
    const text = editing.text.trim()
    if (!text) return
    try {
      const res = await chatsApi.editMessage(selectedConvId, editing.id, { content: text })
      applyMsgFromServer(res)
      setEditing(null)
    } catch {
      /* toast tự hiện */
    }
  }

  const handleRecall = async (m: ChatMessage) => {
    if (!selectedConvId) return
    const ok = await confirm({
      title: 'Thu hồi tin nhắn?',
      message: 'Nội dung tin nhắn (kèm tệp đính kèm) sẽ bị gỡ với mọi thành viên.',
      confirmText: 'Thu hồi',
      tone: 'danger',
    })
    if (!ok) return
    try {
      await chatsApi.recallMessage(selectedConvId, m.id)
      setMessages((prev) =>
        prev.map((x) =>
          x.id === m.id
            ? { ...x, is_recalled: true, content: '', attachment_url: null, attachment_name: null, is_pinned: false }
            : x,
        ),
      )
      setPinnedMsgs((prev) => prev.filter((p) => p.id !== m.id))
    } catch {
      /* toast tự hiện */
    }
  }

  const handleToggleReaction = async (m: ChatMessage, emoji: string) => {
    if (!selectedConvId) return
    setReactionPickerFor(null)
    const mine = m.reactions.find((r) => r.emoji === emoji)?.mine
    try {
      const res = mine
        ? await chatsApi.unreact(selectedConvId, m.id, emoji)
        : await chatsApi.react(selectedConvId, m.id, { emoji })
      applyMsgFromServer(res)
    } catch {
      /* toast tự hiện */
    }
  }

  const handleTogglePin = async (m: ChatMessage) => {
    if (!selectedConvId) return
    try {
      const res = await chatsApi.pinMessage(selectedConvId, m.id, { pinned: !m.is_pinned })
      applyMsgFromServer(res)
      const pinned = await chatsApi.getPinned(selectedConvId)
      setPinnedMsgs(pinned)
    } catch {
      /* toast tự hiện */
    }
  }

  const handleForward = async (targetId: number) => {
    if (!forwardMsg || !selectedConvId) return
    try {
      await chatsApi.forwardMessage(selectedConvId, forwardMsg.id, {
        target_conversation_id: targetId,
      })
      toast?.success('Đã chuyển tiếp tin nhắn')
      setForwardMsg(null)
    } catch {
      /* toast tự hiện */
    }
  }

  const jumpToMessage = (mid: number) => {
    const el = document.getElementById(`chat-msg-${mid}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.classList.add('msg-flash')
      setTimeout(() => el.classList.remove('msg-flash'), 1600)
    } else {
      toast?.info('Tin nhắn nằm ngoài phần lịch sử đang tải — hãy cuộn lên để tải thêm.')
    }
  }

  const runConvSearch = async () => {
    if (!selectedConvId || !convSearchQuery.trim()) {
      setConvSearchResults([])
      return
    }
    setConvSearching(true)
    try {
      setConvSearchResults(await chatsApi.searchInConversation(selectedConvId, convSearchQuery.trim()))
    } catch {
      setConvSearchResults([])
    } finally {
      setConvSearching(false)
    }
  }

  // ------------------------------------------------------------------ Quản trị nhóm
  const handleRenameGroup = async () => {
    if (!activeConv) return
    const name = groupNameDraft.trim()
    if (name.length < 2 || name === activeConv.name) {
      setRenamingGroup(false)
      return
    }
    try {
      const conv = await chatsApi.renameGroup(activeConv.id, { name })
      setConversations((prev) => prev.map((c) => (c.id === conv.id ? conv : c)))
      setRenamingGroup(false)
      toast?.success('Đã đổi tên nhóm')
    } catch {
      /* toast tự hiện */
    }
  }

  const handleToggleMemberAdmin = async (memberId: number, makeAdmin: boolean) => {
    if (!activeConv) return
    try {
      const conv = await chatsApi.setMemberRole(activeConv.id, memberId, { is_admin: makeAdmin })
      setConversations((prev) => prev.map((c) => (c.id === conv.id ? conv : c)))
      toast?.success(makeAdmin ? 'Đã phong quản trị viên nhóm' : 'Đã gỡ quản trị viên nhóm')
    } catch {
      /* toast tự hiện */
    }
  }

  const handleToggleMute = async () => {
    if (!activeConv) return
    try {
      await chatsApi.setMute(activeConv.id, { muted: !activeConv.is_muted })
      setConversations((prev) =>
        prev.map((c) => (c.id === activeConv.id ? { ...c, is_muted: !c.is_muted } : c)),
      )
    } catch {
      /* toast tự hiện */
    }
  }

  const handleToggleArchive = async () => {
    if (!activeConv) return
    const nextArchived = !activeConv.is_archived
    try {
      await chatsApi.setArchive(activeConv.id, { archived: nextArchived })
      toast?.success(nextArchived ? 'Đã lưu trữ hội thoại' : 'Đã bỏ lưu trữ')
      if (nextArchived) {
        setConversations((prev) => prev.filter((c) => c.id !== activeConv.id))
        setArchivedConvs((prev) => [{ ...activeConv, is_archived: true }, ...prev.filter((c) => c.id !== activeConv.id)])
        setSelectedConvId(null)
      } else {
        setArchivedConvs((prev) => prev.filter((c) => c.id !== activeConv.id))
        fetchConversations()
      }
    } catch {
      /* toast tự hiện */
    }
  }

  // ------------------------------------------------------------------ Khởi tạo / duyệt / xoá
  const handleStartDirectChat = async (targetUser: User) => {
    try {
      const conv = await chatsApi.createDirect({ recipient_id: targetUser.id })
      setConversations((prev) => (prev.some((c) => c.id === conv.id) ? prev : [conv, ...prev]))
      setSelectedConvId(conv.id)
      setShowDirectModal(false)
    } catch {
      toast?.error('Không mở được cuộc trò chuyện với đồng chí này')
    }
  }

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!groupName.trim()) return

    setCreatingGroup(true)
    try {
      const conv = await chatsApi.createGroup({
        name: groupName.trim(),
        member_ids: selectedMemberIds,
      })
      setConversations((prev) => [conv, ...prev])
      setSelectedConvId(conv.id)
      if (conv.status === 'cho_duyet') {
        toast?.info('Đã gửi yêu cầu tạo nhóm — chờ chỉ huy Lữ đoàn duyệt.')
      } else {
        toast?.success(`Đã tạo nhóm: ${conv.name}`)
      }
      setShowGroupModal(false)
      setGroupName('')
      setSelectedMemberIds([])
    } catch {
      toast?.error('Không tạo được nhóm kíp trực')
    } finally {
      setCreatingGroup(false)
    }
  }

  const handleApproveGroup = async (conv: ChatConversation) => {
    try {
      await chatsApi.reviewGroup(conv.id, { approve: true })
      toast?.success(`Đã duyệt nhóm: ${conv.name}`)
      setPendingGroups((prev) => prev.filter((g) => g.id !== conv.id))
      fetchConversations()
    } catch {
      /* toast tự hiện */
    }
  }

  const handleRejectGroup = async (conv: ChatConversation) => {
    const res = await prompt({
      title: `Từ chối nhóm "${conv.name}"`,
      message: 'Nhập lý do từ chối để người tạo nhóm biết (bắt buộc).',
      fields: [{ name: 'note', label: 'Lý do từ chối', placeholder: 'VD: Đã có nhóm tương tự...', maxLength: 500, required: true }],
      confirmText: 'Từ chối nhóm',
    })
    if (!res) return
    try {
      await chatsApi.reviewGroup(conv.id, { approve: false, note: res.note })
      toast?.success('Đã từ chối nhóm')
      setPendingGroups((prev) => prev.filter((g) => g.id !== conv.id))
      fetchConversations()
    } catch {
      /* toast tự hiện */
    }
  }

  const handleDeleteGroup = async (conv: ChatConversation) => {
    const ok = await confirm({
      title: `Xoá nhóm "${conv.name}"?`,
      message: 'Toàn bộ tin nhắn và tệp đính kèm trong nhóm sẽ bị xoá vĩnh viễn, không khôi phục được.',
      confirmText: 'Xoá nhóm',
      tone: 'danger',
    })
    if (!ok) return
    try {
      await chatsApi.deleteGroup(conv.id)
      toast?.success('Đã xoá nhóm')
      setConversations((prev) => prev.filter((c) => c.id !== conv.id))
      setPendingGroups((prev) => prev.filter((c) => c.id !== conv.id))
      setSelectedConvId((cur) => (cur === conv.id ? null : cur))
    } catch {
      /* toast tự hiện */
    }
  }

  const handleRemoveMember = async (
    conv: ChatConversation,
    member: { user_id: number; full_name?: string | null; username: string },
  ) => {
    const ok = await confirm({
      title: 'Xoá thành viên?',
      message: `Xoá ${member.full_name || member.username} khỏi nhóm "${conv.name}"?`,
      confirmText: 'Xoá khỏi nhóm',
      tone: 'danger',
    })
    if (!ok) return
    try {
      await chatsApi.removeMember(conv.id, member.user_id)
      toast?.success('Đã xoá thành viên')
      fetchConversations()
    } catch {
      /* toast tự hiện */
    }
  }

  const groupLocked = activeConv?.type === 'group' && activeConv.status !== 'da_duyet'
  const pinnedToShow = showAllPinned ? pinnedMsgs : pinnedMsgs.slice(0, 1)

  return (
    <div className="intra-chat-layout">
      {/* 1. Header ứng dụng Chat */}
      <div className="chat-app-header">
        <div className="chat-header-brand">
          <div className="chat-brand-icon">
            <Icon name="message-square" size={20} />
          </div>
          <div>
            <h2 className="chat-brand-title">
              INTRA-CHAT TÁC CHIẾN LỮ ĐOÀN 21
              <span className="chat-version-tag">MẠNG NỘI BỘ LAN</span>
            </h2>
            <p className="chat-brand-sub">
              Kênh trao đổi nghiệp vụ tác chiến, chỉ huy điều hành · Bảo mật cao · Mạng nội bộ LAN
            </p>
          </div>
        </div>

        <div className="chat-header-actions">
          <button type="button" className="btn-chat-action btn-direct" onClick={() => setShowDirectModal(true)}>
            <Icon name="user" size={13} /> + Nhắn riêng
          </button>
          <button type="button" className="btn-chat-action btn-group" onClick={() => setShowGroupModal(true)}>
            <Icon name="users" size={13} /> + Lập nhóm kíp trực
          </button>
        </div>
      </div>

      {/* 2. Thân ứng dụng 3 cột */}
      <div className="chat-body-grid">
        {/* CỘT 1: SIDEBAR DANH SÁCH HỘI THOẠI */}
        <div className="chat-sidebar">
          <div className="sidebar-header">
            <div className="search-input-wrapper">
              <span className="search-icon">
                <Icon name="search" size={14} />
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm hội thoại, đồng chí, kíp trực..."
              />
            </div>

            <div className="sidebar-filter-tabs">
              {([
                ['all', 'Tất cả'],
                ['direct', 'Trực tiếp'],
                ['group', 'Nhóm'],
                ['unread', 'Chưa đọc'],
                ['archived', 'Lưu trữ'],
              ] as const).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  className={`tab-btn ${tabFilter === key ? 'active' : ''}`}
                  onClick={() => setTabFilter(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {isApprover && pendingGroups.length > 0 && tabFilter !== 'archived' && (
            <div className="pending-groups-box">
              <button type="button" className="pending-groups-head" onClick={() => setShowPending((v) => !v)}>
                <span className="pending-caret">{showPending ? '▾' : '▸'}</span>
                <span>Nhóm chờ duyệt ({pendingGroups.length})</span>
              </button>
              {showPending &&
                pendingGroups.map((g) => (
                  <div key={g.id} className="pending-group-item">
                    <div className="pending-group-info">
                      <strong>{g.name}</strong>
                      <span>
                        {g.participants.length} đ/c ·{' '}
                        {g.participants.find((p) => p.user_id === g.created_by_id)?.full_name ||
                          `Tài khoản #${g.created_by_id}`}
                      </span>
                    </div>
                    <div className="pending-group-actions">
                      <button type="button" className="btn-approve" onClick={() => handleApproveGroup(g)}>
                        Duyệt
                      </button>
                      <button type="button" className="btn-reject" onClick={() => handleRejectGroup(g)}>
                        Từ chối
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}

          <div className="conversations-scroll">
            {loadingList ? (
              <div className="conv-empty-hint">Đang tải danh sách...</div>
            ) : filteredConversations.length === 0 ? (
              <div className="conv-empty-hint">
                {tabFilter === 'archived'
                  ? 'Chưa có hội thoại nào được lưu trữ.'
                  : 'Không có cuộc trò chuyện nào. Bấm “+ Nhắn riêng” hoặc “+ Lập nhóm kíp trực”.'}
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const active = conv.id === selectedConvId
                const isGroup = conv.type === 'group'
                const displayName = conv.name || conv.other_user?.full_name || 'Hội thoại'
                const initials = getInitials(displayName)
                const online = !isGroup && isUserOnline(conv.other_user?.user_id, conv.other_user_online)

                return (
                  <div
                    key={conv.id}
                    className={`conv-item ${active ? 'active' : ''}`}
                    onClick={() => setSelectedConvId(conv.id)}
                  >
                    <div className={`conv-avatar-box ${isGroup ? 'is-group' : 'is-direct'}`}>
                      {isGroup ? <Icon name="users" size={18} /> : initials}
                      {online && <span className="online-indicator-dot" />}
                    </div>

                    <div className="conv-info">
                      <div className="conv-row-top">
                        <span className="conv-title">
                          {displayName}
                          {conv.is_muted && <span className="conv-muted-tag" title="Đã tắt thông báo">🔕</span>}
                          {isGroup && conv.status !== 'da_duyet' && (
                            <span className={`group-status-tag is-${conv.status}`}>
                              {CHAT_GROUP_STATUS_LABELS[conv.status]}
                            </span>
                          )}
                        </span>
                        <span className="conv-time">{fmtTimeFriendly(conv.last_message_at || conv.created_at)}</span>
                      </div>
                      <div className="conv-row-bottom">
                        <p className="conv-preview">
                          {conv.status === 'tu_choi'
                            ? `Bị từ chối${conv.review_note ? `: ${conv.review_note}` : ''}`
                            : conv.status === 'cho_duyet'
                              ? 'Đang chờ chỉ huy duyệt…'
                              : conv.last_message_preview || 'Bắt đầu cuộc trao đổi...'}
                        </p>
                        {conv.unread_count > 0 && !conv.is_muted && (
                          <span className="unread-badge-pill">{conv.unread_count}</span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* CỘT 2: KHUNG CHAT CHÍNH */}
        <div className="chat-main">
          {activeConv ? (
            <>
              <div className="chat-topbar">
                <div className="chat-partner-profile">
                  <div
                    className={`topbar-avatar ${
                      activeConv.type === 'group' ? 'conv-avatar-box is-group' : 'conv-avatar-box is-direct'
                    }`}
                  >
                    {activeConv.type === 'group' ? (
                      <Icon name="users" size={18} />
                    ) : (
                      getInitials(activeConv.name || activeConv.other_user?.full_name || '')
                    )}
                  </div>
                  <div className="partner-names">
                    <h3 className="partner-main-name">
                      {activeConv.name || activeConv.other_user?.full_name}
                      {activeConv.type === 'group' ? (
                        <span className="partner-role-badge">
                          Nhóm kíp trực ({activeConv.participants.length} đ/c)
                        </span>
                      ) : (
                        <span className="partner-role-badge">
                          {activeConv.other_user?.rank ? `${activeConv.other_user.rank} · ` : ''}
                          {activeConv.other_user?.position || activeConv.other_user?.unit_name || 'Quân nhân'}
                        </span>
                      )}
                    </h3>
                    <p className="partner-status-line">
                      {activeConv.type === 'direct' ? (
                        <>
                          <span
                            className="status-dot-pulse"
                            style={
                              isUserOnline(activeConv.other_user?.user_id, activeConv.other_user_online)
                                ? undefined
                                : { background: '#94a3b8', boxShadow: 'none' }
                            }
                          />{' '}
                          {isUserOnline(activeConv.other_user?.user_id, activeConv.other_user_online)
                            ? 'Đang trực tuyến'
                            : 'Ngoại tuyến'}
                        </>
                      ) : (
                        <>
                          <span
                            className="status-dot-pulse"
                            style={socketConnected ? undefined : { background: '#94a3b8', boxShadow: 'none' }}
                          />{' '}
                          {activeConv.participants.filter((p) => isUserOnline(p.user_id, p.is_online)).length} đ/c trực tuyến
                        </>
                      )}
                    </p>
                  </div>
                </div>

                <div className="chat-topbar-tools">
                  <button
                    type="button"
                    className={`topbar-tool-btn ${convSearchOpen ? 'active' : ''}`}
                    title="Tìm trong hội thoại"
                    onClick={() => setConvSearchOpen((v) => !v)}
                  >
                    <Icon name="search" size={15} />
                  </button>
                  <button
                    type="button"
                    className={`topbar-tool-btn ${activeConv.is_muted ? 'active' : ''}`}
                    title={activeConv.is_muted ? 'Bật lại thông báo' : 'Tắt thông báo hội thoại'}
                    onClick={handleToggleMute}
                  >
                    <Icon name="eye-off" size={15} />
                  </button>
                  <button
                    type="button"
                    className={`topbar-tool-btn ${showDrawer ? 'active' : ''}`}
                    title="Thông tin hội thoại & Tệp tin"
                    onClick={() => setShowDrawer(!showDrawer)}
                  >
                    <Icon name="info" size={15} />
                  </button>
                </div>
              </div>

              {/* Thanh tin đã ghim */}
              {pinnedMsgs.length > 0 && (
                <div className="pinned-bar">
                  <Icon name="pin" size={13} />
                  <div className="pinned-bar-list">
                    {pinnedToShow.map((pm) => (
                      <button key={pm.id} type="button" className="pinned-bar-item" onClick={() => jumpToMessage(pm.id)}>
                        <strong>{pm.sender_name}:</strong> {pm.content || (pm.attachment_name ?? 'Tệp đính kèm')}
                      </button>
                    ))}
                  </div>
                  {pinnedMsgs.length > 1 && (
                    <button type="button" className="pinned-bar-toggle" onClick={() => setShowAllPinned((v) => !v)}>
                      {showAllPinned ? 'Thu gọn' : `+${pinnedMsgs.length - 1}`}
                    </button>
                  )}
                </div>
              )}

              {/* Panel tìm trong hội thoại */}
              {convSearchOpen && (
                <div className="conv-search-panel">
                  <form
                    className="conv-search-row"
                    onSubmit={(e) => {
                      e.preventDefault()
                      runConvSearch()
                    }}
                  >
                    <Icon name="search" size={13} />
                    <input
                      autoFocus
                      value={convSearchQuery}
                      onChange={(e) => setConvSearchQuery(e.target.value)}
                      placeholder="Tìm từ khoá trong hội thoại này…"
                    />
                    <button type="submit" disabled={convSearching}>
                      {convSearching ? '…' : 'Tìm'}
                    </button>
                  </form>
                  {convSearchResults.length > 0 && (
                    <div className="conv-search-results">
                      {convSearchResults.map((r) => (
                        <button key={r.id} type="button" className="conv-search-hit" onClick={() => jumpToMessage(r.id)}>
                          <span className="hit-sender">{r.sender_name}</span>
                          <span className="hit-body">{r.content}</span>
                          <span className="hit-time">{fmtTimeFriendly(r.created_at)}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  {!convSearching && convSearchQuery.trim() && convSearchResults.length === 0 && (
                    <div className="conv-search-empty">Không tìm thấy tin nhắn phù hợp.</div>
                  )}
                </div>
              )}

              {/* Vùng hiển thị tin nhắn */}
              <div className="chat-messages-area">
                {loadingMessages ? (
                  <div className="chat-area-hint">Đang tải lịch sử tin nhắn...</div>
                ) : messages.length === 0 ? (
                  <div className="chat-area-hint">Chưa có tin nhắn trong hội thoại này. Hãy gửi tin nhắn đầu tiên!</div>
                ) : (
                  messages.map((msg) => {
                    if (msg.message_type === 'system') {
                      return (
                        <div key={msg.id} id={`chat-msg-${msg.id}`} className="msg-system-row">
                          <span className="msg-system-pill">{msg.content}</span>
                        </div>
                      )
                    }

                    const isMe = msg.is_me
                    const isUrgentMsg = !msg.is_recalled && (msg.content.includes('[KHẨN]') || msg.content.includes('⚡'))
                    const canRecall = !msg.is_recalled && (isMe || canManageGroup)
                    const canEdit = isMe && !msg.is_recalled
                    const isEditing = editing?.id === msg.id

                    return (
                      <div key={msg.id} id={`chat-msg-${msg.id}`} className={`msg-row ${isMe ? 'msg-me' : 'msg-them'}`}>
                        {!isMe && <div className="msg-sender-avatar">{getInitials(msg.sender_name)}</div>}

                        <div className="msg-content-wrapper">
                          {!isMe && activeConv.type === 'group' && (
                            <span className="msg-sender-name-label">
                              {msg.sender_rank ? `${msg.sender_rank} ` : ''}
                              {msg.sender_name}
                              {msg.sender_position ? ` (${msg.sender_position})` : ''}
                            </span>
                          )}

                          <div className={`msg-bubble ${isMe ? 'bubble-me' : 'bubble-them'} ${msg.is_recalled ? 'bubble-recalled' : ''}`}>
                            {!msg.is_recalled && msg.reply_to && (
                              <button
                                type="button"
                                className="msg-quote"
                                onClick={() => jumpToMessage(msg.reply_to!.id)}
                              >
                                <span className="msg-quote-name">{msg.reply_to.sender_name}</span>
                                <span className="msg-quote-text">
                                  {msg.reply_to.is_recalled ? 'Tin nhắn đã được thu hồi' : msg.reply_to.content}
                                </span>
                              </button>
                            )}

                            {!msg.is_recalled && msg.forwarded_from && (
                              <div className="msg-forwarded-tag">
                                <Icon name="send" size={11} /> Chuyển tiếp từ {msg.forwarded_from.sender_name}
                              </div>
                            )}

                            {isUrgentMsg && <div className="msg-urgent-badge">⚡ HỎA TỐC / KHẨN</div>}

                            {msg.is_recalled ? (
                              <div className="msg-recalled-text">
                                <Icon name="undo" size={12} /> Tin nhắn đã được thu hồi
                              </div>
                            ) : isEditing ? (
                              <div className="msg-edit-box">
                                <textarea
                                  autoFocus
                                  value={editing!.text}
                                  onChange={(e) => setEditing({ id: msg.id, text: e.target.value })}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                      e.preventDefault()
                                      handleSaveEdit()
                                    }
                                    if (e.key === 'Escape') setEditing(null)
                                  }}
                                />
                                <div className="msg-edit-actions">
                                  <button type="button" onClick={() => setEditing(null)}>
                                    Huỷ
                                  </button>
                                  <button type="button" className="primary" onClick={handleSaveEdit}>
                                    Lưu
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <>
                                <div>{msg.content}</div>

                                {msg.attachment_url && !IMAGE_EXT_RE.test(msg.attachment_name || '') && (
                                  <a
                                    href={resolveAsset(msg.attachment_url)}
                                    className="attachment-card"
                                    target="_blank"
                                    rel="noreferrer"
                                    download={msg.attachment_name || undefined}
                                  >
                                    <div className="attachment-icon">
                                      <Icon name="file" size={18} />
                                    </div>
                                    <div className="attachment-info">
                                      <div className="attachment-name">{msg.attachment_name}</div>
                                      <div className="attachment-size">Tệp đính kèm · Bấm để tải</div>
                                    </div>
                                    <Icon name="download" size={15} />
                                  </a>
                                )}

                                {msg.attachment_url && IMAGE_EXT_RE.test(msg.attachment_name || '') && (
                                  <div
                                    className="attached-image-container"
                                    onClick={() => setLightboxImg(resolveAsset(msg.attachment_url))}
                                    title="Bấm để phóng to xem chi tiết"
                                  >
                                    <img src={resolveAsset(msg.attachment_url)} alt={msg.attachment_name || 'Hình ảnh'} />
                                  </div>
                                )}
                              </>
                            )}
                          </div>

                          {/* Reaction chips */}
                          {msg.reactions.length > 0 && (
                            <div className={`msg-reactions ${isMe ? 'align-end' : ''}`}>
                              {msg.reactions.map((r) => (
                                <button
                                  key={r.emoji}
                                  type="button"
                                  className={`reaction-chip ${r.mine ? 'mine' : ''}`}
                                  onClick={() => handleToggleReaction(msg, r.emoji)}
                                  title={r.mine ? 'Bấm để gỡ' : 'Bấm để thả'}
                                >
                                  {r.emoji} {r.count}
                                </button>
                              ))}
                            </div>
                          )}

                          <div className="msg-meta-row">
                            <span>{fmtTimeFriendly(msg.created_at)}</span>
                            {msg.is_edited && !msg.is_recalled && <span className="msg-edited-tag">(đã sửa)</span>}
                            {msg.is_pinned && !msg.is_recalled && <Icon name="pin" size={11} />}
                            {isMe && msg.id === lastMyMsgId && seenBy.length > 0 && (
                              <span className="msg-seen" title={`Đã xem: ${seenBy.join(', ')}`}>
                                ✓✓ Đã xem{activeConv.type === 'group' ? ` (${seenBy.length})` : ''}
                              </span>
                            )}
                          </div>

                          {/* Toolbar hover */}
                          {!msg.is_recalled && !isEditing && (
                            <div className="msg-actions">
                              <button type="button" title="Trả lời" onClick={() => setReplyingTo(msg)}>
                                <Icon name="undo" size={13} />
                              </button>
                              <button
                                type="button"
                                title="Thả cảm xúc"
                                onClick={() => setReactionPickerFor((v) => (v === msg.id ? null : msg.id))}
                              >
                                <Icon name="smile" size={13} />
                              </button>
                              <button type="button" title="Chuyển tiếp" onClick={() => setForwardMsg(msg)}>
                                <Icon name="send" size={13} />
                              </button>
                              {(canManageGroup || activeConv.type === 'direct') && (
                                <button
                                  type="button"
                                  title={msg.is_pinned ? 'Bỏ ghim' : 'Ghim tin'}
                                  className={msg.is_pinned ? 'is-on' : ''}
                                  onClick={() => handleTogglePin(msg)}
                                >
                                  <Icon name="pin" size={13} />
                                </button>
                              )}
                              {canEdit && (
                                <button
                                  type="button"
                                  title="Sửa"
                                  onClick={() => setEditing({ id: msg.id, text: msg.content })}
                                >
                                  <Icon name="edit" size={13} />
                                </button>
                              )}
                              {canRecall && (
                                <button type="button" title="Thu hồi" onClick={() => handleRecall(msg)}>
                                  <Icon name="trash" size={13} />
                                </button>
                              )}
                            </div>
                          )}

                          {reactionPickerFor === msg.id && (
                            <div className={`reaction-popover ${isMe ? 'align-end' : ''}`}>
                              {CHAT_QUICK_REACTIONS.map((emo) => (
                                <button key={emo} type="button" onClick={() => handleToggleReaction(msg, emo)}>
                                  {emo}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}
                {typingLabel && <div className="typing-indicator">{typingLabel}</div>}
                <div ref={messagesEndRef} />
              </div>

              {groupLocked ? (
                <div className={`chat-locked-notice is-${activeConv.status}`}>
                  <Icon name={activeConv.status === 'tu_choi' ? 'x' : 'clock'} size={16} />
                  {activeConv.status === 'cho_duyet' ? (
                    <span>Nhóm đang chờ chỉ huy Lữ đoàn duyệt. Chưa gửi tin nhắn / thêm thành viên được cho tới khi được duyệt.</span>
                  ) : (
                    <span>
                      Nhóm đã bị từ chối.
                      {activeConv.review_note ? ` Lý do: ${activeConv.review_note}` : ''}
                    </span>
                  )}
                </div>
              ) : (
                <div className="chat-bottom-bar">
                  {replyingTo && (
                    <div className="reply-compose-chip">
                      <div className="reply-compose-body">
                        <span className="reply-compose-name">Đang trả lời {replyingTo.sender_name}</span>
                        <span className="reply-compose-text">
                          {replyingTo.is_recalled ? 'Tin nhắn đã được thu hồi' : replyingTo.content}
                        </span>
                      </div>
                      <button type="button" onClick={() => setReplyingTo(null)}>
                        <Icon name="x" size={14} />
                      </button>
                    </div>
                  )}

                  {showEmojiPicker && (
                    <div className="emoji-popover">
                      {EMOJIS.map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          className="emoji-btn"
                          onClick={() => {
                            setInputText((prev) => prev + emoji)
                            setShowEmojiPicker(false)
                          }}
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="chat-input-toolbar">
                    <input type="file" ref={fileInputRef} accept={DOC_ACCEPT} style={{ display: 'none' }} onChange={handleFileUpload} />
                    <button
                      type="button"
                      className="toolbar-btn"
                      title="Gửi tệp tài liệu / video"
                      disabled={sending || !selectedConvId}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Icon name="paperclip" size={15} /> Tệp
                    </button>

                    <input type="file" accept="image/*" ref={imageInputRef} style={{ display: 'none' }} onChange={handleFileUpload} />
                    <button
                      type="button"
                      className="toolbar-btn"
                      title="Gửi hình ảnh / sơ đồ"
                      disabled={sending || !selectedConvId}
                      onClick={() => imageInputRef.current?.click()}
                    >
                      <Icon name="image" size={15} /> Ảnh
                    </button>

                    <button
                      type="button"
                      className="toolbar-btn"
                      title="Biểu tượng cảm xúc & biểu tượng quân sự"
                      onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                    >
                      <Icon name="smile" size={15} /> Biểu cảm
                    </button>

                    <button
                      type="button"
                      className={`toolbar-btn btn-urgent ${isUrgent ? 'is-urgent' : ''}`}
                      onClick={() => setIsUrgent(!isUrgent)}
                      title="Gắn cờ mức độ ưu tiên: Khẩn / Hỏa tốc"
                    >
                      {isUrgent ? '⚡ MỨC ĐỘ: KHẨN' : 'Mức độ: Thường'}
                    </button>
                  </div>

                  <form onSubmit={handleSendMessage} className="chat-input-row">
                    <textarea
                      ref={textareaRef}
                      rows={2}
                      value={inputText}
                      onChange={(e) => handleTextChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendMessage()
                        }
                      }}
                      placeholder={
                        isUrgent
                          ? '⚡ [KHẨN] Nhập mệnh lệnh / báo cáo hỏa tốc (Enter để gửi)...'
                          : 'Nhập tin nhắn tác chiến, trao đổi công việc (Enter gửi, Shift+Enter xuống dòng)...'
                      }
                      className="chat-input-textarea"
                    />
                    <button type="submit" disabled={sending || !inputText.trim()} className="btn-chat-send">
                      <Icon name="send" size={16} /> Gửi
                    </button>
                  </form>
                </div>
              )}
            </>
          ) : (
            <div className="chat-area-hint" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {loadingList ? 'Đang tải...' : 'Chọn cuộc trò chuyện bên trái, hoặc tạo cuộc trò chuyện mới để bắt đầu'}
            </div>
          )}
        </div>

        {/* CỘT 3: DRAWER */}
        {showDrawer && activeConv && (
          <div className="chat-drawer">
            <div className="drawer-header">
              <h4>Thông tin hội thoại</h4>
              <button type="button" className="btn-close-drawer" onClick={() => setShowDrawer(false)}>
                <Icon name="x" size={16} />
              </button>
            </div>

            <div className="drawer-profile-card">
              <div
                className={`drawer-big-avatar ${
                  activeConv.type === 'group' ? 'conv-avatar-box is-group' : 'conv-avatar-box is-direct'
                }`}
              >
                {activeConv.type === 'group' ? (
                  <Icon name="users" size={26} />
                ) : (
                  getInitials(activeConv.name || activeConv.other_user?.full_name || '')
                )}
              </div>

              {activeConv.type === 'group' && canManageGroup && renamingGroup ? (
                <div className="drawer-rename-box">
                  <input
                    autoFocus
                    value={groupNameDraft}
                    onChange={(e) => setGroupNameDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRenameGroup()
                      if (e.key === 'Escape') setRenamingGroup(false)
                    }}
                  />
                  <button type="button" onClick={handleRenameGroup}>
                    Lưu
                  </button>
                  <button type="button" onClick={() => setRenamingGroup(false)}>
                    Huỷ
                  </button>
                </div>
              ) : (
                <h3 className="drawer-profile-name">
                  {activeConv.name || activeConv.other_user?.full_name}
                  {activeConv.type === 'group' && canManageGroup && (
                    <button
                      type="button"
                      className="drawer-rename-btn"
                      title="Đổi tên nhóm"
                      onClick={() => {
                        setGroupNameDraft(activeConv.name || '')
                        setRenamingGroup(true)
                      }}
                    >
                      <Icon name="edit" size={13} />
                    </button>
                  )}
                </h3>
              )}

              <p className="drawer-profile-sub">
                {activeConv.type === 'group'
                  ? `Nhóm kíp trực tác chiến · ${activeConv.participants.length} thành viên`
                  : `${activeConv.other_user?.rank || ''} ${activeConv.other_user?.position || ''} · ${activeConv.other_user?.unit_name || 'Lữ đoàn 21'}`}
              </p>
              <span className="drawer-security-tag">🔒 MẬT - MẠNG QUÂN SỰ LAN NỘI BỘ</span>

              <div className="drawer-quick-actions">
                <button type="button" className={activeConv.is_muted ? 'on' : ''} onClick={handleToggleMute}>
                  <Icon name="eye-off" size={13} /> {activeConv.is_muted ? 'Bật thông báo' : 'Tắt thông báo'}
                </button>
                <button type="button" className={activeConv.is_archived ? 'on' : ''} onClick={handleToggleArchive}>
                  <Icon name="layers" size={13} /> {activeConv.is_archived ? 'Bỏ lưu trữ' : 'Lưu trữ'}
                </button>
              </div>
            </div>

            {activeConv.type === 'group' && (
              <div className="drawer-section">
                <div className="drawer-section-title">
                  <span>Thành viên ({activeConv.participants.length})</span>
                </div>
                <div>
                  {activeConv.participants.map((member) => {
                    const isCreator = member.user_id === activeConv.created_by_id
                    const canRemove =
                      (userId === activeConv.created_by_id || isAdmin) && member.user_id !== userId && !isCreator
                    const canToggleAdmin =
                      (isCommander || userId === activeConv.created_by_id) && !isCreator && member.user_id !== userId
                    return (
                      <div key={member.user_id} className="drawer-member-item">
                        <div className="member-mini-avatar">
                          {getInitials(member.full_name || member.username)}
                          {isUserOnline(member.user_id, member.is_online) && <span className="member-online-dot" />}
                        </div>
                        <div className="member-detail">
                          <div className="member-name">
                            {member.rank ? `${member.rank} ` : ''}
                            {member.full_name || member.username}
                            {isCreator && <span className="member-owner-tag">Người tạo</span>}
                            {!isCreator && member.is_admin && <span className="member-admin-tag">QTV</span>}
                          </div>
                          <div className="member-role-title">
                            {member.position || member.unit_name || 'Thành viên kíp trực'}
                          </div>
                        </div>
                        {canToggleAdmin && (
                          <button
                            type="button"
                            className="member-admin-btn"
                            title={member.is_admin ? 'Gỡ quản trị viên' : 'Phong quản trị viên'}
                            onClick={() => handleToggleMemberAdmin(member.user_id, !member.is_admin)}
                          >
                            <Icon name="shield" size={13} />
                          </button>
                        )}
                        {canRemove && (
                          <button
                            type="button"
                            className="member-remove-btn"
                            title="Xoá khỏi nhóm"
                            onClick={() => handleRemoveMember(activeConv, member)}
                          >
                            <Icon name="x" size={14} />
                          </button>
                        )}
                      </div>
                    )
                  })}
                </div>

                {(userId === activeConv.created_by_id || isAdmin) && (
                  <button type="button" className="drawer-delete-group-btn" onClick={() => handleDeleteGroup(activeConv)}>
                    <Icon name="trash" size={14} /> Xoá nhóm (xoá cả tin nhắn &amp; tệp)
                  </button>
                )}
              </div>
            )}

            <div className="drawer-section">
              <div className="drawer-section-title">
                <span>Tệp tin đã gửi ({sharedAttachments.length})</span>
              </div>
              <div>
                {sharedAttachments.length === 0 ? (
                  <div className="drawer-empty">Chưa có tệp tài liệu nào được gửi</div>
                ) : (
                  sharedAttachments.map((att) => {
                    const isImage = IMAGE_EXT_RE.test(att.attachment_name || '')
                    const url = resolveAsset(att.attachment_url)
                    return (
                      <a
                        key={att.id}
                        href={url}
                        className="drawer-file-item"
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => {
                          if (isImage) {
                            e.preventDefault()
                            setLightboxImg(url)
                          }
                        }}
                      >
                        <span className="drawer-file-icon">
                          <Icon name={isImage ? 'image' : 'file'} size={15} />
                        </span>
                        <span className="drawer-file-name">{att.attachment_name}</span>
                      </a>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MODALS */}
      {showDirectModal && (
        <div className="chat-modal-backdrop">
          <div className="chat-modal-card">
            <div className="chat-modal-head">
              <h3>Chọn Quân nhân để nhắn tin 1-1</h3>
              <button type="button" onClick={() => setShowDirectModal(false)}>
                <Icon name="x" size={18} />
              </button>
            </div>

            <div className="search-input-wrapper" style={{ marginBottom: '12px' }}>
              <span className="search-icon">
                <Icon name="search" size={14} />
              </span>
              <input
                type="text"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                placeholder="Tìm kiếm theo họ tên, chức danh, đơn vị..."
              />
            </div>

            <div className="chat-modal-userlist">
              {allUsers
                .filter((u) => u.id !== userId)
                .filter((u) => {
                  if (!userSearch.trim()) return true
                  const q = userSearch.toLowerCase()
                  return (
                    (u.full_name || '').toLowerCase().includes(q) ||
                    (u.position || '').toLowerCase().includes(q) ||
                    (u.rank || '').toLowerCase().includes(q)
                  )
                })
                .map((u) => (
                  <div key={u.id} className="chat-modal-userrow" onClick={() => handleStartDirectChat(u)}>
                    <div className="member-mini-avatar">{getInitials(u.full_name || u.username)}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="userrow-name">
                        {u.rank ? `${u.rank} ` : ''}
                        {u.full_name}
                      </div>
                      <div className="userrow-sub">
                        {u.position || '—'} · {u.unit_name || 'Lữ đoàn 21'}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {showGroupModal && (
        <div className="chat-modal-backdrop">
          <div className="chat-modal-card">
            <div className="chat-modal-head">
              <h3>Lập Nhóm Kíp trực / Nhóm Tác chiến</h3>
              <button type="button" onClick={() => setShowGroupModal(false)}>
                <Icon name="x" size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateGroup}>
              <label className="chat-modal-label">Tên nhóm kíp trực / công tác:</label>
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="VD: Kíp trực SSCĐ Tiểu đoàn 1, Kíp kỹ thuật..."
                required
                className="chat-modal-input"
              />

              <label className="chat-modal-label">Chọn các đồng chí tham gia nhóm:</label>
              <div className="chat-modal-memberpick">
                {allUsers
                  .filter((u) => u.id !== userId)
                  .map((u) => (
                    <label key={u.id} className="chat-modal-memberopt">
                      <input
                        type="checkbox"
                        checked={selectedMemberIds.includes(u.id)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedMemberIds((prev) => [...prev, u.id])
                          else setSelectedMemberIds((prev) => prev.filter((id) => id !== u.id))
                        }}
                      />
                      <span>
                        <strong>
                          {u.rank ? `${u.rank} ` : ''}
                          {u.full_name}
                        </strong>{' '}
                        ({u.position || u.unit_name})
                      </span>
                    </label>
                  ))}
              </div>

              <div className="chat-modal-foot">
                <button type="button" onClick={() => setShowGroupModal(false)} className="btn-modal-cancel">
                  Huỷ
                </button>
                <button type="submit" disabled={creatingGroup || !groupName.trim()} className="btn-chat-send">
                  {creatingGroup ? 'Đang tạo...' : 'Tạo nhóm ngay'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {forwardMsg && (
        <div className="chat-modal-backdrop">
          <div className="chat-modal-card">
            <div className="chat-modal-head">
              <h3>Chuyển tiếp tin nhắn</h3>
              <button type="button" onClick={() => setForwardMsg(null)}>
                <Icon name="x" size={18} />
              </button>
            </div>
            <div className="forward-preview">
              <strong>{forwardMsg.sender_name}:</strong> {forwardMsg.content || forwardMsg.attachment_name}
            </div>
            <div className="chat-modal-userlist">
              {conversations
                .filter((c) => c.id !== selectedConvId && !(c.type === 'group' && c.status !== 'da_duyet'))
                .map((c) => (
                  <div key={c.id} className="chat-modal-userrow" onClick={() => handleForward(c.id)}>
                    <div className={`conv-avatar-box ${c.type === 'group' ? 'is-group' : 'is-direct'}`}>
                      {c.type === 'group' ? <Icon name="users" size={16} /> : getInitials(c.name || c.other_user?.full_name || '')}
                    </div>
                    <div className="userrow-name">{c.name || c.other_user?.full_name || 'Hội thoại'}</div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {lightboxImg && (
        <div className="lightbox-modal" onClick={() => setLightboxImg(null)}>
          <button type="button" className="lightbox-close-btn" onClick={() => setLightboxImg(null)}>
            <Icon name="x" size={20} />
          </button>
          <img src={lightboxImg} alt="Phóng to hình ảnh" className="lightbox-img" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </div>
  )
}
