'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface DashboardSwitcherProps {
  currentUser: any
}

export default function DashboardSwitcher({ currentUser }: DashboardSwitcherProps) {
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const isDev = process.env.NODE_ENV === 'development'

  if (!isDev) {
    return null
  }

  const dashboardTypes = [
    {
      id: 'individual',
      name: 'Individual Developer',
      icon: '👤',
      description: 'Solo developer with personal account',
      user: {
        id: 'dev-individual-123',
        email: 'individual@pinatacode.com',
        name: 'Alex Developer',
        role: 'owner',
        organization: {
          id: 'org-individual-123',
          name: 'Personal',
          type: 'individual',
          plan: 'free'
        }
      }
    },
    {
      id: 'team-owner',
      name: 'Team Owner',
      icon: '👥',
      description: 'Team creator with full admin access',
      user: {
        id: 'dev-team-owner-123',
        email: 'owner@team.com',
        name: 'Sarah Team Lead',
        role: 'owner',
        organization: {
          id: 'org-team-123',
          name: 'Engineering Team',
          type: 'team',
          plan: 'team'
        }
      }
    },
    {
      id: 'team-member',
      name: 'Team Member',
      icon: '👥',
      description: 'Regular team member without admin access',
      user: {
        id: 'dev-team-member-123',
        email: 'member@team.com',
        name: 'John Developer',
        role: 'member',
        organization: {
          id: 'org-team-123',
          name: 'Engineering Team',
          type: 'team',
          plan: 'team'
        }
      }
    },
    {
      id: 'company-owner',
      name: 'Company Owner/Admin',
      icon: '🏢',
      description: 'Company administrator with full control',
      user: {
        id: 'dev-company-owner-123',
        email: 'admin@company.com',
        name: 'Jennifer CEO',
        role: 'owner',
        organization: {
          id: 'org-company-123',
          name: 'Acme Corporation',
          type: 'company',
          plan: 'enterprise'
        }
      }
    },
    {
      id: 'company-employee',
      name: 'Company Employee',
      icon: '👨‍💼',
      description: 'Regular employee without admin access',
      user: {
        id: 'dev-company-employee-123',
        email: 'employee@company.com',
        name: 'Mike Engineer',
        role: 'employee',
        organization: {
          id: 'org-company-123',
          name: 'Acme Corporation',
          type: 'company',
          plan: 'enterprise'
        }
      }
    },
    {
      id: 'company-manager',
      name: 'Company Manager',
      icon: '👔',
      description: 'Department manager with some admin access',
      user: {
        id: 'dev-company-manager-123',
        email: 'manager@company.com',
        name: 'Lisa Manager',
        role: 'manager',
        organization: {
          id: 'org-company-123',
          name: 'Acme Corporation',
          type: 'company',
          plan: 'enterprise'
        }
      }
    }
  ]

  const switchDashboard = (dashboardType: typeof dashboardTypes[0]) => {
    // Update localStorage with new user
    localStorage.setItem('user', JSON.stringify(dashboardType.user))
    localStorage.setItem('devMode', 'true')

    setIsOpen(false)

    // Force refresh to show new dashboard
    router.refresh()
    window.location.reload()
  }

  const currentDashboard = dashboardTypes.find(
    d => d.user.role === currentUser?.role && d.user.organization.type === currentUser?.organization?.type
  )

  return (
    <>
      {/* Toggle Button */}
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="px-4 py-3 bg-yellow-500 text-yellow-900 rounded-lg shadow-lg hover:bg-yellow-600 transition-all font-semibold flex items-center space-x-2"
          title="Dev Dashboard Switcher"
        >
          <span className="text-xl">🔄</span>
          <span className="hidden md:inline">Dashboard Switcher</span>
        </button>
      </div>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="p-6 border-b border-gray-200 bg-yellow-50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                    <span className="text-3xl">🔄</span>
                    <span>Dev Dashboard Switcher</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Quickly switch between different user types to test dashboards
                  </p>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>
              {currentDashboard && (
                <div className="mt-4 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
                  <div className="flex items-center space-x-2 text-sm">
                    <span className="text-xl">{currentDashboard.icon}</span>
                    <span className="font-semibold">Currently viewing: {currentDashboard.name}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Dashboard Options */}
            <div className="p-6 grid md:grid-cols-2 gap-4">
              {dashboardTypes.map((dashboard) => {
                const isCurrent = currentDashboard?.id === dashboard.id

                return (
                  <button
                    key={dashboard.id}
                    onClick={() => switchDashboard(dashboard)}
                    disabled={isCurrent}
                    className={`p-6 border-2 rounded-xl text-left transition-all ${
                      isCurrent
                        ? 'border-yellow-500 bg-yellow-50 cursor-not-allowed'
                        : 'border-gray-200 hover:border-purple-500 hover:bg-purple-50 cursor-pointer'
                    }`}
                  >
                    <div className="flex items-start space-x-4">
                      <div className="text-4xl">{dashboard.icon}</div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-bold text-gray-900">{dashboard.name}</h3>
                          {isCurrent && (
                            <span className="px-2 py-1 bg-yellow-500 text-yellow-900 text-xs font-semibold rounded-full">
                              Current
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{dashboard.description}</p>
                        <div className="space-y-1 text-xs text-gray-500">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold">Name:</span>
                            <span>{dashboard.user.name}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold">Role:</span>
                            <span className="px-2 py-0.5 bg-gray-100 rounded capitalize">
                              {dashboard.user.role}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold">Org:</span>
                            <span>{dashboard.user.organization.name}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold">Plan:</span>
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded uppercase">
                              {dashboard.user.organization.plan}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Info Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="text-sm text-gray-600 space-y-2">
                <div className="flex items-start space-x-2">
                  <span className="text-lg">💡</span>
                  <div>
                    <span className="font-semibold">Tip:</span> This tool is only available in development mode.
                    Click any dashboard type to instantly switch and reload the page.
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-lg">🔍</span>
                  <div>
                    <span className="font-semibold">Testing:</span> Use this to test different permission levels,
                    UI variations, and role-based features without creating multiple accounts.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
