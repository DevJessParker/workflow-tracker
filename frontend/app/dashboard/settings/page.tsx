'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { User } from '@/contexts/AuthContext'

export default function SettingsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('profile')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Form state
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    phone: '',
    timezone: 'UTC',
  })

  const [organizationData, setOrganizationData] = useState({
    name: '',
    description: '',
    website: '',
  })

  const [notificationPrefs, setNotificationPrefs] = useState({
    emailNotifications: true,
    scanComplete: true,
    patternDetected: true,
    weeklyReport: false,
  })

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      router.push('/auth/login')
      return
    }

    const parsedUser = JSON.parse(storedUser)
    setUser(parsedUser)
    setProfileData({
      name: parsedUser.name,
      email: parsedUser.email,
      phone: '',
      timezone: 'UTC',
    })
    setOrganizationData({
      name: parsedUser.organization.name,
      description: '',
      website: '',
    })
    setLoading(false)
  }, [router])

  const handleProfileSave = async () => {
    setSaving(true)
    // TODO: Implement API call to save profile
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Update localStorage
    if (user) {
      const updatedUser = { ...user, name: profileData.name, email: profileData.email }
      localStorage.setItem('user', JSON.stringify(updatedUser))
      setUser(updatedUser)
    }

    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleOrganizationSave = async () => {
    setSaving(true)
    // TODO: Implement API call to save organization settings
    await new Promise(resolve => setTimeout(resolve, 1000))

    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleNotificationsSave = async () => {
    setSaving(true)
    // TODO: Implement API call to save notification preferences
    await new Promise(resolve => setTimeout(resolve, 1000))

    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    )
  }

  const isOrgAdmin = user.role === 'owner' || user.role === 'admin'
  const tabs = [
    { id: 'profile', label: 'Profile', icon: '👤' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
  ]

  if (isOrgAdmin) {
    tabs.push({ id: 'organization', label: user.organization.type === 'company' ? 'Company' : 'Team', icon: user.organization.type === 'company' ? '🏢' : '👥' })
    tabs.push({ id: 'billing', label: 'Billing', icon: '💳' })
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">Manage your account and preferences</p>
        </div>

        <div className="grid md:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <nav className="space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full text-left px-4 py-3 rounded-lg flex items-center space-x-3 transition-colors ${
                      activeTab === tab.id
                        ? 'bg-purple-100 text-purple-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <span className="text-xl">{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="md:col-span-3">
            {/* Success Message */}
            {saved && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2 text-green-700">
                <span className="text-xl">✓</span>
                <span>Settings saved successfully!</span>
              </div>
            )}

            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-bold text-gray-900">Profile Settings</h2>
                  <p className="text-sm text-gray-600 mt-1">Update your personal information</p>
                </div>
                <div className="p-6 space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={profileData.name}
                      onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Phone Number (Optional)
                    </label>
                    <input
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timezone
                    </label>
                    <select
                      value={profileData.timezone}
                      onChange={(e) => setProfileData({ ...profileData, timezone: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                    </select>
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <button
                      onClick={handleProfileSave}
                      disabled={saving}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-bold text-gray-900">Notification Preferences</h2>
                  <p className="text-sm text-gray-600 mt-1">Choose how you want to be notified</p>
                </div>
                <div className="p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">Email Notifications</div>
                      <div className="text-sm text-gray-600">Receive notifications via email</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationPrefs.emailNotifications}
                        onChange={(e) => setNotificationPrefs({ ...notificationPrefs, emailNotifications: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">Scan Complete</div>
                      <div className="text-sm text-gray-600">Notify when a scan finishes</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationPrefs.scanComplete}
                        onChange={(e) => setNotificationPrefs({ ...notificationPrefs, scanComplete: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">Pattern Detected</div>
                      <div className="text-sm text-gray-600">Notify when new patterns are found</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationPrefs.patternDetected}
                        onChange={(e) => setNotificationPrefs({ ...notificationPrefs, patternDetected: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">Weekly Report</div>
                      <div className="text-sm text-gray-600">Receive weekly activity summary</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationPrefs.weeklyReport}
                        onChange={(e) => setNotificationPrefs({ ...notificationPrefs, weeklyReport: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <button
                      onClick={handleNotificationsSave}
                      disabled={saving}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Preferences'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Organization Tab (for admins only) */}
            {activeTab === 'organization' && isOrgAdmin && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-bold text-gray-900">
                    {user.organization.type === 'company' ? 'Company' : 'Team'} Settings
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">Manage organization information</p>
                </div>
                <div className="p-6 space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {user.organization.type === 'company' ? 'Company' : 'Team'} Name
                    </label>
                    <input
                      type="text"
                      value={organizationData.name}
                      onChange={(e) => setOrganizationData({ ...organizationData, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={organizationData.description}
                      onChange={(e) => setOrganizationData({ ...organizationData, description: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                      placeholder="Brief description of your organization"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Website (Optional)
                    </label>
                    <input
                      type="url"
                      value={organizationData.website}
                      onChange={(e) => setOrganizationData({ ...organizationData, website: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                      placeholder="https://example.com"
                    />
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <button
                      onClick={handleOrganizationSave}
                      disabled={saving}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>

                  {/* Danger Zone */}
                  <div className="pt-6 border-t border-gray-200">
                    <h3 className="text-lg font-bold text-red-600 mb-4">Danger Zone</h3>
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-red-900">
                            Delete {user.organization.type === 'company' ? 'Company' : 'Team'}
                          </div>
                          <div className="text-sm text-red-700 mt-1">
                            This action cannot be undone. All data will be permanently deleted.
                          </div>
                        </div>
                        <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all">
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Billing Tab (for admins only) */}
            {activeTab === 'billing' && isOrgAdmin && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-bold text-gray-900">Billing & Subscription</h2>
                  <p className="text-sm text-gray-600 mt-1">Manage your plan and payment methods</p>
                </div>
                <div className="p-6 space-y-6">
                  {/* Current Plan */}
                  <div className="p-6 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 capitalize">{user.organization.plan || 'free'} Plan</h3>
                        <p className="text-sm text-gray-600">Current subscription</p>
                      </div>
                      <span className="text-3xl font-bold text-purple-600">
                        ${user.organization.plan === 'team' ? '49' : user.organization.plan === 'enterprise' ? '499' : '0'}
                        <span className="text-sm font-normal text-gray-600">/month</span>
                      </span>
                    </div>
                    <div className="flex space-x-4">
                      <Link
                        href="/dashboard/billing/upgrade"
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                      >
                        Upgrade Plan
                      </Link>
                      <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all">
                        View Invoice History
                      </button>
                    </div>
                  </div>

                  {/* Payment Method */}
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-4">Payment Method</h3>
                    <div className="p-4 border border-gray-200 rounded-lg flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-8 bg-gray-200 rounded flex items-center justify-center">
                          <span className="text-xs font-bold">VISA</span>
                        </div>
                        <div>
                          <div className="font-medium">•••• •••• •••• 4242</div>
                          <div className="text-sm text-gray-600">Expires 12/25</div>
                        </div>
                      </div>
                      <button className="text-purple-600 hover:text-purple-700 font-medium">
                        Update
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
