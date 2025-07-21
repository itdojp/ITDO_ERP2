import React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket, WebSocketMessage } from './useWebSocket'
import { queryKeys } from '../lib/queryClient'

export interface RealTimeSyncOptions {
  wsUrl?: string
  enabled?: boolean
  userId?: string
  subscriptions?: string[]
  onEntityUpdate?: (entity: any) => void
  onEntityCreate?: (entity: any) => void
  onEntityDelete?: (entityId: string, entityType: string) => void
  onUserActivity?: (activity: UserActivity) => void
  onNotification?: (notification: any) => void
}

export interface UserActivity {
  userId: string
  type: 'online' | 'offline' | 'typing' | 'viewing' | 'editing'
  entityType?: string
  entityId?: string
  timestamp: number
  metadata?: Record<string, any>
}

export interface RealTimeEvent {
  type: string
  entityType: string
  entityId: string
  action: 'create' | 'update' | 'delete'
  data: any
  userId: string
  timestamp: number
}

export interface CollaborationState {
  activeUsers: Map<string, UserActivity>
  userPresence: Map<string, 'online' | 'offline' | 'away'>
  entityViewers: Map<string, Set<string>>
  entityEditors: Map<string, Set<string>>
}

export const useRealTimeSync = (options: RealTimeSyncOptions = {}) => {
  const {
    wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8080/ws',
    enabled = true,
    userId,
    subscriptions = [],
    onEntityUpdate,
    onEntityCreate,
    onEntityDelete,
    onUserActivity,
    onNotification,
  } = options

  const queryClient = useQueryClient()
  const [collaborationState, setCollaborationState] = React.useState<CollaborationState>({
    activeUsers: new Map(),
    userPresence: new Map(),
    entityViewers: new Map(),
    entityEditors: new Map(),
  })

  const {
    socket,
    connectionState,
    send,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  } = useWebSocket({
    url: wsUrl,
    enabled,
    debug: process.env.NODE_ENV === 'development',
    onOpen: () => {
      console.log('Real-time sync connected')
      // Send authentication and subscription info
      if (userId) {
        send('auth', { userId, subscriptions })
      }
    },
    onClose: () => {
      console.log('Real-time sync disconnected')
      // Clear collaboration state
      setCollaborationState({
        activeUsers: new Map(),
        userPresence: new Map(),
        entityViewers: new Map(),
        entityEditors: new Map(),
      })
    },
  })

  // Handle real-time entity updates
  const handleEntityUpdate = React.useCallback((payload: RealTimeEvent) => {
    const { entityType, entityId, action, data } = payload

    // Update React Query cache based on entity type and action
    switch (action) {
      case 'create':
        // Invalidate list queries to refetch and include new entity
        queryClient.invalidateQueries({ queryKey: [entityType] })
        onEntityCreate?.(data)
        break

      case 'update':
        // Update specific entity in cache
        const entityQueryKey = [entityType, entityId]
        queryClient.setQueryData(entityQueryKey, data)
        
        // Update entity in list queries
        queryClient.setQueriesData(
          { queryKey: [entityType] },
          (oldData: any) => {
            if (!oldData) return oldData
            
            if (Array.isArray(oldData.data)) {
              return {
                ...oldData,
                data: oldData.data.map((item: any) => 
                  item.id === entityId ? { ...item, ...data } : item
                )
              }
            }
            
            return oldData
          }
        )
        
        onEntityUpdate?.(data)
        break

      case 'delete':
        // Remove from cache
        queryClient.removeQueries({ queryKey: [entityType, entityId] })
        
        // Remove from list queries
        queryClient.setQueriesData(
          { queryKey: [entityType] },
          (oldData: any) => {
            if (!oldData) return oldData
            
            if (Array.isArray(oldData.data)) {
              return {
                ...oldData,
                data: oldData.data.filter((item: any) => item.id !== entityId)
              }
            }
            
            return oldData
          }
        )
        
        onEntityDelete?.(entityId, entityType)
        break
    }
  }, [queryClient, onEntityCreate, onEntityUpdate, onEntityDelete])

  // Handle user activity updates
  const handleUserActivity = React.useCallback((activity: UserActivity) => {
    setCollaborationState(prev => {
      const newState = { ...prev }
      
      // Update active users
      newState.activeUsers = new Map(prev.activeUsers)
      newState.activeUsers.set(activity.userId, activity)
      
      // Update user presence
      newState.userPresence = new Map(prev.userPresence)
      if (activity.type === 'online' || activity.type === 'offline') {
        newState.userPresence.set(activity.userId, activity.type)
      }
      
      // Update entity viewers/editors
      if (activity.entityId && activity.entityType) {
        const entityKey = `${activity.entityType}:${activity.entityId}`
        
        if (activity.type === 'viewing') {
          newState.entityViewers = new Map(prev.entityViewers)
          if (!newState.entityViewers.has(entityKey)) {
            newState.entityViewers.set(entityKey, new Set())
          }
          newState.entityViewers.get(entityKey)!.add(activity.userId)
        }
        
        if (activity.type === 'editing') {
          newState.entityEditors = new Map(prev.entityEditors)
          if (!newState.entityEditors.has(entityKey)) {
            newState.entityEditors.set(entityKey, new Set())
          }
          newState.entityEditors.get(entityKey)!.add(activity.userId)
        }
      }
      
      return newState
    })
    
    onUserActivity?.(activity)
  }, [onUserActivity])

  // Handle notifications
  const handleNotification = React.useCallback((notification: any) => {
    // Invalidate notifications query to refetch
    queryClient.invalidateQueries({ queryKey: queryKeys.notifications() })
    onNotification?.(notification)
  }, [queryClient, onNotification])

  // Subscribe to real-time events
  React.useEffect(() => {
    if (!enabled) return

    const unsubscribeFunctions = [
      subscribe('entity_update', handleEntityUpdate),
      subscribe('user_activity', handleUserActivity),
      subscribe('notification', handleNotification),
    ]

    return () => {
      unsubscribeFunctions.forEach(unsub => unsub())
    }
  }, [enabled, subscribe, handleEntityUpdate, handleUserActivity, handleNotification])

  // Broadcast user activity
  const broadcastActivity = React.useCallback((
    type: UserActivity['type'],
    entityType?: string,
    entityId?: string,
    metadata?: Record<string, any>
  ) => {
    if (!userId || connectionState !== 'CONNECTED') return

    const activity: UserActivity = {
      userId,
      type,
      entityType,
      entityId,
      timestamp: Date.now(),
      metadata,
    }

    send('user_activity', activity)
  }, [userId, connectionState, send])

  // Optimistic updates for better UX
  const optimisticUpdate = React.useCallback((
    entityType: string,
    entityId: string,
    updates: Partial<any>
  ) => {
    const entityQueryKey = [entityType, entityId]
    
    queryClient.setQueryData(entityQueryKey, (oldData: any) => {
      if (!oldData) return oldData
      return { ...oldData, ...updates }
    })

    // Also update in list queries
    queryClient.setQueriesData(
      { queryKey: [entityType] },
      (oldData: any) => {
        if (!oldData || !Array.isArray(oldData.data)) return oldData
        
        return {
          ...oldData,
          data: oldData.data.map((item: any) => 
            item.id === entityId ? { ...item, ...updates } : item
          )
        }
      }
    )
  }, [queryClient])

  // Get viewers/editors for a specific entity
  const getEntityCollaborators = React.useCallback((entityType: string, entityId: string) => {
    const entityKey = `${entityType}:${entityId}`
    return {
      viewers: Array.from(collaborationState.entityViewers.get(entityKey) || []),
      editors: Array.from(collaborationState.entityEditors.get(entityKey) || []),
    }
  }, [collaborationState])

  // Get online users
  const getOnlineUsers = React.useCallback(() => {
    return Array.from(collaborationState.userPresence.entries())
      .filter(([_, status]) => status === 'online')
      .map(([userId]) => userId)
  }, [collaborationState])

  // Join entity collaboration
  const joinEntity = React.useCallback((entityType: string, entityId: string, mode: 'viewing' | 'editing' = 'viewing') => {
    broadcastActivity(mode, entityType, entityId)
  }, [broadcastActivity])

  // Leave entity collaboration
  const leaveEntity = React.useCallback((entityType: string, entityId: string) => {
    if (!userId) return

    setCollaborationState(prev => {
      const entityKey = `${entityType}:${entityId}`
      const newState = { ...prev }
      
      // Remove from viewers
      if (newState.entityViewers.has(entityKey)) {
        newState.entityViewers = new Map(prev.entityViewers)
        newState.entityViewers.get(entityKey)!.delete(userId)
        if (newState.entityViewers.get(entityKey)!.size === 0) {
          newState.entityViewers.delete(entityKey)
        }
      }
      
      // Remove from editors
      if (newState.entityEditors.has(entityKey)) {
        newState.entityEditors = new Map(prev.entityEditors)
        newState.entityEditors.get(entityKey)!.delete(userId)
        if (newState.entityEditors.get(entityKey)!.size === 0) {
          newState.entityEditors.delete(entityKey)
        }
      }
      
      return newState
    })

    // Notify server
    send('leave_entity', { entityType, entityId, userId })
  }, [userId, send])

  // Conflict resolution for concurrent edits
  const resolveConflict = React.useCallback((
    entityType: string,
    entityId: string,
    localVersion: any,
    remoteVersion: any,
    mergeStrategy: 'local' | 'remote' | 'merge' | 'manual' = 'remote'
  ) => {
    switch (mergeStrategy) {
      case 'local':
        // Keep local changes, ignore remote
        return localVersion
        
      case 'remote':
        // Accept remote changes, discard local
        optimisticUpdate(entityType, entityId, remoteVersion)
        return remoteVersion
        
      case 'merge':
        // Simple merge strategy - remote wins for conflicts
        const merged = { ...localVersion, ...remoteVersion }
        optimisticUpdate(entityType, entityId, merged)
        return merged
        
      case 'manual':
        // Return both versions for manual resolution
        return { local: localVersion, remote: remoteVersion, requiresManualResolution: true }
        
      default:
        return remoteVersion
    }
  }, [optimisticUpdate])

  return {
    connectionState,
    collaborationState,
    broadcastActivity,
    optimisticUpdate,
    getEntityCollaborators,
    getOnlineUsers,
    joinEntity,
    leaveEntity,
    resolveConflict,
    connect,
    disconnect,
    send,
  }
}

export default useRealTimeSync