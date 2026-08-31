export interface User {
  id: number
  username: string
  full_name: string
  role: string
  is_active: boolean
  clearance: boolean
  unit_id: number | null
  unit_name: string | null
  directive_channel_access: boolean
  command_channel_access: boolean
  is_system: boolean
  must_change_password: boolean
}

export interface UserCreate {
  username: string
  password: string
  full_name: string
  role: string
  unit_id?: number | null
  directive_channel_access?: boolean
  command_channel_access?: boolean
}

export interface ChannelAccessUpdate {
  directive_channel_access?: boolean
  command_channel_access?: boolean
}

export interface RegisterRequest {
  username: string
  password: string
  full_name: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}
