'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { User } from '@/contexts/AuthContext'

interface TeamDashboardProps {
  user: User
  onLogout: () => void
}

export default function TeamDashboard({ user, onLogout }: TeamDashboardProps) {
  const plan = user.organization.plan || 'team'
  const limits = {
    free: { repos: 1, scans: 10, members: 1 },
    team: { repos: 10, scans: 1000, members: 10 },
    enterprise: { repos: '∞', scans: '∞', members: '∞' }
  }
  const currentLimits = limits[plan as keyof typeof limits] || limits.team

  // Mock team members data
  const [teamMembers] = useState([
    { id: '1', name: user.name, email: user.email, role: user.role, status: 'active', joinedAt: '2025-01-15' },
    // Add more mock members as needed
  ])

  const isAdmin = user.role === 'owner' || user.role === 'admin'

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {user.organization.name}
        </h1>
        <div className="flex items-center space-x-2 text-gray-600">
          <span className="text-2xl">👥</span>
          <span>Team Dashboard</span>
          <span className="px-2 py-1 bg-pink-100 text-pink-800 text-xs font-semibold rounded-full uppercase">
            {plan}
          </span>
          <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded-full capitalize">
            {user.role}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Team Repositories</h3>
            <span className="text-2xl">📁</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">of {currentLimits.repos} limit</div>
          <Link
            href="/dashboard/repositories"
            className="text-xs text-pink-600 hover:text-pink-700 mt-2 inline-block"
          >
            Manage repositories →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Team Scans</h3>
            <span className="text-2xl">🔍</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">of {currentLimits.scans}/month</div>
          <Link
            href="/dashboard/scans"
            className="text-xs text-pink-600 hover:text-pink-700 mt-2 inline-block"
          >
            View all scans →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Team Members</h3>
            <span className="text-2xl">👥</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{teamMembers.length}</div>
          <div className="text-sm text-gray-500 mt-1">of {currentLimits.members} limit</div>
          {isAdmin && (
            <Link
              href="/dashboard/team/members"
              className="text-xs text-pink-600 hover:text-pink-700 mt-2 inline-block"
            >
              Manage members →
            </Link>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Patterns Found</h3>
            <span className="text-2xl">📊</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-500 mt-1">across all repos</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-6 grid md:grid-cols-4 gap-4">
          <Link
            href="/dashboard/repositories/connect"
            className="flex items-center space-x-4 p-4 border-2 border-dashed border-purple-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all group"
          >
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              🔗
            </div>
            <div>
              <div className="font-semibold text-gray-900">Connect Repo</div>
              <div className="text-sm text-gray-600">Add repository</div>
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
              <div className="text-sm text-gray-600">Analyze code</div>
            </div>
          </Link>

          {isAdmin && (
            <Link
              href="/dashboard/team/invite"
              className="flex items-center space-x-4 p-4 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
            >
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                ➕
              </div>
              <div>
                <div className="font-semibold text-gray-900">Invite Member</div>
                <div className="text-sm text-gray-600">Add teammate</div>
              </div>
            </Link>
          )}

          {isAdmin && (
            <Link
              href="/dashboard/settings"
              className="flex items-center space-x-4 p-4 border-2 border-dashed border-green-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all group"
            >
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                ⚙️
              </div>
              <div>
                <div className="font-semibold text-gray-900">Team Settings</div>
                <div className="text-sm text-gray-600">Configure team</div>
              </div>
            </Link>
          )}
        </div>
      </div>

      {/* Team Members Overview */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Team Members</h2>
          {isAdmin && (
            <Link
              href="/dashboard/team/invite"
              className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-all text-sm font-semibold"
            >
              + Invite Member
            </Link>
          )}
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Member</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Role</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Joined</th>
                  {isAdmin && <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {teamMembers.map((member) => (
                  <tr key={member.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div>
                        <div className="font-medium text-gray-900">{member.name}</div>
                        <div className="text-sm text-gray-600">{member.email}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded-full capitalize">
                        {member.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full capitalize">
                        {member.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{member.joinedAt}</td>
                    {isAdmin && (
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/dashboard/team/members/${member.id}`}
                          className="text-pink-600 hover:text-pink-700 text-sm font-medium"
                        >
                          Edit
                        </Link>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Recent Team Activity</h2>
        </div>
        <div className="p-6">
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">📭</div>
            <p className="text-lg mb-2">No activity yet</p>
            <p className="text-sm">Team activity will appear here once you start scanning repositories</p>
          </div>
        </div>
      </div>
    </div>
  )
}
