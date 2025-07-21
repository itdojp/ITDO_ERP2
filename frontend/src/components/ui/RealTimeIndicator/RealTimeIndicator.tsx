import React from 'react'
import { Wifi, WifiOff, Users, Eye, Edit, AlertCircle } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { useRealTimeSync } from '../../../hooks/useRealTimeSync'
import { WebSocketState } from '../../../hooks/useWebSocket'

export interface RealTimeIndicatorProps {
  className?: string
  showUserCount?: boolean
  showCollaborators?: boolean
  entityType?: string
  entityId?: string
  userId?: string
}

const RealTimeIndicator = React.memo<RealTimeIndicatorProps>(({
  className,
  showUserCount = true,
  showCollaborators = false,
  entityType,
  entityId,
  userId,
}) => {
  const {
    connectionState,
    collaborationState,
    getEntityCollaborators,
    getOnlineUsers,
    joinEntity,
    leaveEntity,
  } = useRealTimeSync({ userId })

  const onlineUsers = getOnlineUsers()
  const entityCollaborators = entityType && entityId 
    ? getEntityCollaborators(entityType, entityId)
    : { viewers: [], editors: [] }

  // Join entity on mount if specified
  React.useEffect(() => {
    if (entityType && entityId && showCollaborators) {
      joinEntity(entityType, entityId, 'viewing')
      
      return () => {
        leaveEntity(entityType, entityId)
      }
    }
  }, [entityType, entityId, showCollaborators, joinEntity, leaveEntity])

  const getConnectionIcon = () => {
    switch (connectionState) {
      case WebSocketState.CONNECTED:
        return <Wifi className="h-4 w-4 text-green-500" />
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return <Wifi className="h-4 w-4 text-yellow-500 animate-pulse" />
      case WebSocketState.DISCONNECTED:
      case WebSocketState.ERROR:
        return <WifiOff className="h-4 w-4 text-red-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const getConnectionText = () => {
    switch (connectionState) {
      case WebSocketState.CONNECTED:
        return 'Connected'
      case WebSocketState.CONNECTING:
        return 'Connecting...'
      case WebSocketState.RECONNECTING:
        return 'Reconnecting...'
      case WebSocketState.DISCONNECTED:
        return 'Disconnected'
      case WebSocketState.ERROR:
        return 'Connection Error'
      default:
        return 'Unknown'
    }
  }

  const getConnectionColor = () => {
    switch (connectionState) {
      case WebSocketState.CONNECTED:
        return 'text-green-600 bg-green-50 border-green-200'
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case WebSocketState.DISCONNECTED:
      case WebSocketState.ERROR:
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className={cn('flex items-center space-x-3', className)}>
      {/* Connection Status */}
      <div className={cn(
        'flex items-center space-x-2 px-3 py-1 rounded-full border text-xs font-medium',
        getConnectionColor()
      )}>
        {getConnectionIcon()}
        <span>{getConnectionText()}</span>
      </div>

      {/* Online Users Count */}
      {showUserCount && connectionState === WebSocketState.CONNECTED && (
        <div className="flex items-center space-x-1 text-xs text-gray-600">
          <Users className="h-4 w-4" />
          <span>{onlineUsers.length} online</span>
        </div>
      )}

      {/* Entity Collaborators */}
      {showCollaborators && entityType && entityId && connectionState === WebSocketState.CONNECTED && (
        <div className="flex items-center space-x-3">
          {/* Viewers */}
          {entityCollaborators.viewers.length > 0 && (
            <div className="flex items-center space-x-1 text-xs text-gray-600">
              <Eye className="h-4 w-4" />
              <span>{entityCollaborators.viewers.length}</span>
            </div>
          )}

          {/* Editors */}
          {entityCollaborators.editors.length > 0 && (
            <div className="flex items-center space-x-1 text-xs text-orange-600">
              <Edit className="h-4 w-4" />
              <span>{entityCollaborators.editors.length}</span>
            </div>
          )}

          {/* Active Users Avatars */}
          {(entityCollaborators.viewers.length > 0 || entityCollaborators.editors.length > 0) && (
            <div className="flex -space-x-1">
              {[...new Set([...entityCollaborators.viewers, ...entityCollaborators.editors])]
                .slice(0, 3)
                .map((userId, index) => (
                  <div
                    key={userId}
                    className={cn(
                      'w-6 h-6 rounded-full border-2 border-white bg-blue-500 flex items-center justify-center text-xs text-white font-medium',
                      entityCollaborators.editors.includes(userId) && 'ring-2 ring-orange-400'
                    )}
                    title={`User ${userId}${entityCollaborators.editors.includes(userId) ? ' (editing)' : ' (viewing)'}`}
                  >
                    {userId.charAt(0).toUpperCase()}
                  </div>
                ))}
              
              {/* Show more indicator */}
              {entityCollaborators.viewers.length + entityCollaborators.editors.length > 3 && (
                <div className="w-6 h-6 rounded-full border-2 border-white bg-gray-400 flex items-center justify-center text-xs text-white font-medium">
                  +{entityCollaborators.viewers.length + entityCollaborators.editors.length - 3}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
})

RealTimeIndicator.displayName = 'RealTimeIndicator'

export default RealTimeIndicator