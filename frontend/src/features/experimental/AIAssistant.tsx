import React from 'react'
import { 
  Bot, 
  Send, 
  Minimize2, 
  Maximize2, 
  X,
  MessageCircle,
  Lightbulb,
  Search,
  HelpCircle,
  Zap
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useExperimentalFeature, useFeatureAnalytics } from './FeatureFlags'

export interface AIMessage {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: {
    confidence?: number
    sources?: string[]
    suggestions?: string[]
    actions?: AIAction[]
  }
}

export interface AIAction {
  id: string
  label: string
  type: 'navigation' | 'search' | 'create' | 'update' | 'delete'
  target?: string
  data?: any
}

export interface AIAssistantProps {
  className?: string
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  defaultOpen?: boolean
  onAction?: (action: AIAction) => void
}

const AIAssistant: React.FC<AIAssistantProps> = ({
  className,
  position = 'bottom-right',
  defaultOpen = false,
  onAction
}) => {
  const isEnabled = useExperimentalFeature('ai-assistant')
  const { trackFeatureUsage, trackFeatureError } = useFeatureAnalytics()
  
  const [isOpen, setIsOpen] = React.useState(defaultOpen)
  const [isMinimized, setIsMinimized] = React.useState(false)
  const [messages, setMessages] = React.useState<AIMessage[]>([
    {
      id: '1',
      type: 'system',
      content: 'Hi! I\'m your AI assistant. I can help you navigate the system, find information, and suggest optimizations. What would you like to do?',
      timestamp: Date.now(),
      metadata: {
        suggestions: [
          'Show me user analytics',
          'How do I create a new project?',
          'Find performance issues',
          'Generate a report'
        ]
      }
    }
  ])
  const [inputValue, setInputValue] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)
  const [context, setContext] = React.useState({
    currentPage: window.location.pathname,
    userRole: 'user', // Would come from auth context
    recentActions: [] as string[]
  })

  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Track feature usage
  React.useEffect(() => {
    if (isOpen) {
      trackFeatureUsage('ai-assistant', 'opened')
    }
  }, [isOpen, trackFeatureUsage])

  if (!isEnabled) return null

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: AIMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: Date.now()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Simulate AI response (in production, this would call an AI service)
      const response = await simulateAIResponse(inputValue, context)
      
      setMessages(prev => [...prev, response])
      trackFeatureUsage('ai-assistant', 'message_sent', { 
        messageLength: inputValue.length,
        hasActions: response.metadata?.actions ? response.metadata.actions.length > 0 : false
      })
    } catch (error) {
      trackFeatureError('ai-assistant', error as Error)
      
      const errorMessage: AIMessage = {
        id: Date.now().toString(),
        type: 'system',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: Date.now()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion)
  }

  const handleActionClick = (action: AIAction) => {
    trackFeatureUsage('ai-assistant', 'action_clicked', { actionType: action.type })
    onAction?.(action)
  }

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'fixed z-50 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all duration-200 flex items-center justify-center group',
          positionClasses[position],
          className
        )}
        title="Open AI Assistant"
      >
        <Bot className="h-6 w-6" />
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-pulse group-hover:animate-none" />
      </button>
    )
  }

  return (
    <div
      className={cn(
        'fixed z-50 bg-white rounded-lg shadow-xl border',
        positionClasses[position],
        isMinimized ? 'w-80 h-12' : 'w-96 h-96',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <Bot className="h-4 w-4 text-blue-600" />
          </div>
          <div>
            <h3 className="text-sm font-medium">AI Assistant</h3>
            {!isMinimized && (
              <p className="text-xs text-gray-500">Here to help you navigate</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-gray-100 rounded"
            title={isMinimized ? 'Maximize' : 'Minimize'}
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3" style={{ height: '280px' }}>
            {messages.map((message) => (
              <MessageBubble 
                key={message.id} 
                message={message} 
                onSuggestionClick={handleSuggestionClick}
                onActionClick={handleActionClick}
              />
            ))}
            {isLoading && (
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
                <span className="text-xs">AI is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask me anything..."
                className="flex-1 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

interface MessageBubbleProps {
  message: AIMessage
  onSuggestionClick: (suggestion: string) => void
  onActionClick: (action: AIAction) => void
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  onSuggestionClick,
  onActionClick 
}) => {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-xs px-3 py-2 rounded-lg text-sm',
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : isSystem
              ? 'bg-gray-100 text-gray-700 rounded-bl-sm'
              : 'bg-gray-100 text-gray-700 rounded-bl-sm'
        )}
      >
        <div>{message.content}</div>
        
        {/* Suggestions */}
        {message.metadata?.suggestions && (
          <div className="mt-2 space-y-1">
            {message.metadata.suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                className="block w-full text-left px-2 py-1 bg-white bg-opacity-20 rounded text-xs hover:bg-opacity-30 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Actions */}
        {message.metadata?.actions && (
          <div className="mt-2 space-y-1">
            {message.metadata.actions.map((action) => (
              <button
                key={action.id}
                onClick={() => onActionClick(action)}
                className="flex items-center space-x-1 w-full text-left px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors"
              >
                <ActionIcon type={action.type} />
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* Metadata */}
        {message.metadata?.confidence && (
          <div className="mt-1 text-xs opacity-75">
            Confidence: {Math.round(message.metadata.confidence * 100)}%
          </div>
        )}
      </div>
    </div>
  )
}

const ActionIcon: React.FC<{ type: AIAction['type'] }> = ({ type }) => {
  const icons = {
    navigation: <MessageCircle className="h-3 w-3" />,
    search: <Search className="h-3 w-3" />,
    create: <Lightbulb className="h-3 w-3" />,
    update: <Zap className="h-3 w-3" />,
    delete: <X className="h-3 w-3" />
  }
  
  return icons[type] || <HelpCircle className="h-3 w-3" />
}

// Simulate AI response (replace with actual AI service)
const simulateAIResponse = async (input: string, context: any): Promise<AIMessage> => {
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

  const lowerInput = input.toLowerCase()
  
  // Simple pattern matching for demo
  if (lowerInput.includes('user') || lowerInput.includes('analytics')) {
    return {
      id: Date.now().toString(),
      type: 'assistant',
      content: 'I can help you with user analytics! Here are some quick actions you can take:',
      timestamp: Date.now(),
      metadata: {
        confidence: 0.9,
        actions: [
          {
            id: 'nav-users',
            label: 'Go to Users Page',
            type: 'navigation',
            target: '/users'
          },
          {
            id: 'search-users',
            label: 'Search Users',
            type: 'search',
            target: 'users'
          }
        ]
      }
    }
  }

  if (lowerInput.includes('project') || lowerInput.includes('create')) {
    return {
      id: Date.now().toString(),
      type: 'assistant',
      content: 'I can help you create a new project! Would you like me to guide you through the process?',
      timestamp: Date.now(),
      metadata: {
        confidence: 0.85,
        actions: [
          {
            id: 'create-project',
            label: 'Create New Project',
            type: 'create',
            target: 'project'
          },
          {
            id: 'nav-projects',
            label: 'View All Projects',
            type: 'navigation',
            target: '/projects'
          }
        ],
        suggestions: [
          'What information do I need for a new project?',
          'Show me project templates',
          'How do I assign team members?'
        ]
      }
    }
  }

  if (lowerInput.includes('performance') || lowerInput.includes('slow') || lowerInput.includes('issue')) {
    return {
      id: Date.now().toString(),
      type: 'assistant',
      content: 'I can help you identify performance issues. Based on the current page, here are some recommendations:',
      timestamp: Date.now(),
      metadata: {
        confidence: 0.8,
        actions: [
          {
            id: 'performance-report',
            label: 'Generate Performance Report',
            type: 'create',
            target: 'performance-report'
          },
          {
            id: 'nav-analytics',
            label: 'View Analytics Dashboard',
            type: 'navigation',
            target: '/analytics'
          }
        ]
      }
    }
  }

  // Default response
  return {
    id: Date.now().toString(),
    type: 'assistant',
    content: `I understand you're asking about "${input}". While I'm still learning, I can help you navigate the system. What specific task would you like to accomplish?`,
    timestamp: Date.now(),
    metadata: {
      confidence: 0.6,
      suggestions: [
        'Show me the dashboard',
        'Help me find user data',
        'Create a new report',
        'Explain this page'
      ]
    }
  }
}

export default AIAssistant