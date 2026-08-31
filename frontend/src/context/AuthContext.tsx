import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { clearToken, getToken, setToken } from '../api/client'
import { decodeJwtPayload } from '../api/jwt'
import { usersApi } from '../api/users'
import type { LoginRequest } from '../types/user'

interface AuthContextValue {
  isAuthenticated: boolean
  isLoading: boolean
  username: string | null
  role: string | null
  userId: number | null
  unitId: number | null
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
  role: string | null
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

function claimsFromStoredToken(): Claims {
  const token = getToken()
  if (!token) return EMPTY_CLAIMS
  const payload = decodeJwtPayload(token)
  if (!payload) return EMPTY_CLAIMS
  return {
    username: payload.sub ?? null,
    role: payload.role ?? null,
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
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    setIsAuthenticated(Boolean(getToken()))
    setClaims(claimsFromStoredToken())
  }, [])

  async function login(credentials: LoginRequest) {
    setIsLoading(true)
    try {
      const token = await usersApi.login(credentials)
      setToken(token.access_token)
      setIsAuthenticated(true)
      setClaims(claimsFromStoredToken())
    } finally {
      setIsLoading(false)
    }
  }

  function logout() {
    clearToken()
    setIsAuthenticated(false)
    setClaims(EMPTY_CLAIMS)
  }

  const role = claims.role
  const isAdmin = role === 'admin'
  const isCommander = role === 'commander' || isAdmin
  const canEditContent = role === 'officer' || isCommander

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        username: claims.username,
        role,
        userId: claims.userId,
        unitId: claims.unitId,
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
