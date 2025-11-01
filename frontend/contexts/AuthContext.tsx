'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface Organization {
  id: string
  name: string
  type: 'individual' | 'team' | 'company'
  plan?: string
}

interface User {
  id: string
  email: string
  name: string
  role: string
  organization: Organization
}

interface AuthContextType {
  user: User | null
  isDevMode: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [isDevMode, setIsDevMode] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in (from localStorage in dev mode)
    const storedUser = localStorage.getItem('user')
    const devMode = localStorage.getItem('devMode')

    if (storedUser) {
      setUser(JSON.parse(storedUser))
      setIsDevMode(devMode === 'true')
    }

    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    // TODO: Implement actual authentication
    // For now, this is handled by the dev bypass
    throw new Error('Not implemented - use dev bypass')
  }

  const logout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('devMode')
    setUser(null)
    setIsDevMode(false)
    router.push('/')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isDevMode,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
