# WebSocket Integration Guide

## Overview
This guide shows how to integrate the WebSocket hook into the scanner page to replace HTTP polling.

## Step 1: Import the WebSocket Hook

Add to the top of `app/dashboard/scanner/page.tsx`:

```typescript
import { useScanWebSocket, ConnectionStatus } from '../../hooks/useScanWebSocket'
```

## Step 2: Add Connection Status State

Add this state variable with your other state declarations:

```typescript
const [wsConnectionStatus, setWsConnectionStatus] = useState<ConnectionStatus>('disconnected')
```

## Step 3: Replace `startScan` Function

Replace the entire `startScan` function with this simplified version:

```typescript
const startScan = async () => {
  try {
    setScanning(true)
    setScanResults(null)
    setDiagram(null)
    setScanStatus({
      scan_id: 'pending',
      status: 'starting',
      progress: 0,
      message: 'Starting scan...',
      files_scanned: 0,
      nodes_found: 0
    })

    console.log('🚀 Starting scan with config:', config)

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

    // Start the scan
    const response = await fetch(`${API_URL}/api/v1/scanner/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })

    const data = await response.json()
    console.log('✅ Scan started:', data.scan_id)

    // Store scan_id and let WebSocket hook handle updates
    setScanId(data.scan_id)

  } catch (error) {
    console.error('Failed to start scan:', error)
    alert(`Failed to start scan: ${error instanceof Error ? error.message : 'Unknown error'}`)
    setScanning(false)
    setScanStatus(null)
  }
}
```

## Step 4: Add WebSocket Hook Usage

Add this after the `startScan` function definition:

```typescript
// WebSocket connection for real-time updates
const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://')

useScanWebSocket({
  url: wsUrl,
  scanId: scanId || '',
  enabled: !!scanId && scanning,  // Only connect when scanning
  onUpdate: (update) => {
    console.log('📊 WebSocket update:', update)

    // Update scan status
    setScanStatus({
      scan_id: update.scan_id,
      status: update.status || 'unknown',
      progress: update.progress || 0,
      message: update.message || '',
      files_scanned: update.files_scanned || 0,
      nodes_found: update.nodes_found || 0,
      eta: update.eta,
      total_files: update.total_files,
    })

    // Handle completion
    if (update.status === 'completed') {
      setScanning(false)
      loadScanResults(update.scan_id)
    } else if (update.status === 'failed') {
      setScanning(false)
      alert(`Scan failed: ${update.message}`)
    }
  },
  onConnectionChange: (status) => {
    console.log('🔌 WebSocket connection status:', status)
    setWsConnectionStatus(status)
  },
})
```

## Step 5: Remove Old Polling Code

**DELETE** these functions entirely:
- `pollForActiveScan()`
- `pollScanStatus()`
- The entire `useEffect` hook that resumes scans from localStorage

## Step 6: Add Connection Status Indicator

Add this component before the progress bar section (around line 544):

```tsx
{/* WebSocket Connection Status */}
{scanning && (
  <div className="mb-4 flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${
        wsConnectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
        wsConnectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
        wsConnectionStatus === 'error' ? 'bg-red-500' :
        'bg-gray-400'
      }`} />
      <span className="text-sm text-gray-600">
        {wsConnectionStatus === 'connected' && '🔗 Live updates active'}
        {wsConnectionStatus === 'connecting' && '⏳ Connecting to live updates...'}
        {wsConnectionStatus === 'error' && '❌ Connection error'}
        {wsConnectionStatus === 'disconnected' && '🔌 Disconnected'}
      </span>
    </div>
    <span className="text-xs text-gray-400">WebSocket</span>
  </div>
)}
```

## Complete Example

Here's a minimal working example:

```typescript
'use client'

import { useState } from 'react'
import { useScanWebSocket } from '../../hooks/useScanWebSocket'

export default function ScannerPage() {
  const [scanning, setScanning] = useState(false)
  const [scanId, setScanId] = useState<string | null>(null)
  const [scanStatus, setScanStatus] = useState<any>(null)
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')

  const API_URL = 'http://localhost:8000'
  const WS_URL = 'ws://localhost:8000'

  const startScan = async () => {
    const response = await fetch(`${API_URL}/api/v1/scanner/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ /* config */ }),
    })
    const data = await response.json()
    setScanId(data.scan_id)
    setScanning(true)
  }

  // WebSocket hook handles all real-time updates
  useScanWebSocket({
    url: WS_URL,
    scanId: scanId || '',
    enabled: !!scanId && scanning,
    onUpdate: (update) => {
      setScanStatus(update)
      if (update.status === 'completed') {
        setScanning(false)
      }
    },
    onConnectionChange: setWsStatus,
  })

  return (
    <div>
      <button onClick={startScan}>Start Scan</button>

      {/* Connection Status */}
      <div>Status: {wsStatus}</div>

      {/* Progress Bar */}
      {scanStatus && (
        <div>
          <div>Progress: {scanStatus.progress}%</div>
          <div>Files: {scanStatus.files_scanned}/{scanStatus.total_files}</div>
          <div>Status: {scanStatus.status}</div>
        </div>
      )}
    </div>
  )
}
```

## Benefits

✅ **No more polling** - 1 connection instead of 3,600 requests/hour
✅ **Real-time updates** - Instant, no 1-second delay
✅ **Survives hot reload** - Auto-reconnects automatically
✅ **Production-ready** - Scales horizontally with Redis
✅ **Better UX** - Connection status indicator
✅ **Cleaner code** - 50 lines vs 200 lines of polling logic

## Testing

1. Start Docker: `docker-compose up`
2. Navigate to scanner page
3. Start a scan
4. Watch console logs for WebSocket messages
5. Trigger hot reload (save any file) - connection should auto-reconnect
6. Progress bar should continue updating seamlessly
