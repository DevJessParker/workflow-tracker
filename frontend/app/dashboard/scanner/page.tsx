'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useScanWebSocket, type ScanProgress } from '@/hooks/useScanWebSocket'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Repository {
  name: string
  path: string
  source: string
}

export default function ScannerPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Scanner state
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [selectedRepo, setSelectedRepo] = useState<string>('')
  const [scanId, setScanId] = useState<string | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)

  // WebSocket hook for real-time progress
  const {
    progress,
    isConnected,
    connectionStatus,
    error: wsError,
  } = useScanWebSocket({
    scanId,
    enabled: isScanning && scanId !== null,
    onProgress: (progress: ScanProgress) => {
      console.log('📊 Progress update:', progress)
    },
    onComplete: (progress: ScanProgress) => {
      console.log('✅ Scan completed:', progress)
      setIsScanning(false)
    },
    onError: (error: string) => {
      console.error('❌ Scan error:', error)
      setScanError(error)
      setIsScanning(false)
    },
  })

  useEffect(() => {
    // Check authentication
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      router.push('/auth/login')
      return
    }

    setUser(JSON.parse(storedUser))
    setLoading(false)

    // Fetch repositories
    fetchRepositories()
  }, [router])

  useEffect(() => {
    console.log('🔌 WebSocket connection status:', connectionStatus)
  }, [connectionStatus])

  const fetchRepositories = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/scanner/repositories?source=local`)
      if (response.ok) {
        const repos = await response.json()
        setRepositories(repos)
        if (repos.length > 0) {
          setSelectedRepo(repos[0].path)
        }
      }
    } catch (error) {
      console.error('Failed to fetch repositories:', error)
    }
  }

  const startScan = async () => {
    if (!selectedRepo) {
      setScanError('Please select a repository')
      return
    }

    console.log('🚀 Starting scan with config:', {
      repository_path: selectedRepo,
    })
    console.log('🔗 API URL:', API_URL)

    try {
      setScanError(null)
      setIsScanning(true)

      console.log('📤 Sending POST request to start scan:', `${API_URL}/api/v1/scanner/scan`)

      const response = await fetch(`${API_URL}/api/v1/scanner/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository_path: selectedRepo,
          file_types: ['.cs', '.ts', '.html', '.xaml'],
          exclude_patterns: ['node_modules', 'bin', 'obj', '.git', 'dist'],
        }),
      })

      if (!response.ok) {
        throw new Error(`Scan failed: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('✅ Scan started successfully:', data)
      console.log('🎯 Scan ID:', data.scan_id)

      setScanId(data.scan_id)
    } catch (error: any) {
      console.error('❌ Failed to start scan:', error)
      setScanError(error.message)
      setIsScanning(false)
    }
  }

  const getProgressBarColor = () => {
    if (!progress) return 'bg-purple-600'
    if (progress.status === 'error' || progress.status === 'failed') return 'bg-red-600'
    if (progress.status === 'completed') return 'bg-green-600'
    return 'bg-purple-600'
  }

  const getStatusText = () => {
    if (!isScanning) return 'Ready to scan'
    if (!progress) return 'Initializing...'

    switch (progress.status) {
      case 'queued':
        return 'Scan queued...'
      case 'discovering':
        return 'Discovering files...'
      case 'scanning':
        return `Scanning (${progress.files_scanned} files, ${progress.nodes_found} nodes)`
      case 'completed':
        return '✅ Scan completed!'
      case 'error':
      case 'failed':
        return `❌ Scan failed: ${progress.message}`
      default:
        return 'Scanning...'
    }
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
                <Link href="/dashboard" className="text-gray-600 hover:text-purple-600">
                  Dashboard
                </Link>
                <Link
                  href="/dashboard/scanner"
                  className="text-purple-600 font-medium border-b-2 border-purple-600 pb-1"
                >
                  Scanner
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/dashboard" className="text-gray-600 hover:text-purple-600">
                Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold mb-6">Code Scanner</h1>

          {/* Repository Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Repository
            </label>
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isScanning}
            >
              {repositories.length === 0 && (
                <option value="">No repositories available</option>
              )}
              {repositories.map((repo) => (
                <option key={repo.path} value={repo.path}>
                  {repo.name} ({repo.path})
                </option>
              ))}
            </select>
          </div>

          {/* Scan Button */}
          <button
            onClick={startScan}
            disabled={isScanning || !selectedRepo}
            className={`w-full px-6 py-3 rounded-lg font-medium transition-colors ${
              isScanning || !selectedRepo
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {isScanning ? 'Scanning...' : 'Start Scan'}
          </button>

          {/* Error Message */}
          {(scanError || wsError) && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{scanError || wsError}</p>
            </div>
          )}

          {/* Progress Section */}
          {isScanning && (
            <div className="mt-6">
              {/* Connection Status */}
              <div className="mb-4 flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'
                  }`}
                />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Connecting...'}
                </span>
              </div>

              {/* Status Text */}
              <div className="mb-2">
                <p className="text-sm font-medium text-gray-700">{getStatusText()}</p>
              </div>

              {/* Progress Bar */}
              {progress && (
                <>
                  <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                    <div
                      className={`h-4 rounded-full transition-all duration-300 ${getProgressBarColor()}`}
                      style={{ width: `${Math.min(progress.progress, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{progress.progress.toFixed(1)}%</span>
                    <span>
                      {progress.files_scanned} files | {progress.nodes_found} nodes
                    </span>
                  </div>
                  {progress.message && (
                    <p className="mt-2 text-sm text-gray-600">{progress.message}</p>
                  )}
                </>
              )}
            </div>
          )}

          {/* Scan Results */}
          {progress && progress.status === 'completed' && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-lg font-medium text-green-800 mb-2">Scan Complete!</h3>
              <div className="space-y-1 text-sm text-green-700">
                <p>📁 Files scanned: {progress.files_scanned}</p>
                <p>🔍 Nodes found: {progress.nodes_found}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
