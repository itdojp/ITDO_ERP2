// Hooks Barrel Export File
// This file provides a centralized export point for all custom hooks

export { default as useLoading } from './useLoading'
export type { UseLoadingReturn, LoadingState } from './useLoading'

// Re-export all user profile hooks (no default export)
export * from './useUserProfile'

export { default as useFormValidation, ValidationRules } from './useFormValidation'
export type { 
  ValidationRule, 
  FieldValidation, 
  FormValidationConfig, 
  ValidationError, 
  FormValidationState, 
  FormValidationOptions 
} from './useFormValidation'

// Error handling hooks
export {
  useErrorHandler,
  useQueryErrorHandler,
  useMutationErrorHandler,
  useFormErrorHandler,
  useGlobalErrorHandler,
  classifyError,
  getUserFriendlyMessage,
} from './useErrorHandler'
export type { 
  ErrorType, 
  ErrorDetails, 
  ErrorHandlerOptions 
} from './useErrorHandler'

// Performance monitoring hooks
export {
  usePerformanceMonitor,
  withPerformanceMonitoring,
} from './usePerformanceMonitor'
export type {
  PerformanceMetric,
  ComponentPerformanceData,
  PerformanceThresholds,
  PerformanceMonitorOptions,
} from './usePerformanceMonitor'

// Accessibility hooks
export {
  useAccessibility,
  useFocusManagement,
  useFocusTrap,
  useKeyboardNavigation,
  useScreenReaderAnnouncements,
} from './useAccessibility'
export type {
  AccessibilityPreferences,
  UseAccessibilityOptions,
  FocusManagementOptions,
} from './useAccessibility'

// Real-time synchronization hooks
export { useWebSocket, useRealTimeSync } from './useWebSocket'
export { useRealTimeSync as default } from './useRealTimeSync'
export type {
  WebSocketOptions,
  UseWebSocketReturn,
  WebSocketState,
  RealTimeSyncOptions,
  UserActivity,
  RealTimeEvent,
  CollaborationState,
} from './useWebSocket'

// Search and filtering hooks
export { useAdvancedSearch, useDebounce } from './useAdvancedSearch'
export { useDebounce as default } from './useDebounce'
export type {
  SearchFilter,
  SearchSort,
  SearchFacet,
  SearchOptions,
  SearchResult,
  FacetResult,
  FacetBucket,
  SearchResponse,
  UseAdvancedSearchOptions,
  UseAdvancedSearchReturn,
  FilterOperator,
} from './useAdvancedSearch'

// Permission and RBAC hooks
export {
  usePermissions,
  usePermissionContext,
  PermissionProvider,
  PermissionContext,
} from './usePermissions'
export type {
  PermissionContext as PermissionContextType,
  UsePermissionsOptions,
} from './usePermissions'

// Performance optimization hooks
export { 
  usePerformanceMonitor, 
  withPerformanceMonitor 
} from './usePerformanceMonitor'
export { 
  useVirtualization, 
  useDynamicVirtualization, 
  VirtualList, 
  VirtualTableRow 
} from './useVirtualization'
export { 
  useMemoizedCallback,
  useStableCallback,
  useCancellableCallback,
  useDebouncedCallback,
  useThrottledCallback,
  useRetryCallback,
  useBatchedCallback,
  useDeepMemoizedCallback
} from './useMemoizedCallback'

// Memory optimization hooks
export {
  useMemoryOptimizedCallback,
  useMemoryOptimizedState,
  useMemoryOptimizedEffect,
  useMemoryOptimizedCache,
  useMemoryOptimizedRef,
  useMemoryOptimizedTimer,
  useMemoryOptimizedEventListener,
  useMemoryOptimizedIntersectionObserver,
  useMemoryUsage,
  useCleanupManager
} from './useMemoryOptimization'

// Query hooks
export * from './queries'