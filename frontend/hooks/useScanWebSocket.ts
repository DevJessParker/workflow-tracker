/**
 * WebSocket Hook for Real-time Scan Progress
 * Connects to backend WebSocket endpoint and streams progress updates
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export interface ScanProgress {
  scan_id: string
  status: 'queued' | 'discovering' | 'scanning' | 'completed' | 'error' | 'failed'
  progress: number
  message: string
  files_scanned: number
  nodes_found: number
  eta: string | null
  total_files: number | null
}

export interface UseScanWebSocketOptions {
  scanId: string | null
  enabled?: boolean
  onProgress?: (progress: ScanProgress) => void
  onComplete?: (progress: ScanProgress) => void
  onError?: (error: string) => void
}

export interface UseScanWebSocketReturn {
  progress: ScanProgress | null
  isConnected: boolean
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  error: string | null
  connect: () => void
  disconnect: () => void
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
const MAX_RECONNECT_ATTEMPTS = 10
const INITIAL_RECONNECT_DELAY = 2000 // 2 seconds

export function useScanWebSocket(options: UseScanWebSocketOptions): UseScanWebSocketReturn {
  const { scanId, enabled = true, onProgress, onComplete, onError } = options

  const [progress, setProgress] = useState<ScanProgress | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnectRef = useRef(true)

  const updateConnectionStatus = useCallback((status: typeof connectionStatus) => {
    console.log('[WebSocket] Connection status:', status)
    setConnectionStatus(status)
    setIsConnected(status === 'connected')
  }, [])

  const handleMessage = useCallback((data: string) => {
    try {
      const progressData: ScanProgress = JSON.parse(data)
      console.log('[WebSocket] 📥 Progress update:', progressData)

      setProgress(progressData)
      onProgress?.(progressData)

      if (progressData.status === 'completed') {
        console.log('[WebSocket] ✅ Scan completed')
        onComplete?.(progressData)
        shouldReconnectRef.current = false
      } else if (progressData.status === 'error' || progressData.status === 'failed') {
        console.log('[WebSocket] ❌ Scan failed:', progressData.message)
        onError?.(progressData.message)
        shouldReconnectRef.current = false
      }
    } catch (err) {
      console.error('[WebSocket] Failed to parse message:', err)
    }
  }, [onProgress, onComplete, onError])

  const connect = useCallback(() => {
    if (!scanId) {
      console.log('[WebSocket] No scan ID, skipping connection')
      return
    }

    if (!enabled) {
      console.log('[WebSocket] Not connecting: enabled=false, scanId=', scanId)
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Already connected or connecting, skipping...')
      return
    }

    const wsUrl = `${WS_URL}/api/v1/scanner/ws/scan/${scanId}`
    console.log('[WebSocket] 🔌 Connecting to:', wsUrl)

    updateConnectionStatus('connecting')

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WebSocket] ✅ Connected successfully')
        updateConnectionStatus('connected')
        reconnectAttemptsRef.current = 0
        setError(null)
      }

      ws.onmessage = (event) => {
        handleMessage(event.data)
      }

      ws.onerror = (event) => {
        console.error('[WebSocket] ❌ WebSocket error:', event)
        updateConnectionStatus('error')
        setError('WebSocket connection error')
      }

      ws.onclose = (event) => {
        console.log('[WebSocket] 🔌 Disconnected:', event.code, '-', event.reason || 'No reason')
        updateConnectionStatus('disconnected')

        // Attempt to reconnect if appropriate
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++
          const delay = INITIAL_RECONNECT_DELAY * reconnectAttemptsRef.current
          console.log(
            `[WebSocket] 🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`
          )

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          console.error('[WebSocket] ❌ Max reconnection attempts reached')
          setError('Failed to connect after multiple attempts')
          onError?.('Failed to connect after multiple attempts')
        }
      }
    } catch (err) {
      console.error('[WebSocket] Failed to create WebSocket:', err)
      updateConnectionStatus('error')
      setError('Failed to create WebSocket connection')
    }
  }, [scanId, enabled, WS_URL, handleMessage, updateConnectionStatus, onError])

  const disconnect = useCallback(() => {
    console.log('[WebSocket] 🔌 Disconnecting...')
    shouldReconnectRef.current = false

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    updateConnectionStatus('disconnected')
  }, [updateConnectionStatus])

  // Connect when scanId changes or enabled changes
  useEffect(() => {
    if (scanId && enabled) {
      shouldReconnectRef.current = true
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [scanId, enabled, connect, disconnect])

  return {
    progress,
    isConnected,
    connectionStatus,
    error,
    connect,
    disconnect,
  }
}
