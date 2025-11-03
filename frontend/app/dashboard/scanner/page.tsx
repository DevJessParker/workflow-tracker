'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface ScanConfig {
  repoPath: string
  sourceType: 'local' | 'github' | 'gitlab' | 'bitbucket'
  fileExtensions: string[]
  detectDatabase: boolean
  detectApi: boolean
  detectFiles: boolean
  detectMessages: boolean
  detectTransforms: boolean
}

interface ScanStatus {
  scan_id: string
  status: string
  progress: number
  message: string
  files_scanned: number
  nodes_found: number
}

interface WorkflowNode {
  id: string
  type: string
  name: string
  description: string
  location: {
    file_path: string
    line_number: number
  }
  table_name?: string
  endpoint?: string
  http_method?: string
}

interface WorkflowEdge {
  source: string
  target: string
  label: string
  edge_type: string
}

interface ScanResults {
  scan_id: string
  status: string
  files_scanned: number
  scan_duration: number
  graph: {
    nodes: WorkflowNode[]
    edges: WorkflowEdge[]
  }
}

export default function ScannerPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Environment and repository state
  const [environment, setEnvironment] = useState<any>(null)
  const [repositories, setRepositories] = useState<any[]>([])

  // Scan configuration state
  const [config, setConfig] = useState<ScanConfig>({
    repoPath: '',
    sourceType: 'local',
    fileExtensions: ['.cs', '.ts', '.html', '.xaml'],
    detectDatabase: true,
    detectApi: true,
    detectFiles: true,
    detectMessages: true,
    detectTransforms: true,
  })

  // Scan execution state
  const [scanning, setScanning] = useState(false)
  const [scanId, setScanId] = useState<string | null>(null)
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null)
  const [scanResults, setScanResults] = useState<ScanResults | null>(null)
  const [diagram, setDiagram] = useState<string | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // Check authentication
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      router.push('/auth/login')
      return
    }

    setUser(JSON.parse(storedUser))
    setLoading(false)

    // Load environment info
    loadEnvironment()
  }, [router])

  const loadEnvironment = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/scanner/environment`)
      const data = await response.json()
      setEnvironment(data)

      // If supports local repos, load them
      if (data.supports_local_repos) {
        loadRepositories('local')
      }
    } catch (error) {
      console.error('Failed to load environment:', error)
    }
  }

  const loadRepositories = async (source: string) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/scanner/repositories?source=${source}`)
      const data = await response.json()
      setRepositories(data.repositories || [])
    } catch (error) {
      console.error('Failed to load repositories:', error)
    }
  }

  const startScan = async () => {
    try {
      setScanning(true)
      setScanResults(null)
      setDiagram(null)

      // Set initial status immediately for UI feedback
      setScanStatus({
        scan_id: 'pending',
        status: 'starting',
        progress: 0,
        message: 'Starting scan...',
        files_scanned: 0,
        nodes_found: 0
      })

      console.log('Starting scan with config:', config)
      console.log('API URL:', API_URL)

      const response = await fetch(`${API_URL}/api/v1/scanner/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_path: config.repoPath,
          source_type: config.sourceType,
          file_extensions: config.fileExtensions,
          detect_database: config.detectDatabase,
          detect_api: config.detectApi,
          detect_files: config.detectFiles,
          detect_messages: config.detectMessages,
          detect_transforms: config.detectTransforms,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Scan started:', data)
      setScanId(data.scan_id)

      // Poll for status
      pollScanStatus(data.scan_id)
    } catch (error) {
      console.error('Failed to start scan:', error)
      alert(`Failed to start scan: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setScanning(false)
      setScanStatus(null)
    }
  }

  const pollScanStatus = async (id: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/scanner/scan/${id}/status`)
        const status = await response.json()

        console.log('📊 Scan status update:', {
          progress: status.progress,
          message: status.message,
          files: status.files_scanned,
          nodes: status.nodes_found,
          status: status.status
        })

        setScanStatus(status)

        if (status.status === 'completed') {
          console.log('✅ Scan completed!')
          clearInterval(pollInterval)
          setScanning(false)
          loadScanResults(id)
        } else if (status.status === 'failed') {
          console.error('❌ Scan failed!')
          clearInterval(pollInterval)
          setScanning(false)
        }
      } catch (error) {
        console.error('Failed to poll scan status:', error)
      }
    }, 1000)

    // Stop polling after 10 minutes
    setTimeout(() => clearInterval(pollInterval), 600000)
  }

  const loadScanResults = async (id: string) => {
    try {
      // Load results
      const resultsResponse = await fetch(`${API_URL}/api/v1/scanner/scan/${id}/results`)
      const results = await resultsResponse.json()
      setScanResults(results)

      // Load diagram
      const diagramResponse = await fetch(`${API_URL}/api/v1/scanner/scan/${id}/diagram?format=mermaid`)
      const diagramData = await diagramResponse.json()
      setDiagram(diagramData.diagram)
    } catch (error) {
      console.error('Failed to load scan results:', error)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    router.push('/')
  }

  if (loading) {
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
                <Link href="/dashboard/repositories" className="text-gray-600 hover:text-purple-600">
                  Repositories
                </Link>
                <Link href="/dashboard/scans" className="text-gray-600 hover:text-purple-600">
                  Scans
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
              {environment && environment.is_docker && (
                <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                  DOCKER
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🔍 Workflow Scanner</h1>
          <p className="text-gray-600 mt-2">
            Scan your repositories to discover and visualize UI workflows from Angular and WPF applications
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Scan Configuration</h2>

              {/* Source Type Toggle */}
              {environment && environment.supports_local_repos && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Repository Source
                  </label>
                  <div className="flex space-x-2">
                    <button
                      className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                        config.sourceType === 'local'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                      onClick={() => {
                        setConfig({ ...config, sourceType: 'local' })
                        loadRepositories('local')
                      }}
                    >
                      📁 Local
                    </button>
                    <button
                      className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                        config.sourceType !== 'local'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                      onClick={() => setConfig({ ...config, sourceType: 'github' })}
                    >
                      ☁️ Cloud
                    </button>
                  </div>
                </div>
              )}

              {/* Repository Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Repository Path
                </label>
                {config.sourceType === 'local' && repositories.length > 0 ? (
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={config.repoPath}
                    onChange={(e) => setConfig({ ...config, repoPath: e.target.value })}
                  >
                    <option value="">Select a repository...</option>
                    {repositories.map((repo) => (
                      <option key={repo.path} value={repo.path}>
                        {repo.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="/path/to/repository"
                    value={config.repoPath}
                    onChange={(e) => setConfig({ ...config, repoPath: e.target.value })}
                  />
                )}
              </div>

              {/* File Extensions */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File Extensions
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder=".cs,.ts,.html,.xaml"
                  value={config.fileExtensions.join(',')}
                  onChange={(e) =>
                    setConfig({ ...config, fileExtensions: e.target.value.split(',').map((ext) => ext.trim()) })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">Comma-separated list</p>
              </div>

              {/* Detection Options */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Detection Options</label>
                <div className="space-y-2">
                  {[
                    { key: 'detectDatabase', label: 'Database Operations' },
                    { key: 'detectApi', label: 'API Calls' },
                    { key: 'detectFiles', label: 'File I/O' },
                    { key: 'detectMessages', label: 'Message Queues' },
                    { key: 'detectTransforms', label: 'Data Transforms' },
                  ].map((option) => (
                    <label key={option.key} className="flex items-center">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                        checked={config[option.key as keyof ScanConfig] as boolean}
                        onChange={(e) => setConfig({ ...config, [option.key]: e.target.checked })}
                      />
                      <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Start Scan Button */}
              <button
                className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
                  scanning || !config.repoPath
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-700'
                }`}
                onClick={startScan}
                disabled={scanning || !config.repoPath}
              >
                {scanning ? '⏳ Scanning...' : '🔍 Start Scan'}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {/* Scan Progress */}
            {scanning && scanStatus && (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="flex items-center space-x-3 mb-4">
                  <span className="text-3xl animate-bounce">🪅</span>
                  <h2 className="text-xl font-bold text-gray-900">Scanning Your Code...</h2>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between items-center text-sm text-gray-600 mb-2">
                    <span className="font-medium">{scanStatus.message}</span>
                    <span className="text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                      {scanStatus.progress.toFixed(0)}%
                    </span>
                  </div>
                  <div className="relative w-full bg-gray-200 rounded-full h-6 overflow-hidden shadow-inner">
                    <div
                      className="h-6 rounded-full transition-all duration-500 ease-out relative"
                      style={{
                        width: `${scanStatus.progress}%`,
                        background: 'linear-gradient(90deg, #667eea 0%, #764ba2 14%, #f093fb 28%, #f5576c 42%, #feca57 57%, #48dbfb 71%, #0abde3 85%, #00d2d3 100%)',
                        boxShadow: '0 2px 8px rgba(102, 126, 234, 0.4)'
                      }}
                    >
                      <div className="absolute inset-0 bg-white opacity-20 animate-pulse"></div>
                    </div>
                  </div>
                </div>
                <div className="flex justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-500">📄 Files:</span>
                    <span className="font-bold text-purple-600">{scanStatus.files_scanned}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-500">🔗 Nodes:</span>
                    <span className="font-bold text-pink-600">{scanStatus.nodes_found}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-500">⚡ Status:</span>
                    <span className="font-bold text-blue-600 capitalize">{scanStatus.status}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Scan Results */}
            {scanResults && (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Scan Results</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-3xl font-bold text-purple-600">{scanResults.files_scanned}</div>
                      <div className="text-sm text-gray-600">Files Scanned</div>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-3xl font-bold text-blue-600">{scanResults.graph.nodes.length}</div>
                      <div className="text-sm text-gray-600">Workflow Nodes</div>
                    </div>
                    <div className="text-center p-4 bg-pink-50 rounded-lg">
                      <div className="text-3xl font-bold text-pink-600">{scanResults.graph.edges.length}</div>
                      <div className="text-sm text-gray-600">Connections</div>
                    </div>
                  </div>
                </div>

                {/* Diagram */}
                {diagram && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Workflow Diagram</h2>
                    <div className="bg-gray-50 p-4 rounded-lg overflow-auto">
                      <pre className="text-sm text-gray-700">{diagram}</pre>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Copy this Mermaid diagram and paste it into{' '}
                      <a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">
                        mermaid.live
                      </a>{' '}
                      or GitHub to visualize
                    </p>
                  </div>
                )}

                {/* Nodes List */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Detected Workflows</h2>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {scanResults.graph.nodes.map((node) => (
                      <div
                        key={node.id}
                        className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
                              node.type.includes('database') ? 'bg-green-100 text-green-800' :
                              node.type.includes('api') ? 'bg-blue-100 text-blue-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {node.type.toUpperCase()}
                            </span>
                            <span className="ml-2 font-medium text-gray-900">{node.name}</span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {node.location.file_path}:{node.location.line_number}
                          </span>
                        </div>
                        {node.description && (
                          <p className="text-sm text-gray-600 mt-1">{node.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!scanning && !scanResults && (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <div className="text-6xl mb-4">🪅</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Ready to Scan</h3>
                <p className="text-gray-600">
                  Configure your scan settings and click "Start Scan" to analyze your repository
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
