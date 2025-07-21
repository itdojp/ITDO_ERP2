import axios, { 
  AxiosInstance, 
  AxiosRequestConfig, 
  AxiosResponse, 
  AxiosError,
  InternalAxiosRequestConfig 
} from 'axios'

export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
  timestamp: string
  version: string
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

export interface ApiError {
  code: string
  message: string
  details?: any
  field?: string
  timestamp: string
}

export interface RequestOptions extends AxiosRequestConfig {
  skipAuth?: boolean
  skipErrorHandling?: boolean
  retries?: number
  timeout?: number
}

// Authentication token management
class TokenManager {
  private accessToken: string | null = null
  private refreshToken: string | null = null
  private refreshPromise: Promise<string> | null = null

  constructor() {
    this.loadTokensFromStorage()
  }

  private loadTokensFromStorage() {
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token')
      this.refreshToken = localStorage.getItem('refresh_token')
    }
  }

  setTokens(accessToken: string, refreshToken?: string) {
    this.accessToken = accessToken
    if (refreshToken) {
      this.refreshToken = refreshToken
    }
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken)
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
      }
    }
  }

  getAccessToken(): string | null {
    return this.accessToken
  }

  getRefreshToken(): string | null {
    return this.refreshToken
  }

  clearTokens() {
    this.accessToken = null
    this.refreshToken = null
    
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async refreshAccessToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise
    }

    if (!this.refreshToken) {
      throw new Error('No refresh token available')
    }

    this.refreshPromise = this.performTokenRefresh()
    
    try {
      const newToken = await this.refreshPromise
      return newToken
    } finally {
      this.refreshPromise = null
    }
  }

  private async performTokenRefresh(): Promise<string> {
    try {
      const response = await axios.post('/api/auth/refresh', {
        refresh_token: this.refreshToken
      })

      const { access_token, refresh_token } = response.data.data
      this.setTokens(access_token, refresh_token)
      
      return access_token
    } catch (error) {
      this.clearTokens()
      // Redirect to login or emit logout event
      window.dispatchEvent(new CustomEvent('auth:logout'))
      throw error
    }
  }
}

// API Client class
export class ApiClient {
  private client: AxiosInstance
  private tokenManager: TokenManager
  private baseURL: string
  private defaultTimeout: number = 30000

  constructor(baseURL: string = process.env.REACT_APP_API_BASE_URL || '/api') {
    this.baseURL = baseURL
    this.tokenManager = new TokenManager()
    this.client = this.createAxiosInstance()
    this.setupInterceptors()
  }

  private createAxiosInstance(): AxiosInstance {
    return axios.create({
      baseURL: this.baseURL,
      timeout: this.defaultTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    })
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add auth token
        const token = this.tokenManager.getAccessToken()
        if (token && !config.skipAuth) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId()

        // Add timestamp
        config.headers['X-Timestamp'] = new Date().toISOString()

        return config
      },
      (error: AxiosError) => {
        return Promise.reject(this.transformError(error))
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return this.transformResponse(response)
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        // Handle 401 Unauthorized - attempt token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const newToken = await this.tokenManager.refreshAccessToken()
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed, redirect to login
            return Promise.reject(this.transformError(error))
          }
        }

        return Promise.reject(this.transformError(error))
      }
    )
  }

  private transformResponse(response: AxiosResponse): AxiosResponse {
    // Ensure consistent response format
    if (response.data && typeof response.data === 'object') {
      if (!response.data.hasOwnProperty('success')) {
        response.data = {
          data: response.data,
          success: true,
          timestamp: new Date().toISOString(),
          version: '1.0'
        }
      }
    }

    return response
  }

  private transformError(error: AxiosError): ApiError {
    const apiError: ApiError = {
      code: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred',
      timestamp: new Date().toISOString(),
    }

    if (error.response) {
      // Server responded with error status
      const responseData = error.response.data as any
      
      apiError.code = responseData?.code || `HTTP_${error.response.status}`
      apiError.message = responseData?.message || error.message
      apiError.details = responseData?.details
      apiError.field = responseData?.field
    } else if (error.request) {
      // Request was made but no response received
      apiError.code = 'NETWORK_ERROR'
      apiError.message = 'Network error - please check your connection'
    } else {
      // Something else happened
      apiError.message = error.message
    }

    return apiError
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // HTTP Methods
  async get<T = any>(
    url: string, 
    config?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, config)
    return response.data
  }

  async post<T = any>(
    url: string, 
    data?: any, 
    config?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async put<T = any>(
    url: string, 
    data?: any, 
    config?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async patch<T = any>(
    url: string, 
    data?: any, 
    config?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async delete<T = any>(
    url: string, 
    config?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url, config)
    return response.data
  }

  // Specialized methods
  async upload<T = any>(
    url: string,
    file: File | FormData,
    config?: RequestOptions & {
      onUploadProgress?: (progressEvent: any) => void
    }
  ): Promise<ApiResponse<T>> {
    const formData = file instanceof FormData ? file : new FormData()
    if (file instanceof File) {
      formData.append('file', file)
    }

    const response = await this.client.post<ApiResponse<T>>(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
    })

    return response.data
  }

  async download(
    url: string,
    filename?: string,
    config?: RequestOptions
  ): Promise<void> {
    const response = await this.client.get(url, {
      ...config,
      responseType: 'blob',
    })

    // Create download link
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  // Paginated requests
  async getPaginated<T = any>(
    url: string,
    params?: {
      page?: number
      limit?: number
      sort?: string
      order?: 'asc' | 'desc'
      [key: string]: any
    },
    config?: RequestOptions
  ): Promise<PaginatedResponse<T>> {
    const response = await this.client.get<PaginatedResponse<T>>(url, {
      ...config,
      params,
    })
    return response.data
  }

  // Batch requests
  async batch<T = any>(
    requests: Array<{
      method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
      url: string
      data?: any
      config?: RequestOptions
    }>
  ): Promise<ApiResponse<T>[]> {
    const promises = requests.map(req => {
      switch (req.method) {
        case 'GET':
          return this.get(req.url, req.config)
        case 'POST':
          return this.post(req.url, req.data, req.config)
        case 'PUT':
          return this.put(req.url, req.data, req.config)
        case 'PATCH':
          return this.patch(req.url, req.data, req.config)
        case 'DELETE':
          return this.delete(req.url, req.config)
        default:
          throw new Error(`Unsupported method: ${req.method}`)
      }
    })

    return Promise.all(promises)
  }

  // Retry mechanism
  async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: any

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error
        
        if (attempt === maxRetries) {
          break
        }

        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt - 1)))
      }
    }

    throw lastError
  }

  // Authentication methods
  setAuthToken(accessToken: string, refreshToken?: string) {
    this.tokenManager.setTokens(accessToken, refreshToken)
  }

  clearAuthToken() {
    this.tokenManager.clearTokens()
  }

  getAuthToken(): string | null {
    return this.tokenManager.getAccessToken()
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health', { skipAuth: true })
      return true
    } catch {
      return false
    }
  }
}

// Create default API client instance
export const apiClient = new ApiClient()

// Export utility functions
export const createApiClient = (baseURL?: string) => new ApiClient(baseURL)

export default apiClient