'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import IndividualDashboard from '@/components/dashboards/IndividualDashboard'
import TeamDashboard from '@/components/dashboards/TeamDashboard'
import EmployeeDashboard from '@/components/dashboards/EmployeeDashboard'
import CompanyDashboard from '@/components/dashboards/CompanyDashboard'
import DashboardSwitcher from '@/components/DashboardSwitcher'
import type { User, UserRole } from '@/contexts/AuthContext'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isDevMode, setIsDevMode] = useState(false)
  const [loading, setLoading] = useState(true)
  const [unviewedScansCount, setUnviewedScansCount] = useState(0)

  useEffect(() => {
    // Check authentication
    const storedUser = localStorage.getItem('user')
    const devMode = localStorage.getItem('devMode')

    if (!storedUser) {
      router.push('/auth/login')
      return
    }

    setUser(JSON.parse(storedUser))
    setIsDevMode(devMode === 'true')
    setLoading(false)
  }, [router])

  useEffect(() => {
    // Load unviewed scans count
    loadUnviewedScansCount()

    // Poll every 30 seconds for updates
    const interval = setInterval(loadUnviewedScansCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadUnviewedScansCount = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scans/unviewed/count`)

      if (response.ok) {
        const data = await response.json()
        setUnviewedScansCount(data.count)
      }
    } catch (err) {
      console.error('Failed to load unviewed scans count:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('devMode')
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  // Determine which dashboard to show based on organization type and user role
  const getDashboardComponent = () => {
    const { type } = user.organization
    const { role } = user

    // For companies: show different dashboards for admins/owners vs employees
    if (type === 'company') {
      if (role === 'owner' || role === 'admin') {
        return <CompanyDashboard user={user} onLogout={handleLogout} />
      } else {
        return <EmployeeDashboard user={user} onLogout={handleLogout} />
      }
    }

    // For teams: show team dashboard
    if (type === 'team') {
      return <TeamDashboard user={user} onLogout={handleLogout} />
    }

    // For individuals: show individual dashboard
    return <IndividualDashboard user={user} onLogout={handleLogout} />
  }

  const getNavLinks = () => {
    const { type } = user.organization
    const { role } = user

    const baseLinks = [
      { href: '/dashboard', label: 'Dashboard', active: true },
      { href: '/dashboard/scanner', label: 'Scanner' },
      { href: '/dashboard/repositories', label: 'Repositories' },
      { href: '/dashboard/scans', label: 'Scans' },
    ]

    // Add team/company specific links
    if (type === 'team') {
      baseLinks.push({ href: '/dashboard/team/members', label: 'Members' })
    } else if (type === 'company') {
      if (role === 'owner' || role === 'admin') {
        baseLinks.push({ href: '/dashboard/employees', label: 'Employees' })
        baseLinks.push({ href: '/dashboard/access', label: 'Access' })
      }
    }

    return baseLinks
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="flex items-center space-x-2">
                <span className="text-3xl">🪅</span>
                <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Pinata Code
                </span>
              </Link>
              <div className="hidden md:flex space-x-6">
                {getNavLinks().map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={
                      link.active
                        ? 'text-purple-600 font-medium border-b-2 border-purple-600 pb-1 relative'
                        : 'text-gray-600 hover:text-purple-600 relative'
                    }
                  >
                    {link.label}
                    {link.label === 'Scans' && unviewedScansCount > 0 && (
                      <span className="absolute -top-2 -right-4 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                        {unviewedScansCount}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {isDevMode && (
                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full">
                  DEV MODE
                </span>
              )}
              <Link href="/dashboard/settings" className="text-gray-600 hover:text-purple-600">
                Settings
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-gray-600 hover:text-red-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Render appropriate dashboard */}
      {getDashboardComponent()}

      {/* Dev Dashboard Switcher (only visible in development) */}
      <DashboardSwitcher currentUser={user} />
    </div>
  )
}
