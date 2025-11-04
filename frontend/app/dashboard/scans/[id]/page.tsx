'use client'

import { useEffect, useState, lazy, Suspense } from 'react'
import { useParams, useRouter } from 'next/navigation'
import DashboardNavbar from '@/app/components/DashboardNavbar'
import PinataSpinner from '@/app/components/PinataSpinner'

// Lazy load MermaidDiagram for better performance
const MermaidDiagram = lazy(() => import('../../../components/MermaidDiagram'))

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

interface UIWorkflow {
  id: string
  name: string
  summary: string
  outcome: string
  trigger: {
    name: string
    description: string
    interaction_type: string
    component: string
    location: string
  }
  steps: Array<{
    step_number: number
    title: string
    description: string
    technical_details: string
    icon: string
    node_id: string
  }>
  story: string
}

interface ScanResults {
  scan_id: string
  repository_path: string
  files_scanned: number
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  workflows?: UIWorkflow[]
  scan_time_seconds: number
  scan_duration: number
  errors: string[]
}

type TabType = 'overview' | 'workflows' | 'nodes' | 'database' | 'api' | 'tables'

interface DatabaseTable {
  table_name: string
  read_count: number
  write_count: number
  schema_file: string | null
  schema_line: number | null
  migrations: Array<{
    file_path: string
    migration_name: string
    timestamp: string
    changes: string[]
  }>
  schema: {
    columns: Record<string, {
      name: string
      data_type: string
      nullable: boolean
      primary_key: boolean
      foreign_key: string | null
      default: string | null
    }>
    indexes: string[]
    relationships: string[]
  }
}

