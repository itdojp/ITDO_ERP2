import React from 'react'

export interface WebSocketMessage<T = any> {
  type: string
  payload: T
  id?: string
  timestamp: number
  userId?: string
}

export interface WebSocketOptions {
  url: string
  protocols?: string | string[]
  reconnectAttempts?: number
  reconnectInterval?: number
  heartbeatInterval?: number
  enableHeartbeat?: boolean
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
  debug?: boolean
}

export interface UseWebSocketReturn {
  socket: WebSocket | null
  connectionState: WebSocketState
  send: <T = any>(type: string, payload: T, id?: string) => void
  sendRaw: (data: string | ArrayBuffer | Blob) => void
  connect: () => void
  disconnect: () => void
  subscribe: (type: string, handler: (payload: any) => void) => () => void
  unsubscribe: (type: string, handler?: (payload: any) => void) => void
  lastMessage: WebSocketMessage | null
  connectionInfo: ConnectionInfo
}

export enum WebSocketState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR',
  RECONNECTING = 'RECONNECTING'
}

export interface ConnectionInfo {
  attempts: number
  lastConnected?: Date
  lastDisconnected?: Date
  lastError?: string
  totalReconnects: number
  uptime: number
}

const DEFAULT_OPTIONS: Partial<WebSocketOptions> = {
  reconnectAttempts: 5,
  reconnectInterval: 3000,
  heartbeatInterval: 30000,
  enableHeartbeat: true,
  debug: false,
}

