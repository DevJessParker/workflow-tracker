'use client'

import Link from 'next/link'
import type { User } from '@/contexts/AuthContext'

interface IndividualDashboardProps {
  user: User
  onLogout: () => void
}

export default function IndividualDashboard({ user, onLogout }: IndividualDashboardProps) {
  const plan = user.organization.plan || 'free'
  const limits = {
    free: { repos: 1, scans: 10 },
    team: { repos: 10, scans: 1000 },
    enterprise: { repos: '∞', scans: '∞' }
  }
  const currentLimits = limits[plan as keyof typeof limits] || limits.free

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user.name}!
        </h1>
        <div className="flex items-center space-x-2 text-gray-600">
          <span className="text-2xl">👤</span>
          <span>Individual Account</span>
          <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded-full uppercase">
            {plan}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">My Repositories</h3>
            <span className="text-2xl">📁</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">of {currentLimits.repos} limit</div>
          <Link
            href="/dashboard/repositories"
            className="text-xs text-purple-600 hover:text-purple-700 mt-2 inline-block"
          >
            Manage repositories →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Scans This Month</h3>
            <span className="text-2xl">🔍</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">of {currentLimits.scans} limit</div>
          <Link
            href="/dashboard/scans"
            className="text-xs text-purple-600 hover:text-purple-700 mt-2 inline-block"
          >
            View scan history →
          </Link>
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
            <h3 className="text-sm font-medium text-gray-600">Storage Used</h3>
            <span className="text-2xl">💾</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">0 MB</div>
          <div className="text-sm text-gray-500 mt-1">of 1 GB limit</div>
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

          <Link
            href="/dashboard/settings"
            className="flex items-center space-x-4 p-4 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              ⚙️
            </div>
            <div>
              <div className="font-semibold text-gray-900">Account Settings</div>
              <div className="text-sm text-gray-600">Manage your profile</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow mb-8">
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

      {/* Upgrade Banner */}
      {plan === 'free' && (
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg shadow-xl p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold mb-2">Ready to scale?</h3>
              <p className="text-purple-100">
                Upgrade to Team plan for 10 repositories and 1,000 scans per month
              </p>
            </div>
            <Link
              href="/dashboard/billing/upgrade"
              className="px-6 py-3 bg-white text-purple-600 font-semibold rounded-lg hover:shadow-xl transition-all whitespace-nowrap"
            >
              Upgrade Plan
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
