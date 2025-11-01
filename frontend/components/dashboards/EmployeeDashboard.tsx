'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { User } from '@/contexts/AuthContext'

interface EmployeeDashboardProps {
  user: User
  onLogout: () => void
}

export default function EmployeeDashboard({ user, onLogout }: EmployeeDashboardProps) {
  const plan = user.organization.plan || 'enterprise'

  // Mock employee data
  const [myStats] = useState({
    assignedRepos: 3,
    scansRun: 12,
    patternsFound: 45,
    lastScanDate: '2025-10-28'
  })

  const [recentScans] = useState([
    { id: '1', repo: 'web-app', date: '2025-10-28', patterns: 15, status: 'completed' },
    { id: '2', repo: 'api-service', date: '2025-10-27', patterns: 12, status: 'completed' },
    { id: '3', repo: 'mobile-app', date: '2025-10-26', patterns: 18, status: 'completed' },
  ])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome, {user.name}
        </h1>
        <div className="flex items-center space-x-2 text-gray-600">
          <span className="text-2xl">👨‍💼</span>
          <span>{user.organization.name}</span>
          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full capitalize">
            {user.role}
          </span>
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
          <div className="text-3xl font-bold text-gray-900">{myStats.assignedRepos}</div>
          <div className="text-sm text-gray-500 mt-1">assigned to me</div>
          <Link
            href="/dashboard/repositories"
            className="text-xs text-blue-600 hover:text-blue-700 mt-2 inline-block"
          >
            View repositories →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Scans Run</h3>
            <span className="text-2xl">🔍</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{myStats.scansRun}</div>
          <div className="text-sm text-gray-500 mt-1">this month</div>
          <Link
            href="/dashboard/scans"
            className="text-xs text-blue-600 hover:text-blue-700 mt-2 inline-block"
          >
            View scan history →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Patterns Found</h3>
            <span className="text-2xl">📊</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{myStats.patternsFound}</div>
          <div className="text-sm text-gray-500 mt-1">across my scans</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Last Scan</h3>
            <span className="text-2xl">⏱️</span>
          </div>
          <div className="text-lg font-bold text-gray-900">{myStats.lastScanDate}</div>
          <div className="text-sm text-gray-500 mt-1">most recent activity</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-6 grid md:grid-cols-3 gap-4">
          <Link
            href="/dashboard/scans/new"
            className="flex items-center space-x-4 p-4 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              🔍
            </div>
            <div>
              <div className="font-semibold text-gray-900">Run Scan</div>
              <div className="text-sm text-gray-600">Analyze repository</div>
            </div>
          </Link>

          <Link
            href="/dashboard/repositories"
            className="flex items-center space-x-4 p-4 border-2 border-dashed border-purple-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all group"
          >
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              📁
            </div>
            <div>
              <div className="font-semibold text-gray-900">My Repositories</div>
              <div className="text-sm text-gray-600">View assigned repos</div>
            </div>
          </Link>

          <Link
            href="/dashboard/settings"
            className="flex items-center space-x-4 p-4 border-2 border-dashed border-green-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all group"
          >
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              ⚙️
            </div>
            <div>
              <div className="font-semibold text-gray-900">My Settings</div>
              <div className="text-sm text-gray-600">Update profile</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Scans */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">My Recent Scans</h2>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Repository</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Patterns</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentScans.map((scan) => (
                  <tr key={scan.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="font-medium text-gray-900">{scan.repo}</div>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{scan.date}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                        {scan.patterns} patterns
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full capitalize">
                        {scan.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/dashboard/scans/${scan.id}`}
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        View Results
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Company Resources */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Company Resources</h2>
        </div>
        <div className="p-6">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl mb-2">📚</div>
              <h3 className="font-semibold text-gray-900 mb-1">Documentation</h3>
              <p className="text-sm text-gray-600 mb-3">Company workflow guidelines</p>
              <a href="/docs" className="text-xs text-blue-600 hover:text-blue-700 font-medium">
                View docs →
              </a>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl mb-2">👥</div>
              <h3 className="font-semibold text-gray-900 mb-1">Team Directory</h3>
              <p className="text-sm text-gray-600 mb-3">Find colleagues and teams</p>
              <Link href="/dashboard/directory" className="text-xs text-purple-600 hover:text-purple-700 font-medium">
                Browse directory →
              </Link>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-2xl mb-2">💬</div>
              <h3 className="font-semibold text-gray-900 mb-1">Support</h3>
              <p className="text-sm text-gray-600 mb-3">Get help from IT team</p>
              <Link href="/dashboard/support" className="text-xs text-green-600 hover:text-green-700 font-medium">
                Contact support →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