export const useWebSocket = (options: WebSocketOptions): UseWebSocketReturn => {
  const {
    url,
    protocols,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    enableHeartbeat = true,
    onOpen,
    onClose,
    onError,
    onMessage,
    debug = false,
  } = { ...DEFAULT_OPTIONS, ...options }

  const [socket, setSocket] = React.useState<WebSocket | null>(null)
  const [connectionState, setConnectionState] = React.useState<WebSocketState>(WebSocketState.DISCONNECTED)
  const [lastMessage, setLastMessage] = React.useState<WebSocketMessage | null>(null)
  const [connectionInfo, setConnectionInfo] = React.useState<ConnectionInfo>({
    attempts: 0,
    totalReconnects: 0,
    uptime: 0,
  })

  // Message handlers registry
  const messageHandlers = React.useRef<Map<string, Set<(payload: any) => void>>>(new Map())
  
  // Connection management refs
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout>()
  const heartbeatIntervalRef = React.useRef<NodeJS.Timeout>()
  const connectionStartTime = React.useRef<Date>()
  const shouldReconnect = React.useRef(true)

  const log = React.useCallback((...args: any[]) => {
    if (debug) {
      console.log('[WebSocket]', ...args)
    }
  }, [debug])

  const updateConnectionInfo = React.useCallback((updates: Partial<ConnectionInfo>) => {
    setConnectionInfo(prev => ({ ...prev, ...updates }))
  }, [])

  const startHeartbeat = React.useCallback(() => {
    if (!enableHeartbeat || !socket) return

    const sendHeartbeat = () => {
      if (socket?.readyState === WebSocket.OPEN) {
        const heartbeatMessage: WebSocketMessage = {
          type: 'heartbeat',
          payload: { timestamp: Date.now() },
          timestamp: Date.now(),
        }
        socket.send(JSON.stringify(heartbeatMessage))
        log('Heartbeat sent')
      }
    }

    heartbeatIntervalRef.current = setInterval(sendHeartbeat, heartbeatInterval)
    log('Heartbeat started')
  }, [socket, enableHeartbeat, heartbeatInterval, log])

  const stopHeartbeat = React.useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = undefined
      log('Heartbeat stopped')
    }
  }, [log])

  const handleMessage = React.useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      setLastMessage(message)
      
      log('Message received:', message)

      // Handle heartbeat response
      if (message.type === 'heartbeat' || message.type === 'pong') {
        log('Heartbeat response received')
        return
      }

      // Call global message handler
      onMessage?.(message)

      // Call type-specific handlers
      const handlers = messageHandlers.current.get(message.type)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message.payload)
          } catch (error) {
            console.error('Error in message handler:', error)
          }
        })
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }, [onMessage, log])

  const connect = React.useCallback(() => {
    if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) {
      log('Already connected or connecting')
      return
    }

    try {
      log('Connecting to:', url)
      setConnectionState(WebSocketState.CONNECTING)
      
      const newSocket = new WebSocket(url, protocols)
      connectionStartTime.current = new Date()

      newSocket.onopen = (event) => {
        log('Connected')
        setConnectionState(WebSocketState.CONNECTED)
        setSocket(newSocket)
        
        updateConnectionInfo({
          lastConnected: new Date(),
          attempts: 0,
        })

        startHeartbeat()
        onOpen?.(event)
      }

      newSocket.onclose = (event) => {
        log('Disconnected:', event.code, event.reason)
        setConnectionState(WebSocketState.DISCONNECTED)
        setSocket(null)
        
        updateConnectionInfo({
          lastDisconnected: new Date(),
        })

        stopHeartbeat()
        
        // Clear reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
        }

        // Attempt reconnection if not manually disconnected
        if (shouldReconnect.current && event.code !== 1000) {
          const currentAttempts = connectionInfo.attempts + 1
          
          if (currentAttempts <= reconnectAttempts) {
            log(`Reconnecting in ${reconnectInterval}ms (attempt ${currentAttempts}/${reconnectAttempts})`)
            setConnectionState(WebSocketState.RECONNECTING)
            
            updateConnectionInfo({
              attempts: currentAttempts,
              totalReconnects: connectionInfo.totalReconnects + 1,
            })

            reconnectTimeoutRef.current = setTimeout(() => {
              connect()
            }, reconnectInterval)
          } else {
            log('Max reconnection attempts reached')
            setConnectionState(WebSocketState.ERROR)
            updateConnectionInfo({
              lastError: 'Max reconnection attempts reached'
            })
          }
        }

        onClose?.(event)
      }

      newSocket.onerror = (event) => {
        log('Error:', event)
        setConnectionState(WebSocketState.ERROR)
        
        updateConnectionInfo({
          lastError: 'Connection error'
        })

        onError?.(event)
      }

      newSocket.onmessage = handleMessage

    } catch (error) {
      log('Connection error:', error)
      setConnectionState(WebSocketState.ERROR)
      updateConnectionInfo({
        lastError: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }, [
    url, 
    protocols, 
    socket, 
    reconnectAttempts, 
    reconnectInterval,
    connectionInfo.attempts,
    connectionInfo.totalReconnects,
    onOpen, 
    onClose, 
    onError,
    handleMessage,
    startHeartbeat,
    stopHeartbeat,
    updateConnectionInfo,
    log
  ])

  const disconnect = React.useCallback(() => {
    log('Manually disconnecting')
    shouldReconnect.current = false
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    stopHeartbeat()
    
    if (socket) {
      socket.close(1000, 'Manual disconnect')
    }
    
    setSocket(null)
    setConnectionState(WebSocketState.DISCONNECTED)
  }, [socket, stopHeartbeat, log])

  const send = React.useCallback(<T = any>(type: string, payload: T, id?: string) => {
    if (socket?.readyState !== WebSocket.OPEN) {
      log('Cannot send message: not connected')
      return
    }

    const message: WebSocketMessage<T> = {
      type,
      payload,
      id: id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
    }

    try {
      socket.send(JSON.stringify(message))
      log('Message sent:', message)
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }, [socket, log])

  const sendRaw = React.useCallback((data: string | ArrayBuffer | Blob) => {
    if (socket?.readyState !== WebSocket.OPEN) {
      log('Cannot send raw data: not connected')
      return
    }

    try {
      socket.send(data)
      log('Raw data sent')
    } catch (error) {
      console.error('Error sending raw data:', error)
    }
  }, [socket, log])

  const subscribe = React.useCallback((type: string, handler: (payload: any) => void) => {
    if (!messageHandlers.current.has(type)) {
      messageHandlers.current.set(type, new Set())
    }
    
    messageHandlers.current.get(type)!.add(handler)
    log('Subscribed to:', type)

    // Return unsubscribe function
    return () => {
      const handlers = messageHandlers.current.get(type)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          messageHandlers.current.delete(type)
        }
      }
      log('Unsubscribed from:', type)
    }
  }, [log])

  const unsubscribe = React.useCallback((type: string, handler?: (payload: any) => void) => {
    if (handler) {
      const handlers = messageHandlers.current.get(type)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          messageHandlers.current.delete(type)
        }
      }
    } else {
      messageHandlers.current.delete(type)
    }
    log('Unsubscribed from:', type)
  }, [log])

  // Calculate uptime
  React.useEffect(() => {
    const interval = setInterval(() => {
      if (connectionState === WebSocketState.CONNECTED && connectionStartTime.current) {
        const uptime = Date.now() - connectionStartTime.current.getTime()
        updateConnectionInfo({ uptime })
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [connectionState, updateConnectionInfo])

  // Auto-connect on mount
  React.useEffect(() => {
    shouldReconnect.current = true
    connect()
    
    // Cleanup on unmount
    return () => {
      shouldReconnect.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      stopHeartbeat()
      if (socket) {
        socket.close(1000, 'Component unmounting')
      }
    }
  }, []) // Only run on mount/unmount

  // Handle visibility change to reconnect when tab becomes active
  React.useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && connectionState === WebSocketState.DISCONNECTED) {
        log('Tab became visible, attempting to reconnect')
        shouldReconnect.current = true
        connect()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [connectionState, connect, log])

  return {
    socket,
    connectionState,
    send,
    sendRaw,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    lastMessage,
    connectionInfo,
  }
}

export default useWebSocket