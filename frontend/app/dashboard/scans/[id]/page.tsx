'use client'

import { useEffect, useState, lazy, Suspense } from 'react'
import { useParams, useRouter } from 'next/navigation'
import DashboardNavbar from '@/app/components/DashboardNavbar'
import PinataSpinner from '@/app/components/PinataSpinner'
import { useTableBookmarks } from '@/app/hooks/useTableBookmarks'
import { useApiBookmarks } from '@/app/hooks/useApiBookmarks'
import { useComponentBookmarks } from '@/app/hooks/useComponentBookmarks'

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

type TabType = 'overview' | 'workflows' | 'nodes' | 'database' | 'api' | 'tables' | 'components' | 'pages' | 'dependencies'

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

interface APIRoute {
  route_path: string
  http_method: string
  file_path: string | null
  line_number: number | null
  handler_name: string | null
  request_headers: Array<{
    name: string
    required: boolean
    description: string
  }>
  request_payload: Record<string, {
    field_name: string
    data_type: string
    required: boolean
    description: string
  }>
  response_payload: Record<string, {
    field_name: string
    data_type: string
    required: boolean
    description: string
  }>
  middleware: Array<{
    name: string
    type: string
    description: string
  }>
  call_count: number
  error_count: number
  authentication_required: boolean
  rate_limited: boolean
  tags: string[]
}

interface Component {
  name: string
  type: string
  file_path: string
  line_number: number | null
  description: string | null
  used_in: Array<{
    used_in_file: string
    used_in_component: string
    line_number: number | null
  }>
  uses_components: string[]
  handlers: Array<{
    name: string
    event_type: string
    line_number: number | null
  }>
  data_fields: Array<{
    name: string
    data_type: string
    source: string
    required: boolean
    default_value: string | null
  }>
  html_structure: string | null
  has_form: boolean
  lines_of_code: number
  complexity_score: number
}

interface Page {
  name: string
  path: string
  file_path: string
  line_number: number | null
  components: string[]
  route_params: string[]
  query_params: string[]
  title: string | null
  requires_auth: boolean
  layout: string | null
  component_count: number
  api_calls_count: number
  database_queries_count: number
}

interface Dependency {
  name: string
  current_version: string
  latest_version: string | null
  package_file: string | null
  package_manager: string | null
  is_used: boolean
  usage_count: number
  used_in_files: string[]
  is_outdated: boolean
  versions_behind: number
  major_update_available: boolean
  minor_update_available: boolean
  patch_update_available: boolean
  is_dev_dependency: boolean
  is_peer_dependency: boolean
  has_security_warning: boolean
  is_deprecated: boolean
  has_conflict: boolean
  conflict_details: string | null
  description: string | null
  license: string | null
  last_published: string | null
}

interface DependencyConflict {
  package_name: string
  versions: string[]
  locations: string[]
  severity: string
}

interface DependencyMetrics {
  total_dependencies: number
  outdated_count: number
  unused_count: number
  security_warnings: number
  deprecated_count: number
  conflict_count: number
  major_updates_available: number
  minor_updates_available: number
  patch_updates_available: number
  avg_versions_behind: number
  health_score: number
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
  const [tableSearchQuery, setTableSearchQuery] = useState('')
  const [apiRoutes, setApiRoutes] = useState<Record<string, APIRoute> | null>(null)
  const [loadingRoutes, setLoadingRoutes] = useState(false)
  const [routeSearchQuery, setRouteSearchQuery] = useState('')
  const [components, setComponents] = useState<Record<string, Component> | null>(null)
  const [loadingComponents, setLoadingComponents] = useState(false)
  const [componentSearchQuery, setComponentSearchQuery] = useState('')
  const [pages, setPages] = useState<Record<string, Page> | null>(null)
  const [loadingPages, setLoadingPages] = useState(false)
  const [pageSearchQuery, setPageSearchQuery] = useState('')
  const [dependencies, setDependencies] = useState<Record<string, Dependency> | null>(null)
  const [dependencyConflicts, setDependencyConflicts] = useState<DependencyConflict[] | null>(null)
  const [dependencyMetrics, setDependencyMetrics] = useState<DependencyMetrics | null>(null)
  const [loadingDependencies, setLoadingDependencies] = useState(false)
  const [dependencySearchQuery, setDependencySearchQuery] = useState('')

  // Bookmark management for tables
  const {
    bookmarkedTables,
    toggleBookmark,
    isBookmarked,
    canAddMoreBookmarks,
    getBookmarkCount,
    MAX_BOOKMARKS,
  } = useTableBookmarks(scanId)

  // Bookmark management for API routes
  const {
    bookmarkedRoutes,
    toggleBookmark: toggleRouteBookmark,
    isBookmarked: isRouteBookmarked,
    canAddMoreBookmarks: canAddMoreRouteBookmarks,
    getBookmarkCount: getRouteBookmarkCount,
    MAX_BOOKMARKS: MAX_ROUTE_BOOKMARKS,
  } = useApiBookmarks(scanId)

