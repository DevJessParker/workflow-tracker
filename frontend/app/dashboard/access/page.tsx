'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { User } from '@/contexts/AuthContext'

interface AccessRole {
  id: string
  name: string
  description: string
  permissions: string[]
  userCount: number
}

interface UserAccess {
  id: string
  name: string
  email: string
  role: string
  repositories: string[]
  lastActive: string
}

export default function AccessManagementPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'users' | 'roles' | 'repositories'>('users')

  // Mock data
  const [roles] = useState<AccessRole[]>([
    {
      id: '1',
      name: 'Administrator',
      description: 'Full access to all features and settings',
      permissions: ['manage_users', 'manage_repos', 'run_scans', 'view_reports', 'manage_billing'],
      userCount: 3
    },
    {
      id: '2',
      name: 'Developer',
      description: 'Can run scans and view reports',
      permissions: ['run_scans', 'view_reports'],
      userCount: 15
    },
    {
      id: '3',
      name: 'Viewer',
      description: 'Read-only access to reports',
      permissions: ['view_reports'],
      userCount: 8
    }
  ])

  const [userAccess] = useState<UserAccess[]>([
    {
      id: '1',
      name: 'Sarah Johnson',
      email: 'sarah@company.com',
      role: 'Developer',
      repositories: ['web-app', 'api-service', 'mobile-app'],
      lastActive: '2 hours ago'
    },
    {
      id: '2',
      name: 'Mike Chen',
      email: 'mike@company.com',
      role: 'Administrator',
      repositories: ['All repositories'],
      lastActive: '5 hours ago'
    },
    {
      id: '3',
      name: 'Emily Davis',
      email: 'emily@company.com',
      role: 'Developer',
      repositories: ['web-app', 'mobile-app'],
      lastActive: '1 day ago'
    },
    {
      id: '4',
      name: 'James Wilson',
      email: 'james@company.com',
      role: 'Viewer',
      repositories: ['web-app'],
      lastActive: '3 days ago'
    }
  ])

  const [repoAccess] = useState([
    { id: '1', name: 'web-app', users: 12, visibility: 'Private', lastScan: '2 hours ago' },
    { id: '2', name: 'api-service', users: 8, visibility: 'Private', lastScan: '5 hours ago' },
    { id: '3', name: 'mobile-app', users: 10, visibility: 'Private', lastScan: '1 day ago' },
    { id: '4', name: 'docs-site', users: 5, visibility: 'Internal', lastScan: '3 days ago' }
  ])

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      router.push('/auth/login')
      return
    }

    const parsedUser = JSON.parse(storedUser)
    setUser(parsedUser)

    // Check if user has access to this page
    if (parsedUser.role !== 'owner' && parsedUser.role !== 'admin') {
      router.push('/dashboard')
      return
    }

    setLoading(false)
  }, [router])

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <span className="text-3xl">🪅</span>
              <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Pinata Code
              </span>
            </Link>
            <Link href="/dashboard" className="text-gray-600 hover:text-purple-600">
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Access Management</h1>
          <p className="text-gray-600">Control user permissions and repository access</p>
        </div>

        {/* Tabs */}
        <div className="mb-8 border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('users')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'users'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              👥 User Access
            </button>
            <button
              onClick={() => setActiveTab('roles')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'roles'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              🎭 Roles & Permissions
            </button>
            <button
              onClick={() => setActiveTab('repositories')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'repositories'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              📁 Repository Access
            </button>
          </nav>
        </div>

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-gray-900">User Access Control</h2>
                <p className="text-sm text-gray-600 mt-1">Manage individual user permissions and repository access</p>
              </div>
              <Link
                href="/dashboard/employees/invite"
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm font-semibold"
              >
                + Add User
              </Link>
            </div>
            <div className="p-6">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-gray-200">
                    <tr>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">User</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Role</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Repository Access</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Last Active</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userAccess.map((userItem) => (
                      <tr key={userItem.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium text-gray-900">{userItem.name}</div>
                            <div className="text-sm text-gray-600">{userItem.email}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-3 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded-full">
                            {userItem.role}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-sm text-gray-600">
                            {userItem.repositories.length > 2
                              ? `${userItem.repositories.slice(0, 2).join(', ')}...`
                              : userItem.repositories.join(', ')}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">{userItem.lastActive}</td>
                        <td className="py-3 px-4 text-right">
                          <button className="text-purple-600 hover:text-purple-700 text-sm font-medium mr-4">
                            Edit Access
                          </button>
                          <button className="text-red-600 hover:text-red-700 text-sm font-medium">
                            Revoke
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Roles & Permissions</h2>
                  <p className="text-sm text-gray-600 mt-1">Define roles and their associated permissions</p>
                </div>
                <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm font-semibold">
                  + Create Role
                </button>
              </div>
              <div className="p-6 space-y-4">
                {roles.map((role) => (
                  <div key={role.id} className="p-6 border border-gray-200 rounded-lg hover:border-purple-300 transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">{role.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{role.description}</p>
                      </div>
                      <span className="px-3 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded-full">
                        {role.userCount} users
                      </span>
                    </div>
                    <div className="mb-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">Permissions:</div>
                      <div className="flex flex-wrap gap-2">
                        {role.permissions.map((permission) => (
                          <span key={permission} className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded">
                            {permission.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex space-x-3">
                      <button className="text-sm text-purple-600 hover:text-purple-700 font-medium">
                        Edit Permissions
                      </button>
                      {role.name !== 'Administrator' && (
                        <button className="text-sm text-red-600 hover:text-red-700 font-medium">
                          Delete Role
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Permission Reference */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-bold text-gray-900">Available Permissions</h3>
              </div>
              <div className="p-6">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-semibold text-gray-900 mb-2">manage_users</div>
                    <div className="text-sm text-gray-600">Create, edit, and delete users</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-semibold text-gray-900 mb-2">manage_repos</div>
                    <div className="text-sm text-gray-600">Add, remove, and configure repositories</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-semibold text-gray-900 mb-2">run_scans</div>
                    <div className="text-sm text-gray-600">Execute workflow scans on repositories</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-semibold text-gray-900 mb-2">view_reports</div>
                    <div className="text-sm text-gray-600">View scan results and reports</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-semibold text-gray-900 mb-2">manage_billing</div>
                    <div className="text-sm text-gray-600">Manage subscription and billing settings</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Repositories Tab */}
        {activeTab === 'repositories' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Repository Access Control</h2>
                <p className="text-sm text-gray-600 mt-1">Manage who can access each repository</p>
              </div>
              <Link
                href="/dashboard/repositories/connect"
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm font-semibold"
              >
                + Add Repository
              </Link>
            </div>
            <div className="p-6">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-gray-200">
                    <tr>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Repository</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Visibility</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Users with Access</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Last Scan</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {repoAccess.map((repo) => (
                      <tr key={repo.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center space-x-2">
                            <span className="text-xl">📁</span>
                            <span className="font-medium text-gray-900">{repo.name}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                            repo.visibility === 'Private'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {repo.visibility}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-600">{repo.users} users</span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">{repo.lastScan}</td>
                        <td className="py-3 px-4 text-right">
                          <button className="text-purple-600 hover:text-purple-700 text-sm font-medium mr-4">
                            Manage Access
                          </button>
                          <button className="text-gray-600 hover:text-gray-700 text-sm font-medium">
                            Settings
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
