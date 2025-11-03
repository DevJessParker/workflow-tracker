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
  eta?: string
  total_files?: number
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

  // Debug: Log when scanStatus changes
  useEffect(() => {
    const timestamp = new Date().toLocaleTimeString()
    console.log(`[${timestamp}] 🔄 REACT STATE CHANGE: scanStatus updated to:`, scanStatus)
    if (scanStatus) {
      console.log(`[${timestamp}] 🔄 Progress bar should show: ${scanStatus.progress}%`)
      console.log(`[${timestamp}] 🔄 Files: ${scanStatus.files_scanned}/${scanStatus.total_files || '?'}`)
      console.log(`[${timestamp}] 🔄 Nodes: ${scanStatus.nodes_found}`)
      console.log(`[${timestamp}] 🔄 Status: ${scanStatus.status}`)
      console.log(`[${timestamp}] 🔄 ETA: ${scanStatus.eta || 'N/A'}`)
    }
  }, [scanStatus])

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

      console.log('🚀 Starting scan with config:', config)
      console.log('🔗 API URL:', API_URL)

      const requestBody = {
        repo_path: config.repoPath,
        source_type: config.sourceType,
        file_extensions: config.fileExtensions,
        detect_database: config.detectDatabase,
        detect_api: config.detectApi,
        detect_files: config.detectFiles,
        detect_messages: config.detectMessages,
        detect_transforms: config.detectTransforms,
      }

      // Start polling for active scans IMMEDIATELY (don't wait for POST)
      console.log('🔄 Starting to poll for active scans immediately...')
      pollForActiveScan()

      // Send POST request (fire-and-forget, don't wait for response)
      console.log('📤 Sending POST request in background:', `${API_URL}/api/v1/scanner/scan`)
      fetch(`${API_URL}/api/v1/scanner/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      }).then(response => {
        console.log('📥 POST response received (async):', response.status)
        return response.json()
      }).then(data => {
        console.log('✅ Scan started (async confirmation):', data.scan_id)
      }).catch(error => {
        console.error('❌ POST request failed (but polling continues):', error)
      })

    } catch (error) {
      console.error('Failed to start scan:', error)
      alert(`Failed to start scan: ${error instanceof Error ?.message : 'Unknown error'}`)
      setScanning(false)
      setScanStatus(null)
    }
  }

  const pollForActiveScan = () => {
    console.log('🔄 pollForActiveScan: Starting to look for active scans...')
    let attempts = 0
    const maxAttempts = 60 // Poll for up to 60 seconds

    const checkInterval = setInterval(async () => {
      attempts++
      const timestamp = new Date().toLocaleTimeString()

      try {
        console.log(`[${timestamp}] 🔍 Attempt #${attempts}: Checking for active scans...`)

        const response = await fetch(`${API_URL}/api/v1/scanner/scans/active`)
        const data = await response.json()

        console.log(`[${timestamp}] 📊 Active scans response:`, data)

        if (data.active_scans && data.active_scans.length > 0) {
          const latestScan = data.active_scans[data.active_scans.length - 1]
          console.log(`[${timestamp}] ✅ Found active scan! ID: ${latestScan.scan_id}`)
          console.log(`[${timestamp}] 🔄 Switching to scan status polling...`)

          clearInterval(checkInterval)
          setScanId(latestScan.scan_id)
          pollScanStatus(latestScan.scan_id)
        } else {
          console.log(`[${timestamp}] ⏳ No active scans yet, will retry... (${attempts}/${maxAttempts})`)
        }

        if (attempts >= maxAttempts) {
          console.error(`[${timestamp}] ❌ Timeout: No active scans found after ${maxAttempts} attempts`)
          clearInterval(checkInterval)
          setScanning(false)
          setScanStatus(null)
          alert('Scan failed to start - no active scans detected after 60 seconds')
        }
      } catch (error) {
        console.error(`[${timestamp}] ❌ Error checking for active scans:`, error)
      }
    }, 1000) // Check every second
  }

  const pollScanStatus = async (id: string) => {
    console.log(`🔄 Starting to poll scan status for ID: ${id}`)
    let pollCount = 0

    const pollInterval = setInterval(async () => {
      pollCount++
      const timestamp = new Date().toLocaleTimeString()

      try {
        console.log(`[${timestamp}] 📡 Poll #${pollCount}: Fetching status from ${API_URL}/api/v1/scanner/scan/${id}/status`)

        const response = await fetch(`${API_URL}/api/v1/scanner/scan/${id}/status`)

        console.log(`[${timestamp}] 📡 Poll #${pollCount}: Response status: ${response.status}`)

        if (!response.ok) {
          console.error(`[${timestamp}] ❌ Poll #${pollCount}: HTTP error! status: ${response.status}`)
          return
        }

        const status = await response.json()

        console.log(`[${timestamp}] 📊 Poll #${pollCount}: RAW API Response:`, JSON.stringify(status, null, 2))
        console.log(`[${timestamp}] 📊 Poll #${pollCount}: Parsed status:`, {
          scan_id: status.scan_id,
          status: status.status,
          progress: status.progress,
          message: status.message,
          files_scanned: status.files_scanned,
          total_files: status.total_files,
          nodes_found: status.nodes_found,
          eta: status.eta
        })

        // Log previous state for comparison
        console.log(`[${timestamp}] 🔍 Poll #${pollCount}: Current scanStatus state BEFORE update:`, scanStatus)

        // Update state
        console.log(`[${timestamp}] ⚡ Poll #${pollCount}: Calling setScanStatus with new data...`)
        setScanStatus(status)

        console.log(`[${timestamp}] ✓ Poll #${pollCount}: setScanStatus called successfully`)

        if (status.status === 'completed') {
          console.log(`[${timestamp}] ✅ Poll #${pollCount}: Scan completed! Stopping poll and loading results.`)
          clearInterval(pollInterval)
          setScanning(false)
          loadScanResults(id)
        } else if (status.status === 'failed') {
          console.error(`[${timestamp}] ❌ Poll #${pollCount}: Scan failed! Message: ${status.message}`)
          clearInterval(pollInterval)
          setScanning(false)
        } else {
          console.log(`[${timestamp}] ⏳ Poll #${pollCount}: Scan still in progress... (${status.status})`)
        }
      } catch (error) {
        console.error(`[${timestamp}] ❌ Poll #${pollCount}: Error during polling:`, error)
      }
    }, 1000)

    // Stop polling after 10 minutes
    setTimeout(() => {
      console.log('⏱️ 10 minute timeout reached, stopping poll')
      clearInterval(pollInterval)
    }, 600000)
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
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl animate-bounce">🪅</span>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">
                        {scanStatus.status === 'initializing' && 'Initializing...'}
                        {scanStatus.status === 'discovering' && 'Discovering Files...'}
                        {scanStatus.status === 'scanning' && 'Scanning Your Code...'}
                        {scanStatus.status === 'queued' && 'Queued...'}
                      </h2>
                      <p className="text-sm text-gray-500">{scanStatus.message}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                      {scanStatus.progress.toFixed(0)}%
                    </div>
                    {scanStatus.eta && scanStatus.status === 'scanning' && (
                      <div className="text-xs text-gray-500">
                        ⏱️ ETA: {scanStatus.eta}
                      </div>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
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

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-purple-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {scanStatus.files_scanned.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600">Files Processed</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {scanStatus.total_files ? scanStatus.total_files.toLocaleString() : '...'}
                    </div>
                    <div className="text-xs text-gray-600">Total Files</div>
                  </div>
                  <div className="bg-pink-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-pink-600">
                      {scanStatus.nodes_found.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600">Nodes Found</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-green-600 capitalize">
                      {scanStatus.status}
                    </div>
                    <div className="text-xs text-gray-600">Status</div>
                  </div>
                </div>
              </div>
            )}

            {/* Scan Results */}
            {scanResults && (() => {
              // Calculate metrics
              const nodes = scanResults.graph.nodes
              const edges = scanResults.graph.edges

              const nodesByType = nodes.reduce((acc: any, node) => {
                acc[node.type] = (acc[node.type] || 0) + 1
                return acc
              }, {})

              const dbNodes = nodes.filter(n => n.type.includes('database'))
              const apiNodes = nodes.filter(n => n.type.includes('api'))
              const fileNodes = nodes.filter(n => n.type.includes('file'))
              const uiNodes = nodes.filter(n => n.type.includes('ui') || n.name.includes('Click') || n.name.includes('Button'))

              // Extract unique database tables
              const tables = [...new Set(dbNodes.filter(n => n.table_name).map(n => n.table_name))]
              const tableOperations = tables.map(table => {
                const tableNodes = dbNodes.filter(n => n.table_name === table)
                const reads = tableNodes.filter(n => n.type.includes('read')).length
                const writes = tableNodes.filter(n => n.type.includes('write')).length
                const files = [...new Set(tableNodes.map(n => n.location.file_path))]
                return { table, reads, writes, files, nodes: tableNodes }
              })

              // Extract unique API endpoints
              const endpoints = [...new Set(apiNodes.filter(n => n.endpoint).map(n => n.endpoint))]

              return (
                <div className="space-y-6">
                  {/* Metrics Dashboard */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center space-x-2 mb-4">
                      <span className="text-2xl">📊</span>
                      <h2 className="text-xl font-bold text-gray-900">Metrics & Analytics</h2>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                        <div className="text-3xl font-bold text-purple-600">{scanResults.files_scanned}</div>
                        <div className="text-sm text-gray-600">Files Scanned</div>
                      </div>
                      <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                        <div className="text-3xl font-bold text-blue-600">{nodes.length}</div>
                        <div className="text-sm text-gray-600">Total Nodes</div>
                      </div>
                      <div className="text-center p-4 bg-gradient-to-br from-pink-50 to-pink-100 rounded-lg">
                        <div className="text-3xl font-bold text-pink-600">{edges.length}</div>
                        <div className="text-sm text-gray-600">Connections</div>
                      </div>
                      <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                        <div className="text-3xl font-bold text-green-600">{(scanResults.scan_duration || 0).toFixed(1)}s</div>
                        <div className="text-sm text-gray-600">Scan Duration</div>
                      </div>
                    </div>

                    {/* Workflow Type Breakdown */}
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Workflow Type Breakdown</h3>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {Object.entries(nodesByType).map(([type, count]) => (
                          <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm font-medium text-gray-700 capitalize">
                              {type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-lg font-bold text-gray-900">{count as number}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3 border-l-4 border-green-500 bg-green-50 rounded">
                        <div className="text-2xl font-bold text-green-600">{dbNodes.length}</div>
                        <div className="text-xs text-gray-600">Database Operations</div>
                      </div>
                      <div className="p-3 border-l-4 border-blue-500 bg-blue-50 rounded">
                        <div className="text-2xl font-bold text-blue-600">{apiNodes.length}</div>
                        <div className="text-xs text-gray-600">API Calls</div>
                      </div>
                      <div className="p-3 border-l-4 border-purple-500 bg-purple-50 rounded">
                        <div className="text-2xl font-bold text-purple-600">{fileNodes.length}</div>
                        <div className="text-xs text-gray-600">File Operations</div>
                      </div>
                      <div className="p-3 border-l-4 border-pink-500 bg-pink-50 rounded">
                        <div className="text-2xl font-bold text-pink-600">{tables.length}</div>
                        <div className="text-xs text-gray-600">Unique Tables</div>
                      </div>
                    </div>
                  </div>

                  {/* Database Tables */}
                  {tables.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <span className="text-2xl">🗄️</span>
                        <h2 className="text-xl font-bold text-gray-900">Database Tables</h2>
                      </div>
                      <div className="space-y-3">
                        {tableOperations.map(({ table, reads, writes, files, nodes: tableNodes }) => (
                          <div key={table} className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-lg font-bold text-gray-900">{table}</h3>
                              <div className="flex items-center space-x-3">
                                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-semibold">
                                  📖 {reads} reads
                                </span>
                                <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-sm font-semibold">
                                  ✏️ {writes} writes
                                </span>
                              </div>
                            </div>
                            <div className="text-sm text-gray-600 mb-2">
                              <strong>Used in {files.length} file{files.length !== 1 ? 's' : ''}:</strong>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {files.map(file => (
                                <span key={file} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  {file.split('/').pop()}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Database Relationship Diagram */}
                  {tables.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <span className="text-2xl">🔗</span>
                        <h2 className="text-xl font-bold text-gray-900">Database Relationship Diagram</h2>
                      </div>
                      <div className="bg-gray-50 p-6 rounded-lg">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {tableOperations.map(({ table, reads, writes }) => (
                            <div key={table} className="bg-white border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                              <div className="text-center border-b border-gray-200 pb-2 mb-2">
                                <h4 className="font-bold text-gray-900">{table}</h4>
                              </div>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Read Operations:</span>
                                  <span className="font-semibold text-green-600">{reads}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Write Operations:</span>
                                  <span className="font-semibold text-orange-600">{writes}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Total Operations:</span>
                                  <span className="font-semibold text-purple-600">{reads + writes}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* API Endpoints */}
                  {endpoints.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <span className="text-2xl">🌐</span>
                        <h2 className="text-xl font-bold text-gray-900">API Endpoints</h2>
                      </div>
                      <div className="space-y-2">
                        {endpoints.map(endpoint => {
                          const endpointNodes = apiNodes.filter(n => n.endpoint === endpoint)
                          const methods = [...new Set(endpointNodes.map(n => n.http_method || n.method).filter(Boolean))]
                          return (
                            <div key={endpoint} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                              <div className="flex items-center space-x-3">
                                {methods.map(method => (
                                  <span key={method} className={`px-2 py-1 rounded text-xs font-bold ${
                                    method === 'GET' ? 'bg-green-500 text-white' :
                                    method === 'POST' ? 'bg-blue-500 text-white' :
                                    method === 'PUT' ? 'bg-yellow-500 text-white' :
                                    method === 'DELETE' ? 'bg-red-500 text-white' :
                                    'bg-gray-500 text-white'
                                  }`}>
                                    {method}
                                  </span>
                                ))}
                                <code className="text-sm font-mono text-gray-900">{endpoint}</code>
                              </div>
                              <span className="text-sm text-gray-500">{endpointNodes.length} call{endpointNodes.length !== 1 ? 's' : ''}</span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Data Workflow Visualization */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center space-x-2 mb-4">
                      <span className="text-2xl">📈</span>
                      <h2 className="text-xl font-bold text-gray-900">Data Workflow Visualization</h2>
                    </div>
                    <div className="bg-gradient-to-r from-purple-50 via-blue-50 to-green-50 p-8 rounded-lg">
                      <div className="flex items-center justify-around">
                        <div className="text-center">
                          <div className="w-24 h-24 bg-purple-500 rounded-full flex items-center justify-center text-white text-3xl mb-2 shadow-lg">
                            🖥️
                          </div>
                          <div className="font-bold text-gray-900">UI Layer</div>
                          <div className="text-sm text-gray-600">{uiNodes.length} interactions</div>
                        </div>
                        <div className="text-4xl text-gray-400">→</div>
                        <div className="text-center">
                          <div className="w-24 h-24 bg-blue-500 rounded-full flex items-center justify-center text-white text-3xl mb-2 shadow-lg">
                            🌐
                          </div>
                          <div className="font-bold text-gray-900">API Layer</div>
                          <div className="text-sm text-gray-600">{apiNodes.length} endpoints</div>
                        </div>
                        <div className="text-4xl text-gray-400">→</div>
                        <div className="text-center">
                          <div className="w-24 h-24 bg-green-500 rounded-full flex items-center justify-center text-white text-3xl mb-2 shadow-lg">
                            🗄️
                          </div>
                          <div className="font-bold text-gray-900">Data Layer</div>
                          <div className="text-sm text-gray-600">{dbNodes.length} operations</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* UI Workflow Visualization */}
                  {uiNodes.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <span className="text-2xl">🎨</span>
                        <h2 className="text-xl font-bold text-gray-900">UI Workflow Visualization</h2>
                      </div>
                      <div className="space-y-3">
                        {uiNodes.slice(0, 10).map(node => (
                          <div key={node.id} className="border-l-4 border-purple-500 pl-4 py-2 bg-purple-50 rounded">
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="font-bold text-purple-900">{node.name}</span>
                                <p className="text-sm text-gray-600">{node.description}</p>
                              </div>
                              <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                                {node.location.file_path.split('/').pop()}:{node.location.line_number}
                              </span>
                            </div>
                          </div>
                        ))}
                        {uiNodes.length > 10 && (
                          <div className="text-center text-sm text-gray-500">
                            + {uiNodes.length - 10} more UI interactions
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Full Workflow Diagram */}
                  {diagram && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <span className="text-2xl">🗺️</span>
                        <h2 className="text-xl font-bold text-gray-900">Complete Workflow Diagram</h2>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg overflow-auto">
                        <pre className="text-sm text-gray-700">{diagram}</pre>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Copy this Mermaid diagram and paste it into{' '}
                        <a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">
                          mermaid.live
                        </a>{' '}
                        to visualize the complete workflow
                      </p>
                    </div>
                  )}

                  {/* All Detected Workflows */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center space-x-2 mb-4">
                      <span className="text-2xl">📋</span>
                      <h2 className="text-xl font-bold text-gray-900">All Detected Workflows ({nodes.length})</h2>
                    </div>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {nodes.map((node) => (
                        <div
                          key={node.id}
                          className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
                                node.type.includes('database') ? 'bg-green-100 text-green-800' :
                                node.type.includes('api') ? 'bg-blue-100 text-blue-800' :
                                node.type.includes('file') ? 'bg-yellow-100 text-yellow-800' :
                                'bg-purple-100 text-purple-800'
                              }`}>
                                {node.type.toUpperCase().replace(/_/g, ' ')}
                              </span>
                              <span className="ml-2 font-medium text-gray-900">{node.name}</span>
                              {node.table_name && (
                                <span className="ml-2 text-xs text-gray-600">→ {node.table_name}</span>
                              )}
                              {node.endpoint && (
                                <span className="ml-2 text-xs text-gray-600">→ {node.endpoint}</span>
                              )}
                            </div>
                            <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
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
              )
            })()}

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