  // Bookmark management for components
  const {
    bookmarkedComponents,
    toggleBookmark: toggleComponentBookmark,
    isBookmarked: isComponentBookmarked,
    canAddMoreBookmarks: canAddMoreComponentBookmarks,
    getBookmarkCount: getComponentBookmarkCount,
    MAX_BOOKMARKS: MAX_COMPONENT_BOOKMARKS,
  } = useComponentBookmarks(scanId)

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

  const loadApiRoutes = async () => {
    if (apiRoutes) return // Already loaded

    try {
      setLoadingRoutes(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scan/${scanId}/api-routes`)

      if (response.ok) {
        const data = await response.json()
        setApiRoutes(data.routes)
      }
    } catch (err) {
      console.error('Failed to load API routes:', err)
    } finally {
      setLoadingRoutes(false)
    }
  }

  const loadComponents = async () => {
    if (components) return // Already loaded

    try {
      setLoadingComponents(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scan/${scanId}/components`)

      if (response.ok) {
        const data = await response.json()
        setComponents(data.components)
      }
    } catch (err) {
      console.error('Failed to load components:', err)
    } finally {
      setLoadingComponents(false)
    }
  }

  const loadPages = async () => {
    if (pages) return // Already loaded

    try {
      setLoadingPages(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scan/${scanId}/pages`)

      if (response.ok) {
        const data = await response.json()
        setPages(data.pages)
      }
    } catch (err) {
      console.error('Failed to load pages:', err)
    } finally {
      setLoadingPages(false)
    }
  }

  const loadDependencies = async () => {
    if (dependencies) return // Already loaded

    try {
      setLoadingDependencies(true)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/scanner/scan/${scanId}/dependencies`)

      if (response.ok) {
        const data = await response.json()
        setDependencies(data.dependencies)
        setDependencyConflicts(data.conflicts)
        setDependencyMetrics(data.metrics)
      }
    } catch (err) {
      console.error('Failed to load dependencies:', err)
    } finally {
      setLoadingDependencies(false)
    }
  }

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab)
    if (tab === 'tables') {
      loadDatabaseTables()
    }
    if (tab === 'api') {
      loadApiRoutes()
    }
    if (tab === 'components') {
      loadComponents()
    }
    if (tab === 'pages') {
      loadPages()
    }
    if (tab === 'dependencies') {
      loadDependencies()
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
    if (loadingRoutes) {
      return (
        <div className="flex justify-center py-12">
          <PinataSpinner size="lg" message="Loading API routes..." />
        </div>
      )
    }

    if (!apiRoutes || Object.keys(apiRoutes).length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🌐</div>
          <p className="text-gray-600">No API routes detected in this scan</p>
        </div>
      )
    }

    // Calculate high-traffic threshold (routes with calls > 75th percentile)
    const allRoutes = Object.values(apiRoutes)
    const callCounts = allRoutes.map(r => r.call_count)
    const sortedCalls = [...callCounts].sort((a, b) => b - a)
    const highTrafficThreshold = sortedCalls[Math.floor(sortedCalls.length * 0.25)] || 10

    const isHighTraffic = (route: APIRoute) => {
      return route.call_count >= highTrafficThreshold
    }

    // Filter routes by search query
    const filteredRoutes = Object.entries(apiRoutes).filter(([routeKey, route]) => {
      if (!routeSearchQuery) return true
      const searchLower = routeSearchQuery.toLowerCase()
      return (
        route.route_path.toLowerCase().includes(searchLower) ||
        route.http_method.toLowerCase().includes(searchLower) ||
        route.tags.some(tag => tag.toLowerCase().includes(searchLower))
      )
    })

    // Sort routes: bookmarked first, then by traffic, then alphabetically
    const sortedRoutes = [...filteredRoutes].sort(([keyA, routeA], [keyB, routeB]) => {
      const aBookmarked = isRouteBookmarked(keyA)
      const bBookmarked = isRouteBookmarked(keyB)

      // Bookmarked routes first
      if (aBookmarked && !bBookmarked) return -1
      if (!aBookmarked && bBookmarked) return 1

      // Then by call count (descending)
      if (routeA.call_count !== routeB.call_count) return routeB.call_count - routeA.call_count

      // Finally alphabetically by path
      return routeA.route_path.localeCompare(routeB.route_path)
    })

    const handleRouteBookmarkClick = (routeKey: string) => {
      const success = toggleRouteBookmark(routeKey)
      if (!success && !isRouteBookmarked(routeKey)) {
        alert(`You can only bookmark up to ${MAX_ROUTE_BOOKMARKS} routes.`)
      }
    }

    const getMethodColor = (method: string) => {
      const colors: Record<string, string> = {
        GET: 'bg-green-100 text-green-700 border-green-300',
        POST: 'bg-blue-100 text-blue-700 border-blue-300',
        PUT: 'bg-yellow-100 text-yellow-700 border-yellow-300',
        PATCH: 'bg-orange-100 text-orange-700 border-orange-300',
        DELETE: 'bg-red-100 text-red-700 border-red-300',
      }
      return colors[method.toUpperCase()] || 'bg-gray-100 text-gray-700 border-gray-300'
    }

    return (
      <div className="space-y-6">
        {/* Search and Bookmark Info */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex-1 w-full sm:w-auto">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search routes by path, method, or tag..."
                  value={routeSearchQuery}
                  onChange={(e) => setRouteSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <svg
                  className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">Bookmarks:</span>
                <span className="font-semibold text-blue-600">
                  {getRouteBookmarkCount()} / {MAX_ROUTE_BOOKMARKS}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-medium">
                  🔥 High Traffic
                </span>
                <span className="text-gray-600 text-xs">
                  = {highTrafficThreshold}+ calls
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Results count */}
        {routeSearchQuery && (
          <div className="text-sm text-gray-600">
            Found {sortedRoutes.length} of {Object.keys(apiRoutes).length} routes
          </div>
        )}

        {/* API Routes */}
        {sortedRoutes.map(([routeKey, route]) => (
          <div key={routeKey} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Route Header */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 flex-wrap">
                    <span className={`px-3 py-1 rounded-md font-semibold text-sm border ${getMethodColor(route.http_method)}`}>
                      {route.http_method}
                    </span>
                    <h3 className="text-xl font-mono font-bold text-gray-900">{route.route_path}</h3>

                    {/* High Traffic Badge */}
                    {isHighTraffic(route) && (
                      <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-medium">
                        🔥 High Traffic
                      </span>
                    )}

                    {/* Bookmarked Badge */}
                    {isRouteBookmarked(routeKey) && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">
                        ⭐ Bookmarked
                      </span>
                    )}

                    {/* Auth Required Badge */}
                    {route.authentication_required && (
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">
                        🔒 Auth
                      </span>
                    )}

                    {/* Rate Limited Badge */}
                    {route.rate_limited && (
                      <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">
                        ⏱️ Rate Limited
                      </span>
                    )}
                  </div>

                  {route.file_path && (
                    <p className="text-sm text-gray-600 mt-2">
                      📄 {route.file_path}:{route.line_number}
                      {route.handler_name && <span className="ml-2 font-mono text-blue-600">{route.handler_name}()</span>}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-4">
                  {/* Bookmark Button */}
                  <button
                    onClick={() => handleRouteBookmarkClick(routeKey)}
                    className={`p-2 rounded-lg transition-colors ${
                      isRouteBookmarked(routeKey)
                        ? 'bg-yellow-200 text-yellow-700 hover:bg-yellow-300'
                        : canAddMoreRouteBookmarks()
                        ? 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                    disabled={!isRouteBookmarked(routeKey) && !canAddMoreRouteBookmarks()}
                    title={
                      isRouteBookmarked(routeKey)
                        ? 'Remove bookmark'
                        : canAddMoreRouteBookmarks()
                        ? 'Bookmark route'
                        : 'Maximum bookmarks reached'
                    }
                  >
                    <svg
                      className="w-5 h-5"
                      fill={isRouteBookmarked(routeKey) ? 'currentColor' : 'none'}
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                      />
                    </svg>
                  </button>

                  {/* Metrics */}
                  <div className="flex space-x-3">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{route.call_count}</div>
                      <div className="text-xs text-gray-600">Calls</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{route.error_count}</div>
                      <div className="text-xs text-gray-600">Errors</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Route Details */}
            <div className="p-6 space-y-4">
              {/* Tags */}
              {route.tags && route.tags.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {route.tags.map((tag, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Request Headers */}
              {route.request_headers && route.request_headers.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Request Headers</h4>
                  <div className="bg-gray-50 rounded p-3 space-y-1">
                    {route.request_headers.map((header, idx) => (
                      <div key={idx} className="flex items-start space-x-2 text-sm">
                        <span className="font-mono text-blue-600">{header.name}:</span>
                        <span className="text-gray-600">{header.description || 'string'}</span>
                        {header.required && (
                          <span className="text-red-600 text-xs">*required</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Request Payload */}
              {route.request_payload && Object.keys(route.request_payload).length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Request Payload</h4>
                  <div className="bg-blue-50 rounded p-3">
                    <pre className="text-sm font-mono">
                      {JSON.stringify(
                        Object.entries(route.request_payload).reduce((acc, [key, field]) => {
                          acc[field.field_name] = `${field.data_type}${field.required ? ' (required)' : ''}`
                          return acc
                        }, {} as Record<string, string>),
                        null,
                        2
                      )}
                    </pre>
                  </div>
                </div>
              )}

              {/* Response Payload */}
              {route.response_payload && Object.keys(route.response_payload).length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Response Payload</h4>
                  <div className="bg-green-50 rounded p-3">
                    <pre className="text-sm font-mono">
                      {JSON.stringify(
                        Object.entries(route.response_payload).reduce((acc, [key, field]) => {
                          acc[field.field_name] = field.data_type
                          return acc
                        }, {} as Record<string, string>),
                        null,
                        2
                      )}
                    </pre>
                  </div>
                </div>
              )}

              {/* Middleware */}
              {route.middleware && route.middleware.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Middleware</h4>
                  <div className="space-y-2">
                    {route.middleware.map((mw, idx) => (
                      <div key={idx} className="flex items-start space-x-3 bg-purple-50 rounded p-3">
                        <span className="text-xl">⚙️</span>
                        <div>
                          <div className="font-semibold text-gray-900">{mw.name}</div>
                          <div className="text-xs text-gray-600">{mw.type}</div>
                          {mw.description && (
                            <div className="text-sm text-gray-700 mt-1">{mw.description}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error Rate */}
              {route.call_count > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Analytics</h4>
                  <div className="bg-gray-50 rounded p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Error Rate:</span>
                      <span className={`font-semibold ${
                        (route.error_count / route.call_count) > 0.05 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {((route.error_count / route.call_count) * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderComponentsTab = () => {
    if (loadingComponents) {
      return (
        <div className="flex justify-center py-12">
          <PinataSpinner size="lg" message="Loading components..." />
        </div>
      )
    }

    if (!components || Object.keys(components).length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🧩</div>
          <p className="text-gray-600">No components detected in this scan</p>
        </div>
      )
    }

    // Calculate high complexity threshold
    const allComponents = Object.values(components)
    const complexities = allComponents.map(c => c.complexity_score)
    const sortedComplexities = [...complexities].sort((a, b) => b - a)
    const highComplexityThreshold = sortedComplexities[Math.floor(sortedComplexities.length * 0.25)] || 5

    const isHighComplexity = (component: Component) => {
      return component.complexity_score >= highComplexityThreshold
    }

    // Filter by search
    const filteredComponents = Object.entries(components).filter(([name, comp]) => {
      if (!componentSearchQuery) return true
      const searchLower = componentSearchQuery.toLowerCase()
      return (
        name.toLowerCase().includes(searchLower) ||
        comp.file_path.toLowerCase().includes(searchLower) ||
        comp.type.toLowerCase().includes(searchLower)
      )
    })

    // Sort: bookmarked > complexity > alphabetical
    const sortedComponents = [...filteredComponents].sort(([nameA, compA], [nameB, compB]) => {
      const aBookmarked = isComponentBookmarked(nameA)
      const bBookmarked = isComponentBookmarked(nameB)

      if (aBookmarked && !bBookmarked) return -1
      if (!aBookmarked && bBookmarked) return 1

      if (compA.complexity_score !== compB.complexity_score)
        return compB.complexity_score - compA.complexity_score

      return nameA.localeCompare(nameB)
    })

    const handleComponentBookmarkClick = (componentName: string) => {
      const success = toggleComponentBookmark(componentName)
      if (!success && !isComponentBookmarked(componentName)) {
        alert(`You can only bookmark up to ${MAX_COMPONENT_BOOKMARKS} components.`)
      }
    }

    return (
      <div className="space-y-6">
        {/* Search and Info */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex-1 w-full sm:w-auto">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search components..."
                  value={componentSearchQuery}
                  onChange={(e) => setComponentSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">Bookmarks:</span>
                <span className="font-semibold text-blue-600">{getComponentBookmarkCount()} / {MAX_COMPONENT_BOOKMARKS}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">⚡ Complex</span>
                <span className="text-gray-600 text-xs">= {highComplexityThreshold}+ score</span>
              </div>
            </div>
          </div>
        </div>

        {componentSearchQuery && (
          <div className="text-sm text-gray-600">
            Found {sortedComponents.length} of {Object.keys(components).length} components
          </div>
        )}

        {/* Components */}
        {sortedComponents.map(([componentName, component]) => (
          <div key={componentName} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 flex-wrap">
                    <h3 className="text-xl font-mono font-bold text-gray-900">{component.name}</h3>
                    <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">{component.type}</span>

                    {isHighComplexity(component) && (
                      <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">⚡ Complex</span>
                    )}

                    {isComponentBookmarked(componentName) && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">⭐ Bookmarked</span>
                    )}

                    {component.has_form && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">📝 Form</span>
                    )}
                  </div>

                  <p className="text-sm text-gray-600 mt-2">
                    📄 {component.file_path}:{component.line_number}
                  </p>

                  {component.description && (
                    <p className="text-sm text-gray-700 mt-1">{component.description}</p>
                  )}
                </div>

                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => handleComponentBookmarkClick(componentName)}
                    className={`p-2 rounded-lg transition-colors ${
                      isComponentBookmarked(componentName)
                        ? 'bg-yellow-200 text-yellow-700 hover:bg-yellow-300'
                        : canAddMoreComponentBookmarks()
                        ? 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                    disabled={!isComponentBookmarked(componentName) && !canAddMoreComponentBookmarks()}
                    title={isComponentBookmarked(componentName) ? 'Remove bookmark' : 'Bookmark component'}
                  >
                    <svg className="w-5 h-5" fill={isComponentBookmarked(componentName) ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                  </button>

                  <div className="flex space-x-3 text-center">
                    <div>
                      <div className="text-2xl font-bold text-purple-600">{component.lines_of_code}</div>
                      <div className="text-xs text-gray-600">LOC</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-orange-600">{component.complexity_score}</div>
                      <div className="text-xs text-gray-600">Complexity</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="p-6 space-y-4">
              {/* Used In (Pages) */}
              {component.used_in && component.used_in.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Used In ({component.used_in.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {component.used_in.map((usage, idx) => (
                      <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded border border-blue-200">
                        {usage.used_in_component}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Uses Components */}
              {component.uses_components && component.uses_components.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Uses Components ({component.uses_components.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {component.uses_components.map((compName, idx) => (
                      <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 text-sm rounded border border-purple-200">
                        {compName}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Event Handlers */}
              {component.handlers && component.handlers.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Event Handlers ({component.handlers.length})</h4>
                  <div className="bg-green-50 rounded p-3 space-y-2">
                    {component.handlers.map((handler, idx) => (
                      <div key={idx} className="flex items-center space-x-3 text-sm">
                        <span className="px-2 py-1 bg-green-200 text-green-800 rounded font-mono text-xs">{handler.event_type}</span>
                        <span className="font-mono text-gray-700">{handler.name}</span>
                        {handler.line_number && <span className="text-gray-500 text-xs">:{handler.line_number}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Data Fields */}
              {component.data_fields && component.data_fields.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Data Captured ({component.data_fields.length})</h4>
                  <div className="bg-blue-50 rounded p-3">
                    <div className="grid grid-cols-2 gap-2">
                      {component.data_fields.map((field, idx) => (
                        <div key={idx} className="flex items-center space-x-2 text-sm">
                          <span className="px-1.5 py-0.5 bg-blue-200 text-blue-800 rounded text-xs">{field.source}</span>
                          <span className="font-mono text-gray-700">{field.name}</span>
                          <span className="text-gray-500 text-xs">: {field.data_type}</span>
                          {field.required && <span className="text-red-600 text-xs">*</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Visual Structure */}
              {component.html_structure && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Visual Structure</h4>
                  <div className="bg-gray-50 rounded p-3">
                    <pre className="text-xs font-mono text-gray-700 overflow-x-auto whitespace-pre-wrap">{component.html_structure}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderPagesTab = () => {
    if (loadingPages) {
      return (
        <div className="flex justify-center py-12">
          <PinataSpinner size="lg" message="Loading pages..." />
        </div>
      )
    }

    if (!pages || Object.keys(pages).length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📄</div>
          <p className="text-gray-600">No pages detected in this scan</p>
        </div>
      )
    }

    // Filter by search
    const filteredPages = Object.entries(pages).filter(([name, page]) => {
      if (!pageSearchQuery) return true
      const searchLower = pageSearchQuery.toLowerCase()
      return (
        name.toLowerCase().includes(searchLower) ||
        page.path.toLowerCase().includes(searchLower) ||
        page.file_path.toLowerCase().includes(searchLower)
      )
    })

    // Sort alphabetically by path
    const sortedPages = [...filteredPages].sort(([, pageA], [, pageB]) => {
      return pageA.path.localeCompare(pageB.path)
    })

    return (
      <div className="space-y-6">
        {/* Search */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search pages by name or path..."
              value={pageSearchQuery}
              onChange={(e) => setPageSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {pageSearchQuery && (
          <div className="text-sm text-gray-600">
            Found {sortedPages.length} of {Object.keys(pages).length} pages
          </div>
        )}

        {/* Pages */}
        {sortedPages.map(([pageName, page]) => (
          <div key={pageName} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 flex-wrap">
                    <h3 className="text-xl font-bold text-gray-900">{page.name}</h3>
                    <span className="px-3 py-1 bg-blue-200 text-blue-800 text-sm rounded font-mono">{page.path}</span>

                    {page.requires_auth && (
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">🔒 Protected</span>
                    )}

                    {page.layout && (
                      <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">Layout: {page.layout}</span>
                    )}
                  </div>

                  <p className="text-sm text-gray-600 mt-2">
                    📄 {page.file_path}:{page.line_number}
                  </p>
                </div>

                <div className="flex space-x-3 text-center">
                  <div>
                    <div className="text-2xl font-bold text-purple-600">{page.component_count}</div>
                    <div className="text-xs text-gray-600">Components</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{page.api_calls_count}</div>
                    <div className="text-xs text-gray-600">API Calls</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{page.database_queries_count}</div>
                    <div className="text-xs text-gray-600">DB Queries</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="p-6 space-y-4">
              {/* Components Used */}
              {page.components && page.components.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Components Used ({page.components.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {page.components.map((compName, idx) => (
                      <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 text-sm rounded border border-purple-200">
                        {compName}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Route Parameters */}
              {page.route_params && page.route_params.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Route Parameters</h4>
                  <div className="flex flex-wrap gap-2">
                    {page.route_params.map((param, idx) => (
                      <span key={idx} className="px-3 py-1 bg-yellow-50 text-yellow-700 text-sm rounded border border-yellow-200 font-mono">
                        :{param}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics & Analytics */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Metrics & Analytics</h4>
                <div className="bg-gray-50 rounded p-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Total Components</div>
                    <div className="text-lg font-semibold text-purple-600">{page.component_count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">API Integrations</div>
                    <div className="text-lg font-semibold text-green-600">{page.api_calls_count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Database Operations</div>
                    <div className="text-lg font-semibold text-blue-600">{page.database_queries_count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Authentication</div>
                    <div className="text-lg font-semibold">{page.requires_auth ? '🔒 Required' : '🔓 Public'}</div>
                  </div>
                </div>
              </div>

              {/* Developer Notes */}
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-yellow-600">💡</span>
                  </div>
                  <div className="ml-3 text-sm text-yellow-700">
                    <strong>Debug Tips:</strong> This page makes {page.api_calls_count} API call(s) and {page.database_queries_count} database quer{page.database_queries_count === 1 ? 'y' : 'ies'}.
                    {page.component_count > 10 && ' Consider lazy loading some components to improve initial load time.'}
                    {page.requires_auth && ' Authentication is required - ensure auth state is properly managed.'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderDependenciesTab = () => {
    if (loadingDependencies) {
      return (
        <div className="flex justify-center py-12">
          <PinataSpinner size="lg" message="Loading dependencies..." />
        </div>
      )
    }

    if (!dependencies || Object.keys(dependencies).length === 0) {
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <p className="text-gray-600">No dependencies detected in this scan</p>
        </div>
      )
    }

    // Filter by search
    const filteredDeps = Object.entries(dependencies).filter(([key, dep]) => {
      if (!dependencySearchQuery) return true
      const searchLower = dependencySearchQuery.toLowerCase()
      return (
        dep.name.toLowerCase().includes(searchLower) ||
        (dep.package_manager && dep.package_manager.toLowerCase().includes(searchLower))
      )
    })

    // Sort: unused > outdated > security > alphabetical
    const sortedDeps = [...filteredDeps].sort(([, depA], [, depB]) => {
      // Prioritize issues
      if (!depA.is_used && depB.is_used) return -1
      if (depA.is_used && !depB.is_used) return 1

      if (depA.has_security_warning && !depB.has_security_warning) return -1
      if (!depA.has_security_warning && depB.has_security_warning) return 1

      if (depA.is_outdated && !depB.is_outdated) return -1
      if (!depA.is_outdated && depB.is_outdated) return 1

      return depA.name.localeCompare(depB.name)
    })

    const getHealthColor = (score: number) => {
      if (score >= 80) return 'text-green-600'
      if (score >= 60) return 'text-yellow-600'
      if (score >= 40) return 'text-orange-600'
      return 'text-red-600'
    }

    const getVersionColor = (dep: Dependency) => {
      if (dep.has_security_warning) return 'text-red-600'
      if (dep.major_update_available) return 'text-red-600'
      if (dep.minor_update_available) return 'text-yellow-600'
      if (dep.patch_update_available) return 'text-blue-600'
      return 'text-green-600'
    }

    return (
      <div className="space-y-6">
        {/* Metrics Dashboard */}
        {dependencyMetrics && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Dependency Health</h3>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Health Score:</span>
                <span className={`text-3xl font-bold ${getHealthColor(dependencyMetrics.health_score)}`}>
                  {dependencyMetrics.health_score.toFixed(0)}
                </span>
                <span className="text-sm text-gray-600">/100</span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-gray-900">{dependencyMetrics.total_dependencies}</div>
                <div className="text-xs text-gray-600">Total</div>
              </div>
              <div className="text-center p-3 bg-yellow-50 rounded">
                <div className="text-2xl font-bold text-yellow-600">{dependencyMetrics.outdated_count}</div>
                <div className="text-xs text-gray-600">Outdated</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-600">{dependencyMetrics.unused_count}</div>
                <div className="text-xs text-gray-600">Unused</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded">
                <div className="text-2xl font-bold text-red-600">{dependencyMetrics.security_warnings}</div>
                <div className="text-xs text-gray-600">Security</div>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded">
                <div className="text-2xl font-bold text-orange-600">{dependencyMetrics.conflict_count}</div>
                <div className="text-xs text-gray-600">Conflicts</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded">
                <div className="text-2xl font-bold text-purple-600">{dependencyMetrics.deprecated_count}</div>
                <div className="text-xs text-gray-600">Deprecated</div>
              </div>
            </div>

            {/* Update breakdown */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Available Updates:</span>
                <div className="flex space-x-4">
                  <span className="text-red-600">{dependencyMetrics.major_updates_available} major</span>
                  <span className="text-yellow-600">{dependencyMetrics.minor_updates_available} minor</span>
                  <span className="text-blue-600">{dependencyMetrics.patch_updates_available} patch</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conflicts Alert */}
        {dependencyConflicts && dependencyConflicts.length > 0 && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-red-600 text-xl">⚠️</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Dependency Conflicts Detected</h3>
                <div className="mt-2 space-y-2">
                  {dependencyConflicts.map((conflict, idx) => (
                    <div key={idx} className="text-sm text-red-700">
                      <strong>{conflict.package_name}</strong>: Multiple versions found ({conflict.versions.join(', ')})
                      <div className="text-xs text-red-600 mt-1">
                        Locations: {conflict.locations.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search dependencies..."
              value={dependencySearchQuery}
              onChange={(e) => setDependencySearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {dependencySearchQuery && (
          <div className="text-sm text-gray-600">
            Found {sortedDeps.length} of {Object.keys(dependencies).length} dependencies
          </div>
        )}

        {/* Dependencies List */}
        {sortedDeps.map(([key, dep]) => (
          <div key={key} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 flex-wrap">
                    <h3 className="text-xl font-mono font-bold text-gray-900">{dep.name}</h3>
                    <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded font-mono">{dep.package_manager}</span>

                    {!dep.is_used && !dep.is_dev_dependency && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">🔵 Unused</span>
                    )}

                    {dep.is_dev_dependency && (
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">🛠️ Dev</span>
                    )}

                    {dep.has_security_warning && (
                      <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-medium">🚨 Security</span>
                    )}

                    {dep.is_deprecated && (
                      <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">⚠️ Deprecated</span>
                    )}

                    {dep.has_conflict && (
                      <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-medium">❗ Conflict</span>
                    )}

                    {dep.is_outdated && !dep.has_security_warning && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">📅 Outdated</span>
                    )}
                  </div>

                  <p className="text-sm text-gray-600 mt-2">
                    📄 {dep.package_file}
                  </p>

                  {dep.description && (
                    <p className="text-sm text-gray-700 mt-1">{dep.description}</p>
                  )}
                </div>

                {/* Version Info */}
                <div className="flex space-x-6 text-center">
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Current</div>
                    <div className="text-lg font-semibold font-mono text-gray-900">{dep.current_version}</div>
                  </div>
                  {dep.latest_version && (
                    <>
                      <div className="flex items-center">
                        <span className="text-gray-400">→</span>
                      </div>
                      <div>
                        <div className="text-xs text-gray-600 mb-1">Latest</div>
                        <div className={`text-lg font-semibold font-mono ${getVersionColor(dep)}`}>
                          {dep.latest_version}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="p-6 space-y-4">
              {/* Usage Information */}
              {dep.is_used && dep.used_in_files.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Used In ({dep.usage_count} files)</h4>
                  <div className="bg-green-50 rounded p-3 max-h-32 overflow-y-auto">
                    <div className="space-y-1">
                      {dep.used_in_files.slice(0, 10).map((file, idx) => (
                        <div key={idx} className="text-sm text-gray-700 font-mono">{file}</div>
                      ))}
                      {dep.used_in_files.length > 10 && (
                        <div className="text-sm text-gray-500 italic">... and {dep.used_in_files.length - 10} more</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Version Analysis */}
              {dep.is_outdated && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Update Available</h4>
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
                    <div className="flex items-start space-x-2">
                      <span className="text-yellow-600">📈</span>
                      <div className="text-sm text-yellow-800">
                        <strong>
                          {dep.major_update_available && 'Major '}
                          {dep.minor_update_available && 'Minor '}
                          {dep.patch_update_available && 'Patch '}
                          update available
                        </strong>
                        {dep.versions_behind > 0 && (
                          <span> - {dep.versions_behind} version{dep.versions_behind > 1 ? 's' : ''} behind</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Conflict Details */}
              {dep.has_conflict && dep.conflict_details && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Conflict Details</h4>
                  <div className="bg-red-50 border-l-4 border-red-400 p-3">
                    <p className="text-sm text-red-800">{dep.conflict_details}</p>
                  </div>
                </div>
              )}

              {/* Additional Metadata */}
              {(dep.license || dep.last_published) && (
                <div className="flex items-center space-x-6 text-sm text-gray-600 border-t border-gray-200 pt-3">
                  {dep.license && (
                    <div>
                      <span className="font-medium">License:</span> {dep.license}
                    </div>
                  )}
                  {dep.last_published && (
                    <div>
                      <span className="font-medium">Last Published:</span> {dep.last_published}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
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

    // Calculate heavy usage threshold (tables with operations > 75th percentile)
    const allTables = Object.values(databaseTables)
    const operationCounts = allTables.map(t => t.read_count + t.write_count)
    const sortedCounts = [...operationCounts].sort((a, b) => b - a)
    const heavyUsageThreshold = sortedCounts[Math.floor(sortedCounts.length * 0.25)] || 5

    const isHeavyUsage = (table: DatabaseTable) => {
      return (table.read_count + table.write_count) >= heavyUsageThreshold
    }

    // Filter tables by search query
    const filteredTables = Object.entries(databaseTables).filter(([tableName, table]) => {
      if (!tableSearchQuery) return true
      return tableName.toLowerCase().includes(tableSearchQuery.toLowerCase())
    })

    // Sort tables: bookmarked first, then by usage (heavy to light), then alphabetically
    const sortedTables = [...filteredTables].sort(([nameA, tableA], [nameB, tableB]) => {
      const aBookmarked = isBookmarked(nameA)
      const bBookmarked = isBookmarked(nameB)

      // Bookmarked tables first
      if (aBookmarked && !bBookmarked) return -1
      if (!aBookmarked && bBookmarked) return 1

      // Then by total operations (descending)
      const aOps = tableA.read_count + tableA.write_count
      const bOps = tableB.read_count + tableB.write_count
      if (aOps !== bOps) return bOps - aOps

      // Finally alphabetically
      return nameA.localeCompare(nameB)
    })

    const handleBookmarkClick = (tableName: string) => {
      const success = toggleBookmark(tableName)
      if (!success && !isBookmarked(tableName)) {
        alert(`You can only bookmark up to ${MAX_BOOKMARKS} tables.`)
      }
    }

    return (
      <div className="space-y-6">
        {/* Search and Bookmark Info */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex-1 w-full sm:w-auto">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search tables..."
                  value={tableSearchQuery}
                  onChange={(e) => setTableSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <svg
                  className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">Bookmarks:</span>
                <span className="font-semibold text-blue-600">
                  {getBookmarkCount()} / {MAX_BOOKMARKS}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-medium">
                  🔥 Heavy
                </span>
                <span className="text-gray-600 text-xs">
                  = {heavyUsageThreshold}+ ops
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Results count */}
        {tableSearchQuery && (
          <div className="text-sm text-gray-600">
            Found {sortedTables.length} of {Object.keys(databaseTables).length} tables
          </div>
        )}

        {/* Tables */}
        {sortedTables.map(([tableName, table]) => (
          <div key={tableName} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Table Header */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-xl font-bold text-gray-900">{table.table_name}</h3>

                    {/* Heavy Usage Badge */}
                    {isHeavyUsage(table) && (
                      <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-medium">
                        🔥 Heavy
                      </span>
                    )}

                    {/* Bookmarked Badge */}
                    {isBookmarked(tableName) && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">
                        ⭐ Bookmarked
                      </span>
                    )}
                  </div>

                  {table.schema_file && (
                    <p className="text-sm text-gray-600 mt-1">
                      📄 {table.schema_file}:{table.schema_line}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-4">
                  {/* Bookmark Button */}
                  <button
                    onClick={() => handleBookmarkClick(tableName)}
                    className={`p-2 rounded-lg transition-colors ${
                      isBookmarked(tableName)
                        ? 'bg-yellow-200 text-yellow-700 hover:bg-yellow-300'
                        : canAddMoreBookmarks()
                        ? 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                    disabled={!isBookmarked(tableName) && !canAddMoreBookmarks()}
                    title={
                      isBookmarked(tableName)
                        ? 'Remove bookmark'
                        : canAddMoreBookmarks()
                        ? 'Bookmark table'
                        : 'Maximum bookmarks reached'
                    }
                  >
                    <svg
                      className="w-5 h-5"
                      fill={isBookmarked(tableName) ? 'currentColor' : 'none'}
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                      />
                    </svg>
                  </button>

                  {/* Operation Counts */}
                  <div className="flex space-x-3">
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
            { id: 'components', label: 'Components', icon: '🧩' },
            { id: 'pages', label: 'Pages', icon: '📄' },
            { id: 'tables', label: 'Database Tables', icon: '🗄️' },
            { id: 'api', label: 'API Endpoints', icon: '🌐' },
            { id: 'dependencies', label: 'Dependencies', icon: '📦' },
            { id: 'nodes', label: 'All Nodes', icon: '🔍' },
            { id: 'database', label: 'Database', icon: '💾' },
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
        {activeTab === 'components' && renderComponentsTab()}
        {activeTab === 'pages' && renderPagesTab()}
        {activeTab === 'tables' && renderTablesTab()}
        {activeTab === 'api' && renderApiTab()}
        {activeTab === 'dependencies' && renderDependenciesTab()}
        {activeTab === 'nodes' && renderNodesTab()}
        {activeTab === 'database' && renderDatabaseTab()}
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
