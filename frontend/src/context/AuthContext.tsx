import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { clearToken, getStoredRole, getToken, setStoredRole, setToken } from '../api/client'
import { decodeJwtPayload } from '../api/jwt'
import { profileApi } from '../api/profile'
import { usersApi } from '../api/users'
import type { MilitaryBranch, UserPermissions } from '../types/rbac'
import type { LoginRequest, Role } from '../types/user'

interface AuthContextValue {
  isAuthenticated: boolean
  isLoading: boolean
  username: string | null
  /** Vai trò tài khoản: số nguyên 0..5 (null khi chưa đăng nhập). */
  role: Role | null
  userId: number | null
  unitId: number | null
  branch: MilitaryBranch | null
  branchLabel: string | null
  permissions: Record<string, boolean>
  hasPermission: (permKey: string) => boolean
  hasClearance: boolean
  canDirectiveChannel: boolean
  canCommandChannel: boolean
  mustChangePassword: boolean
  canEditContent: boolean
  isCommander: boolean
  isAdmin: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

interface Claims {
  username: string | null
  role: Role | null
  userId: number | null
  unitId: number | null
  clearance: boolean
  directiveChannel: boolean
  commandChannel: boolean
  mustChangePassword: boolean
}

const EMPTY_CLAIMS: Claims = {
  username: null,
  role: null,
  userId: null,
  unitId: null,
  clearance: false,
  directiveChannel: false,
  commandChannel: false,
  mustChangePassword: false,
}

function normalizeRole(value: unknown): Role | null {
  return typeof value === 'number' && value >= 0 && value <= 5 ? (value as Role) : null
}

function claimsFromStoredToken(): Claims {
  const token = getToken()
  if (!token) return EMPTY_CLAIMS
  const payload = decodeJwtPayload(token)
  if (!payload) return EMPTY_CLAIMS
  // Ưu tiên role đã lưu riêng từ response /users/login, fallback về claim trong JWT.
  const role = normalizeRole(getStoredRole()) ?? normalizeRole(payload.role)
  return {
    username: payload.sub ?? null,
    role,
    userId: payload.uid ?? null,
    unitId: payload.unit ?? null,
    clearance: Boolean(payload.clr),
    directiveChannel: Boolean(payload.dca),
    commandChannel: Boolean(payload.cca),
    mustChangePassword: Boolean(payload.mcp),
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(getToken()))
  const [claims, setClaims] = useState<Claims>(() => claimsFromStoredToken())
  const [userPermissions, setUserPermissions] = useState<UserPermissions | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const authed = Boolean(getToken())
    setIsAuthenticated(authed)
    setClaims(claimsFromStoredToken())
    if (authed) {
      profileApi
        .getPermissions()
        .then(setUserPermissions)
        .catch(() => setUserPermissions(null))
    } else {
      setUserPermissions(null)
    }
  }, [isAuthenticated])

  async function login(credentials: LoginRequest) {
    setIsLoading(true)
    try {
      const token = await usersApi.login(credentials)
      setToken(token.access_token)
      // Lưu role từ response login vào localStorage để lấy ra dùng sau này.
      setStoredRole(token.role)
      setIsAuthenticated(true)
      setClaims(claimsFromStoredToken())
      try {
        const perms = await profileApi.getPermissions()
        setUserPermissions(perms)
      } catch {
        setUserPermissions(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  function logout() {
    clearToken()
    setIsAuthenticated(false)
    setClaims(EMPTY_CLAIMS)
    setUserPermissions(null)
  }

  const role = claims.role
  // 0 = Quản trị hệ thống; 1..3 = toàn quyền chỉ huy; 4 = được đăng nội dung; 5 = chỉ xem.
  const isAdmin = role === 0
  const isCommander = role !== null && role <= 3
  const canEditContent = role !== null && role <= 4

  const hasPermission = (permKey: string): boolean => {
    if (userPermissions?.permissions && permKey in userPermissions.permissions) {
      return Boolean(userPermissions.permissions[permKey])
    }
    // Fallback nếu chưa tải xong permissions
    if (permKey === 'is_admin') return isAdmin
    if (permKey === 'is_commander') return isCommander
    if (permKey === 'publish_news') return canEditContent
    return false
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        username: claims.username,
        role,
        userId: claims.userId,
        unitId: claims.unitId,
        branch: userPermissions?.branch ?? null,
        branchLabel: userPermissions?.branch_label ?? null,
        permissions: userPermissions?.permissions ?? {},
        hasPermission,
        hasClearance: claims.clearance,
        canDirectiveChannel: claims.directiveChannel || isCommander,
        // Kenh chuyen BCH & Cap uy: gac bang quyen MAT (clearance) hoac chi huy
        canCommandChannel: claims.clearance || isCommander,
        mustChangePassword: claims.mustChangePassword,
        canEditContent,
        isCommander,
        isAdmin,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
