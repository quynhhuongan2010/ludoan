interface JwtPayload {
  sub?: string
  /** Vai trò: số nguyên 0..5 (openapi v5.x). */
  role?: number
  uid?: number
  clr?: boolean
  unit?: number | null
  dca?: boolean
  cca?: boolean
  mcp?: boolean
  adm?: boolean
  exp?: number
}

export function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const [, payload] = token.split('.')
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/'))) as JwtPayload
  } catch {
    return null
  }
}
