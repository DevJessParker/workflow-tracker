'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { User } from '@/contexts/AuthContext'

interface CompanyDashboardProps {
  user: User
  onLogout: () => void
}

export default function CompanyDashboard({ user, onLogout }: CompanyDashboardProps) {
  const plan = user.organization.plan || 'enterprise'

  // Mock company data
  const [companyStats] = useState({
    totalEmployees: 45,
    activeRepos: 23,
    totalScans: 342,
    patternsFound: 1247,
    departments: 8,
    teams: 12
  })

  const [employees] = useState([
    { id: '1', name: user.name, email: user.email, role: user.role, department: 'Engineering', status: 'active', joinedAt: '2024-01-15' },
    { id: '2', name: 'Sarah Johnson', email: 'sarah@company.com', role: 'employee', department: 'Engineering', status: 'active', joinedAt: '2024-02-20' },
    { id: '3', name: 'Mike Chen', email: 'mike@company.com', role: 'manager', department: 'Product', status: 'active', joinedAt: '2024-03-10' },
    { id: '4', name: 'Emily Davis', email: 'emily@company.com', role: 'employee', department: 'Engineering', status: 'active', joinedAt: '2024-04-05' },
    { id: '5', name: 'James Wilson', email: 'james@company.com', role: 'admin', department: 'IT', status: 'active', joinedAt: '2024-01-20' },
  ])

  const [recentActivity] = useState([
    { id: '1', user: 'Sarah Johnson', action: 'completed scan', target: 'web-app', time: '2 hours ago' },
    { id: '2', user: 'Mike Chen', action: 'added repository', target: 'mobile-app', time: '5 hours ago' },
    { id: '3', user: 'Emily Davis', action: 'completed scan', target: 'api-service', time: '1 day ago' },
  ])

  const isAdmin = user.role === 'owner' || user.role === 'admin'

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {user.organization.name} Dashboard
        </h1>
        <div className="flex items-center space-x-2 text-gray-600">
          <span className="text-2xl">🏢</span>
          <span>Company Admin Portal</span>
          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded-full uppercase">
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
            <h3 className="text-sm font-medium text-gray-600">Total Employees</h3>
            <span className="text-2xl">👥</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{companyStats.totalEmployees}</div>
          <div className="text-sm text-gray-500 mt-1">across {companyStats.departments} departments</div>
          <Link
            href="/dashboard/employees"
            className="text-xs text-red-600 hover:text-red-700 mt-2 inline-block"
          >
            Manage employees →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Active Repositories</h3>
            <span className="text-2xl">📁</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{companyStats.activeRepos}</div>
          <div className="text-sm text-gray-500 mt-1">unlimited plan</div>
          <Link
            href="/dashboard/repositories"
            className="text-xs text-red-600 hover:text-red-700 mt-2 inline-block"
          >
            View repositories →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Total Scans</h3>
            <span className="text-2xl">🔍</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{companyStats.totalScans}</div>
          <div className="text-sm text-gray-500 mt-1">this month</div>
          <Link
            href="/dashboard/scans"
            className="text-xs text-red-600 hover:text-red-700 mt-2 inline-block"
          >
            View all scans →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Patterns Found</h3>
            <span className="text-2xl">📊</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{companyStats.patternsFound}</div>
          <div className="text-sm text-gray-500 mt-1">across all repos</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-6 grid md:grid-cols-4 gap-4">
          {isAdmin && (
            <Link
              href="/dashboard/employees/invite"
              className="flex items-center space-x-4 p-4 border-2 border-dashed border-red-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition-all group"
            >
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                ➕
              </div>
              <div>
                <div className="font-semibold text-gray-900">Add Employee</div>
                <div className="text-sm text-gray-600">Invite new user</div>
              </div>
            </Link>
          )}

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

          {isAdmin && (
            <Link
              href="/dashboard/access"
              className="flex items-center space-x-4 p-4 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
            >
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                🔐
              </div>
              <div>
                <div className="font-semibold text-gray-900">Access Control</div>
                <div className="text-sm text-gray-600">Manage permissions</div>
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
                <div className="font-semibold text-gray-900">Company Settings</div>
                <div className="text-sm text-gray-600">Configure org</div>
              </div>
            </Link>
          )}
        </div>
      </div>

      {/* Employee Overview */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Employees</h2>
          {isAdmin && (
            <Link
              href="/dashboard/employees/invite"
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all text-sm font-semibold"
            >
              + Add Employee
            </Link>
          )}
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Employee</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Department</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Role</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Joined</th>
                  {isAdmin && <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {employees.slice(0, 5).map((employee) => (
                  <tr key={employee.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div>
                        <div className="font-medium text-gray-900">{employee.name}</div>
                        <div className="text-sm text-gray-600">{employee.email}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{employee.department}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded-full capitalize">
                        {employee.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full capitalize">
                        {employee.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{employee.joinedAt}</td>
                    {isAdmin && (
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/dashboard/employees/${employee.id}`}
                          className="text-red-600 hover:text-red-700 text-sm font-medium"
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
          <div className="mt-4 text-center">
            <Link
              href="/dashboard/employees"
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              View all {companyStats.totalEmployees} employees →
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Recent Company Activity</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center text-xl">
                    👤
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      <span className="font-semibold">{activity.user}</span> {activity.action}{' '}
                      <span className="font-semibold">{activity.target}</span>
                    </div>
                    <div className="text-xs text-gray-500">{activity.time}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-center">
            <Link
              href="/dashboard/activity"
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              View all activity →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
