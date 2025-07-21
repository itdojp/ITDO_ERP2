// Query hooks barrel export file
// This file provides a centralized export point for all query hooks

// User queries
export * from './useUsers'

// Dashboard queries  
export * from './useDashboard'

// Project queries
export * from './useProjects'

// Re-export query client utilities
export { queryClient, queryKeys, invalidateQueries, prefetchQueries, cacheUtils, handleApiError, QueryError } from '../../lib/queryClient'

// Common query types
export interface QueryOptions {
  enabled?: boolean
  staleTime?: number
  cacheTime?: number
  refetchOnMount?: boolean
  refetchOnWindowFocus?: boolean
  refetchOnReconnect?: boolean
}

export interface PaginatedQueryParams {
  page?: number
  limit?: number
  search?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface DateRangeParams {
  start?: Date | string
  end?: Date | string
}

// Query result helpers
export type QueryStatus = 'idle' | 'loading' | 'error' | 'success'

export interface BaseQueryResult<T> {
  data: T | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
  isSuccess: boolean
  isFetching: boolean
  refetch: () => void
}

export interface PaginatedQueryResult<T> extends BaseQueryResult<T> {
  hasNextPage?: boolean
  hasPreviousPage?: boolean
  fetchNextPage?: () => void
  fetchPreviousPage?: () => void
}

// Mutation result helpers
export interface BaseMutationResult<TData = any, TVariables = any> {
  mutate: (variables: TVariables) => void
  mutateAsync: (variables: TVariables) => Promise<TData>
  isLoading: boolean
  isError: boolean
  error: Error | null
  isSuccess: boolean
  reset: () => void
}

// Common query patterns
export const createInfiniteQueryHook = <T, TParams>(
  queryKeyFactory: (params: TParams) => readonly unknown[],
  queryFn: (params: TParams & { pageParam?: any }) => Promise<{ data: T[]; nextCursor?: any; hasMore: boolean }>
) => {
  return (params: TParams) => {
    return useInfiniteQuery({
      queryKey: queryKeyFactory(params),
      queryFn: ({ pageParam }) => queryFn({ ...params, pageParam }),
      getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.nextCursor : undefined,
      getPreviousPageParam: (firstPage) => firstPage.nextCursor ? undefined : undefined,
    })
  }
}

// Error handling utilities
export const isNetworkError = (error: any): boolean => {
  return error?.message?.includes('Network Error') || error?.code === 'NETWORK_ERROR'
}

export const isTimeoutError = (error: any): boolean => {
  return error?.message?.includes('timeout') || error?.code === 'TIMEOUT_ERROR'  
}

export const isAuthError = (error: any): boolean => {
  return error?.status === 401 || error?.status === 403
}

export const isValidationError = (error: any): boolean => {
  return error?.status === 400 || error?.status === 422
}

export const getErrorMessage = (error: any): string => {
  if (typeof error === 'string') return error
  if (error?.message) return error.message
  if (error?.data?.message) return error.data.message
  if (isNetworkError(error)) return 'Network connection error. Please check your internet connection.'
  if (isTimeoutError(error)) return 'Request timed out. Please try again.'
  if (isAuthError(error)) return 'Authentication required. Please log in.'
  if (isValidationError(error)) return 'Invalid data provided. Please check your input.'
  return 'An unexpected error occurred. Please try again.'
}

// Import useInfiniteQuery for the helper function
import { useInfiniteQuery } from '@tanstack/react-query'