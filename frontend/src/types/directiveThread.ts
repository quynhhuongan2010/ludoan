export interface DirectiveMessage {
  id: number
  thread_id: number
  sender_id: number
  sender_full_name: string
  body: string
  attachment_url: string | null
  created_at: string
}

export interface DirectiveThread {
  id: number
  unit_id: number
  unit_name: string
  title: string
  created_by_id: number
  created_by_full_name: string
  created_at: string
  last_message_at: string | null
  is_closed: boolean
  message_count: number
  unread_count: number
}

export interface DirectiveThreadDetail extends DirectiveThread {
  messages: DirectiveMessage[]
}

export interface DirectiveThreadCreate {
  unit_id?: number | null
  title: string
}
