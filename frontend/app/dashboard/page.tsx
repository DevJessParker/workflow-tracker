'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface User {
  id: string
  email: string
  name: string
  role: string
  organization: {
    id: string
    name: string
    type: 'individual' | 'team' | 'company'
    plan?: string
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isDevMode, setIsDevMode] = useState(false)
  const [loading, setLoading] = useState(true)

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

  const orgTypeIcon = {
    individual: '👤',
    team: '👥',
    company: '🏢'
  }

  const planLimits = {
    free: { repos: 1, scans: 10 },
    team: { repos: 10, scans: 1000 },
    enterprise: { repos: '∞', scans: '∞' }
  }

  const currentPlan = user.organization.plan || 'free'
  const limits = planLimits[currentPlan as keyof typeof planLimits] || planLimits.free

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
                <Link href="/dashboard" className="text-purple-600 font-medium border-b-2 border-purple-600 pb-1">
                  Dashboard
                </Link>
                <Link href="/dashboard/repositories" className="text-gray-600 hover:text-purple-600">
                  Repositories
                </Link>
                <Link href="/dashboard/scans" className="text-gray-600 hover:text-purple-600">
                  Scans
                </Link>
                {user.organization.type !== 'individual' && (
                  <Link href="/dashboard/team" className="text-gray-600 hover:text-purple-600">
                    Team
                  </Link>
                )}
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

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {user.name}!
          </h1>
          <div className="flex items-center space-x-2 text-gray-600">
            <span className="text-2xl">{orgTypeIcon[user.organization.type]}</span>
            <span>{user.organization.name}</span>
            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded-full uppercase">
              {currentPlan}
            </span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">Repositories</h3>
              <span className="text-2xl">📁</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">0</div>
            <div className="text-sm text-gray-500 mt-1">of {limits.repos} limit</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">Scans This Month</h3>
              <span className="text-2xl">🔍</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">0</div>
            <div className="text-sm text-gray-500 mt-1">of {limits.scans} limit</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">Patterns Found</h3>
              <span className="text-2xl">📊</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">0</div>
            <div className="text-sm text-gray-500 mt-1">across all scans</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">
                {user.organization.type === 'individual' ? 'Account' : 'Team Members'}
              </h3>
              <span className="text-2xl">{orgTypeIcon[user.organization.type]}</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {user.organization.type === 'individual' ? '1' : '1'}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {user.organization.type === 'individual' ? 'user' : 'active users'}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Quick Actions</h2>
          </div>
          <div className="p-6 grid md:grid-cols-3 gap-4">
            <Link
              href="/dashboard/repositories/connect"
              className="flex items-center space-x-4 p-4 border-2 border-dashed border-purple-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all group"
            >
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                🔗
              </div>
              <div>
                <div className="font-semibold text-gray-900">Connect Repository</div>
                <div className="text-sm text-gray-600">Link your GitHub repo</div>
              </div>
            </Link>

            <Link
              href="/dashboard/scans/new"
              className="flex items-center space-x-4 p-4 border-2 border-dashed border-pink-300 rounded-lg hover:border-pink-500 hover:bg-pink-50 transition-all group"
            >
              <div className="w-12 h-12 bg-pink-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                🔍
              </div>
              <div>
                <div className="font-semibold text-gray-900">Run Scan</div>
                <div className="text-sm text-gray-600">Analyze your codebase</div>
              </div>
            </Link>

            {user.organization.type !== 'individual' && (
              <Link
                href="/dashboard/team/invite"
                className="flex items-center space-x-4 p-4 border-2 border-dashed border-red-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition-all group"
              >
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                  ➕
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Invite Team Member</div>
                  <div className="text-sm text-gray-600">Add collaborators</div>
                </div>
              </Link>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Recent Activity</h2>
          </div>
          <div className="p-6">
            <div className="text-center py-12 text-gray-500">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-lg mb-2">No activity yet</p>
              <p className="text-sm">Connect a repository and run your first scan to get started!</p>
            </div>
          </div>
        </div>

        {/* Upgrade Banner (for free users) */}
        {currentPlan === 'free' && (
          <div className="mt-8 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg shadow-xl p-8 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold mb-2">Ready to scale?</h3>
                <p className="text-purple-100">
                  Upgrade to Team plan for 10 repositories and 1,000 scans per month
                </p>
              </div>
              <Link
                href="/dashboard/billing/upgrade"
                className="px-6 py-3 bg-white text-purple-600 font-semibold rounded-lg hover:shadow-xl transition-all"
              >
                Upgrade to Team
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
