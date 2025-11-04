'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'

export default function DashboardNavbar() {
  const pathname = usePathname()
  const router = useRouter()
  const [unviewedScansCount, setUnviewedScansCount] = useState(0)
  const [isDevMode, setIsDevMode] = useState(false)

  useEffect(() => {
    // Check dev mode
    const devMode = localStorage.getItem('devMode')
    setIsDevMode(devMode === 'true')

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

  const navLinks = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/dashboard/scanner', label: 'Scanner' },
    { href: '/dashboard/repositories', label: 'Repositories' },
    { href: '/dashboard/scans', label: 'Scans' },
  ]

  return (
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
              {navLinks.map((link) => {
                const isActive = pathname === link.href ||
                                (link.href !== '/dashboard' && pathname?.startsWith(link.href))

                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative ${
                      isActive
                        ? 'text-purple-600 font-medium border-b-2 border-purple-600 pb-1'
                        : 'text-gray-600 hover:text-purple-600'
                    }`}
                  >
                    {link.label}
                    {link.label === 'Scans' && unviewedScansCount > 0 && (
                      <span className="absolute -top-2 -right-4 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                        {unviewedScansCount}
                      </span>
                    )}
                  </Link>
                )
              })}
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
  )
}
