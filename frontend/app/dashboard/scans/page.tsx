'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface ScanListItem {
  scan_id: string
  repository_path: string
  repository_name: string
  scan_type: string
  performed_by: string
  created_at: string
  completed_at: string | null
  status: string
  viewed: boolean
  files_scanned: number
  nodes_found: number
  scan_duration: number
}

interface ScanListResponse {
  total: number
  scans: ScanListItem[]
}

export default function ScansPage() {
  const router = useRouter()
  const [scans, setScans] = useState<ScanListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    loadScans()
  }, [])

  const loadScans = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scans?limit=100`)

      if (!response.ok) {
        throw new Error(`Failed to load scans: ${response.statusText}`)
      }

      const data: ScanListResponse = await response.json()
      setScans(data.scans)
      setTotal(data.total)
    } catch (err) {
      console.error('Error loading scans:', err)
      setError(err instanceof Error ? err.message : 'Failed to load scans')
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}m ${secs}s`
  }

  const getStatusBadge = (status: string) => {
    const statusStyles: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      scanning: 'bg-blue-100 text-blue-800',
      discovering: 'bg-yellow-100 text-yellow-800',
      queued: 'bg-gray-100 text-gray-800',
      error: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800',
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    )
  }

  const handleScanClick = (scanId: string) => {
    router.push(`/dashboard/scans/${scanId}`)
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600 text-lg">Loading scans...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 font-semibold">Failed to load scans</p>
          <p className="text-red-600 text-sm mt-2">{error}</p>
          <button
            onClick={loadScans}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Scan History</h1>
        <p className="text-gray-600 mt-2">
          View all code scans and their results. Total scans: {total}
        </p>
      </div>

      {/* Scans Table */}
      {scans.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No scans yet</h3>
          <p className="text-gray-600 mb-6">
            Start your first code scan to see results here.
          </p>
          <button
            onClick={() => router.push('/dashboard/scanner')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Start a Scan
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Repository
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performed By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Files / Nodes
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {scans.map((scan) => (
                  <tr
                    key={scan.scan_id}
                    onClick={() => handleScanClick(scan.scan_id)}
                    className={`cursor-pointer hover:bg-gray-50 transition-colors ${!scan.viewed ? 'bg-blue-50' : ''}`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {!scan.viewed && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full mr-2"></div>
                        )}
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {scan.repository_name}
                          </div>
                          <div className="text-xs text-gray-500 truncate max-w-xs">
                            {scan.repository_path}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 capitalize">
                        {scan.scan_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(scan.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {scan.performed_by}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDate(scan.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {scan.files_scanned} / {scan.nodes_found}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {scan.scan_duration > 0 ? formatDuration(scan.scan_duration) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