export default function ScanDetailPage() {
  const params = useParams()
  const router = useRouter()
  const scanId = params?.id as string

  const [scanResults, setScanResults] = useState<ScanResults | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [selectedWorkflow, setSelectedWorkflow] = useState<UIWorkflow | null>(null)
  const [databaseTables, setDatabaseTables] = useState<Record<string, DatabaseTable> | null>(null)
  const [loadingTables, setLoadingTables] = useState(false)

  useEffect(() => {
    if (scanId) {
      loadScanResults()
      markAsViewed()
    }
  }, [scanId])

  const loadScanResults = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scan/${scanId}/results`)

      if (!response.ok) {
        throw new Error(`Failed to load scan results: ${response.statusText}`)
      }

      const data: ScanResults = await response.json()
      setScanResults(data)

      // Auto-select first workflow if available
      if (data.workflows && data.workflows.length > 0) {
        setSelectedWorkflow(data.workflows[0])
      }
    } catch (err) {
      console.error('Error loading scan results:', err)
      setError(err instanceof Error ? err.message : 'Failed to load scan results')
    } finally {
      setIsLoading(false)
    }
  }

  const markAsViewed = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      await fetch(`${apiUrl}/api/v1/scanner/scans/${scanId}/viewed`, {
        method: 'PATCH',
      })
    } catch (err) {
      console.error('Failed to mark scan as viewed:', err)
    }
  }

  const loadDatabaseTables = async () => {
    if (databaseTables) return // Already loaded

    try {
      setLoadingTables(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scan/${scanId}/database-tables`)

      if (response.ok) {
        const data = await response.json()
        setDatabaseTables(data.tables)
      }
    } catch (err) {
      console.error('Failed to load database tables:', err)
    } finally {
      setLoadingTables(false)
    }
  }

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab)
    if (tab === 'tables') {
      loadDatabaseTables()
    }
  }

  const getDatabaseNodes = () => {
    if (!scanResults) return []
    return scanResults.nodes.filter((node) =>
      node.type.includes('database')
    )
  }

  const getApiNodes = () => {
    if (!scanResults) return []
    return scanResults.nodes.filter((node) =>
      node.type.includes('api')
    )
  }

  const renderOverviewTab = () => {
    if (!scanResults) return null

    const dbNodes = getDatabaseNodes()
    const apiNodes = getApiNodes()

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-blue-600 text-sm font-medium">Files Scanned</div>
            <div className="text-3xl font-bold text-blue-900 mt-1">
              {scanResults.files_scanned}
            </div>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-green-600 text-sm font-medium">Nodes Found</div>
            <div className="text-3xl font-bold text-green-900 mt-1">
              {scanResults.nodes.length}
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="text-purple-600 text-sm font-medium">UI Workflows</div>
            <div className="text-3xl font-bold text-purple-900 mt-1">
              {scanResults.workflows?.length || 0}
            </div>
          </div>
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="text-orange-600 text-sm font-medium">Scan Duration</div>
            <div className="text-3xl font-bold text-orange-900 mt-1">
              {scanResults.scan_duration.toFixed(1)}s
            </div>
          </div>
        </div>

        {/* Repository Info */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Repository Information</h3>
          <div className="space-y-2">
            <div className="flex">
              <span className="font-medium text-gray-700 w-32">Path:</span>
              <span className="text-gray-900">{scanResults.repository_path}</span>
            </div>
            <div className="flex">
              <span className="font-medium text-gray-700 w-32">Scan ID:</span>
              <span className="text-gray-600 font-mono text-sm">{scanResults.scan_id}</span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Database Operations</h3>
            <p className="text-3xl font-bold text-blue-600">{dbNodes.length}</p>
            <p className="text-sm text-gray-600 mt-1">database interactions detected</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">API Endpoints</h3>
            <p className="text-3xl font-bold text-green-600">{apiNodes.length}</p>
            <p className="text-sm text-gray-600 mt-1">API calls detected</p>
          </div>
        </div>

        {/* Errors */}
        {scanResults.errors && scanResults.errors.length > 0 && (
          <div className="bg-red-50 rounded-lg border border-red-200 p-6">
            <h3 className="text-lg font-semibold text-red-900 mb-3">Errors</h3>
            <ul className="space-y-2">
              {scanResults.errors.map((error, index) => (
                <li key={index} className="text-red-700 text-sm">
                  • {error}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  const renderWorkflowsTab = () => {
    if (!scanResults?.workflows || scanResults.workflows.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-gray-600">No UI workflows detected in this scan</p>
        </div>
      )
    }

    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflow List */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Workflows ({scanResults.workflows.length})
          </h3>
          {scanResults.workflows.map((workflow) => (
            <div
              key={workflow.id}
              onClick={() => setSelectedWorkflow(workflow)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedWorkflow?.id === workflow.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-blue-300'
              }`}
            >
              <h4 className="font-semibold text-gray-900">{workflow.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{workflow.summary}</p>
              <div className="mt-2 text-xs text-gray-500">
                {workflow.steps.length} steps
              </div>
            </div>
          ))}
        </div>

        {/* Workflow Details */}
        <div className="lg:col-span-2">
          {selectedWorkflow ? (
            <div className="space-y-6">
              {/* Workflow Header */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {selectedWorkflow.name}
                </h3>
                <p className="text-gray-700 mb-4">{selectedWorkflow.summary}</p>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-900">User Action</p>
                  <p className="text-blue-700">{selectedWorkflow.trigger.description}</p>
                </div>
              </div>

              {/* Workflow Steps */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Workflow Steps</h4>
                <div className="space-y-4">
                  {selectedWorkflow.steps.map((step) => (
                    <div key={step.step_number} className="border-l-4 border-blue-500 pl-4 py-2">
                      <div className="flex items-start">
                        <span className="text-2xl mr-3">{step.icon}</span>
                        <div className="flex-1">
                          <h5 className="font-semibold text-gray-900">
                            Step {step.step_number}: {step.title}
                          </h5>
                          <p className="text-gray-700 mt-1">{step.description}</p>
                          <p className="text-sm text-gray-500 mt-2 italic">
                            Technical: {step.technical_details}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Outcome */}
              <div className="bg-green-50 rounded-lg border border-green-200 p-6">
                <h4 className="text-lg font-semibold text-green-900 mb-2">Outcome</h4>
                <p className="text-green-700">{selectedWorkflow.outcome}</p>
              </div>

              {/* Workflow Diagram */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Visual Diagram</h4>
                <WorkflowDiagram scanId={scanId} workflowId={selectedWorkflow.id} />
              </div>

              {/* Workflow Story */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Workflow Story</h4>
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-gray-700">
                    {selectedWorkflow.story}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600">Select a workflow to view details</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderNodesTab = () => {
    if (!scanResults) return null

    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            All Nodes ({scanResults.nodes.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Location
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {scanResults.nodes.map((node) => (
                  <tr key={node.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {node.name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {node.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {node.location.file_path}:{node.location.line_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {node.table_name && <div>Table: {node.table_name}</div>}
                      {node.endpoint && (
                        <div>
                          {node.http_method} {node.endpoint}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }

  const renderDatabaseTab = () => {
    const dbNodes = getDatabaseNodes()

    if (dbNodes.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">💾</div>
          <p className="text-gray-600">No database operations detected in this scan</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Database Operations ({dbNodes.length})
          </h3>
          <div className="space-y-3">
            {dbNodes.map((node) => (
              <div key={node.id} className="border-l-4 border-blue-500 pl-4 py-3 bg-blue-50 rounded">
                <h4 className="font-semibold text-gray-900">{node.name}</h4>
                <p className="text-sm text-gray-700 mt-1">{node.description}</p>
                {node.table_name && (
                  <p className="text-sm text-blue-700 mt-2">
                    <span className="font-medium">Table:</span> {node.table_name}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  {node.location.file_path}:{node.location.line_number}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderApiTab = () => {
    const apiNodes = getApiNodes()

    if (apiNodes.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🌐</div>
          <p className="text-gray-600">No API endpoints detected in this scan</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            API Endpoints ({apiNodes.length})
          </h3>
          <div className="space-y-3">
            {apiNodes.map((node) => (
              <div key={node.id} className="border-l-4 border-green-500 pl-4 py-3 bg-green-50 rounded">
                <h4 className="font-semibold text-gray-900">{node.name}</h4>
                <p className="text-sm text-gray-700 mt-1">{node.description}</p>
                {node.endpoint && (
                  <p className="text-sm text-green-700 mt-2">
                    <span className="font-medium px-2 py-1 bg-green-200 rounded text-xs mr-2">
                      {node.http_method || 'GET'}
                    </span>
                    {node.endpoint}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  {node.location.file_path}:{node.location.line_number}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderTablesTab = () => {
    if (loadingTables) {
      return (
        <div className="flex justify-center py-12">
          <PinataSpinner size="lg" message="Loading database tables..." />
        </div>
      )
    }

    if (!databaseTables || Object.keys(databaseTables).length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🗄️</div>
          <p className="text-gray-600">No database tables detected in this scan</p>
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {Object.entries(databaseTables).map(([tableName, table]) => (
          <div key={tableName} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Table Header */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{table.table_name}</h3>
                  {table.schema_file && (
                    <p className="text-sm text-gray-600 mt-1">
                      📄 {table.schema_file}:{table.schema_line}
                    </p>
                  )}
                </div>
                <div className="flex space-x-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{table.read_count}</div>
                    <div className="text-xs text-gray-600">Reads</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{table.write_count}</div>
                    <div className="text-xs text-gray-600">Writes</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Migrations */}
              {table.migrations && table.migrations.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    📝 Migrations ({table.migrations.length})
                  </h4>
                  <div className="space-y-2">
                    {table.migrations.map((migration, idx) => (
                      <div key={idx} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{migration.migration_name}</p>
                            <p className="text-sm text-gray-600 mt-1">
                              {migration.file_path.split('/').pop()}
                            </p>
                          </div>
                          <span className="text-xs text-gray-500 font-mono">
                            {migration.timestamp}
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {migration.changes.map((change, cidx) => (
                            <span key={cidx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                              {change}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Current Schema */}
              {table.schema && Object.keys(table.schema.columns).length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    🔑 Current Schema (Post-Migrations)
                  </h4>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-sm text-green-400 font-mono">
                      {JSON.stringify(table.schema, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Columns Table */}
              {table.schema && Object.keys(table.schema.columns).length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    📋 Columns ({Object.keys(table.schema.columns).length})
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Column Name
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Data Type
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Constraints
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Foreign Key
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {Object.entries(table.schema.columns).map(([colName, col]) => (
                          <tr key={colName}>
                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                              {col.name}
                              {col.primary_key && (
                                <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                                  PK
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              <span className="font-mono">{col.data_type}</span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {col.nullable ? (
                                <span className="text-gray-400">Nullable</span>
                              ) : (
                                <span className="text-red-600 font-medium">NOT NULL</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {col.foreign_key ? (
                                <span className="text-blue-600">{col.foreign_key}</span>
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <DashboardNavbar />
        <div className="p-6">
          <div className="flex items-center justify-center h-64">
            <PinataSpinner size="lg" message="Loading scan results..." />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <DashboardNavbar />
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700 font-semibold">Failed to load scan results</p>
            <p className="text-red-600 text-sm mt-2">{error}</p>
            <button
              onClick={() => router.push('/dashboard/scans')}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Back to Scans
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardNavbar />
      <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/dashboard/scans')}
          className="text-blue-600 hover:text-blue-700 mb-4 flex items-center"
        >
          ← Back to Scans
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Scan Results</h1>
        {scanResults && (
          <p className="text-gray-600 mt-2">{scanResults.repository_path}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'workflows', label: 'UI Workflows', icon: '🔄' },
            { id: 'tables', label: 'Database Tables', icon: '🗄️' },
            { id: 'nodes', label: 'All Nodes', icon: '🔍' },
            { id: 'database', label: 'Database', icon: '💾' },
            { id: 'api', label: 'API Endpoints', icon: '🌐' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id as TabType)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'workflows' && renderWorkflowsTab()}
        {activeTab === 'tables' && renderTablesTab()}
        {activeTab === 'nodes' && renderNodesTab()}
        {activeTab === 'database' && renderDatabaseTab()}
        {activeTab === 'api' && renderApiTab()}
      </div>
      </div>
    </div>
  )
}

function WorkflowDiagram({ scanId, workflowId }: { scanId: string; workflowId: string }) {
  const [diagram, setDiagram] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadDiagram()
  }, [scanId, workflowId])

  const loadDiagram = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(
        `${apiUrl}/api/v1/scanner/scan/${scanId}/workflows/${workflowId}/diagram`
      )

      if (response.ok) {
        const data = await response.json()
        setDiagram(data.diagram)
      }
    } catch (err) {
      console.error('Failed to load diagram:', err)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <PinataSpinner size="md" message="Loading diagram..." />
      </div>
    )
  }

  if (!diagram) {
    return <div className="text-center py-8 text-gray-600">Diagram not available</div>
  }

  return (
    <Suspense fallback={<PinataSpinner size="md" message="Rendering diagram..." />}>
      <MermaidDiagram chart={diagram} className="bg-gray-50 p-4 rounded-lg" />
    </Suspense>
  )
}
