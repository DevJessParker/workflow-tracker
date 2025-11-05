/**
 * WebSocket Hook for Scan Progress Updates
 *
 * Manages WebSocket connection with automatic reconnection,
 * error handling, and state management.
 *
 * Features:
 * - Auto-reconnect on disconnect (survives hot reload!)
 * - Connection status tracking
 * - Heartbeat/ping to keep connection alive
 * - Clear error messages
 * - Automatic cleanup
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface ScanUpdate {
  type: 'connected' | 'scan_update' | 'pong' | 'error'
  scan_id: string
  status?: string
  progress?: number
  message?: string
  files_scanned?: number
  total_files?: number
  nodes_found?: number
  eta?: string
  timestamp: string
}

export interface UseScanWebSocketOptions {
  /** WebSocket server URL (e.g., 'ws://localhost:8000') */
  url: string
  /** Scan ID to monitor */
  scanId: string
  /** Enable the WebSocket connection (default: true) */
  enabled?: boolean
  /** Callback when update received */
  onUpdate: (update: ScanUpdate) => void
  /** Callback when connection status changes */
  onConnectionChange?: (status: ConnectionStatus) => void
  /** Enable automatic reconnection (default: true) */
  autoReconnect?: boolean
  /** Max reconnection attempts (default: 10) */
  maxReconnectAttempts?: number
  /** Reconnection delay in ms (default: 2000) */
  reconnectDelay?: number
  /** Enable heartbeat ping (default: true) */
  enableHeartbeat?: boolean
  /** Heartbeat interval in ms (default: 30000) */
  heartbeatInterval?: number
}

export function useScanWebSocket({
  url,
  scanId,
  enabled = true,
  onUpdate,
  onConnectionChange,
  autoReconnect = true,
  maxReconnectAttempts = 10,
  reconnectDelay = 2000,
  enableHeartbeat = true,
  heartbeatInterval = 30000,
}: UseScanWebSocketOptions) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const [lastUpdate, setLastUpdate] = useState<ScanUpdate | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const isIntentionalClose = useRef(false)

  const updateConnectionStatus = useCallback((status: ConnectionStatus) => {
    console.log(`[WebSocket] Connection status: ${status}`)
    setConnectionStatus(status)
    onConnectionChange?.(status)
  }, [onConnectionChange])

  const startHeartbeat = useCallback(() => {
    if (!enableHeartbeat) return

    // Clear existing heartbeat
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current)
    }

    // Send ping every heartbeatInterval
    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('[WebSocket] 🏓 Sending heartbeat ping')
        wsRef.current.send('ping')
      }
    }, heartbeatInterval)
  }, [enableHeartbeat, heartbeatInterval])

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current)
      heartbeatTimerRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Already connected or connecting, skipping...')
      return
    }

    const wsUrl = `${url}/ws/scan/${scanId}`
    console.log(`[WebSocket] 🔌 Connecting to: ${wsUrl}`)

    updateConnectionStatus('connecting')
    setError(null)

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WebSocket] ✅ Connected successfully')
        updateConnectionStatus('connected')
        reconnectAttemptsRef.current = 0
        setError(null)
        startHeartbeat()
      }

      ws.onmessage = (event) => {
        try {
          const update: ScanUpdate = JSON.parse(event.data)

          if (update.type === 'connected') {
            console.log(`[WebSocket] 📡 Connection confirmed for scan: ${update.scan_id}`)
          } else if (update.type === 'scan_update') {
            console.log(`[WebSocket] 📊 Update: ${update.status} - ${update.progress?.toFixed(1)}%`)
            setLastUpdate(update)
            onUpdate(update)
          } else if (update.type === 'pong') {
            console.log('[WebSocket] 🏓 Pong received')
          } else if (update.type === 'error') {
            console.error(`[WebSocket] ❌ Server error: ${update.message}`)
            setError(update.message || 'Unknown server error')
          }
        } catch (err) {
          console.error('[WebSocket] ❌ Failed to parse message:', err)
          console.error('[WebSocket] Raw message:', event.data)
        }
      }

      ws.onerror = (event) => {
        console.error('[WebSocket] ❌ WebSocket error:', event)
        updateConnectionStatus('error')
        setError('WebSocket connection error')
      }

      ws.onclose = (event) => {
        console.log(`[WebSocket] 🔌 Disconnected: ${event.code} - ${event.reason || 'No reason'}`)
        stopHeartbeat()

        if (isIntentionalClose.current) {
          console.log('[WebSocket] Intentional close, not reconnecting')
          updateConnectionStatus('disconnected')
          return
        }

        updateConnectionStatus('disconnected')

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          const delay = reconnectDelay * reconnectAttemptsRef.current // Exponential backoff

          console.log(
            `[WebSocket] 🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          )

          reconnectTimerRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('[WebSocket] ❌ Max reconnection attempts reached')
          setError('Failed to reconnect after multiple attempts')
          updateConnectionStatus('error')
        }
      }
    } catch (err) {
      console.error('[WebSocket] ❌ Failed to create WebSocket:', err)
      updateConnectionStatus('error')
      setError(err instanceof Error ? err.message : 'Failed to create WebSocket')
    }
  }, [url, scanId, autoReconnect, maxReconnectAttempts, reconnectDelay, onUpdate, updateConnectionStatus, startHeartbeat, stopHeartbeat])

  const disconnect = useCallback(() => {
    console.log('[WebSocket] 🔌 Disconnecting...')
    isIntentionalClose.current = true

    // Clear timers
    stopHeartbeat()
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect')
      wsRef.current = null
    }

    updateConnectionStatus('disconnected')
  }, [stopHeartbeat, updateConnectionStatus])

  // Auto-connect when enabled and scanId exists
  useEffect(() => {
    if (!enabled || !scanId) {
      console.log('[WebSocket] Not connecting: enabled=' + enabled + ', scanId=' + scanId)
      return
    }

    isIntentionalClose.current = false
    connect()

    // Cleanup on unmount or when disabled
    return () => {
      disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, scanId])  // Remove connect/disconnect from deps to prevent reconnect loop

  return {
    connectionStatus,
    lastUpdate,
    error,
    reconnect: connect,
    disconnect,
  }
}
