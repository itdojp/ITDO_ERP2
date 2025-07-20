import { apiClient } from './api'

export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

export interface User {
  id: string
  email: string
  name: string
  role?: string
}

export interface LoginResponse {
  user: User
  token: string
  refreshToken?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

class AuthService {
  private static instance: AuthService
  private authState: AuthState = {
    user: null,
    token: null,
    isAuthenticated: false
  }

  private constructor() {
    // Initialize auth state from localStorage
    this.loadAuthState()
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService()
    }
    return AuthService.instance
  }

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials)
      const { user, token, refreshToken } = response.data

      // Store tokens
      localStorage.setItem('token', token)
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken)
      }
      
      // Store user info
      localStorage.setItem('user', JSON.stringify(user))

      // Update auth state
      this.authState = {
        user,
        token,
        isAuthenticated: true
      }

      // Set session cookies for E2E tests
      this.setSessionCookies(credentials.rememberMe || false)

      return response.data
    } catch (error) {
      this.clearAuthState()
      throw error
    }
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      console.warn('Logout API call failed:', error)
    } finally {
      this.clearAuthState()
    }
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refreshToken')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await apiClient.post<{ token: string }>('/auth/refresh', {
        refreshToken
      })

      const { token } = response.data
      localStorage.setItem('token', token)
      this.authState.token = token

      return token
    } catch (error) {
      this.clearAuthState()
      throw error
    }
  }

  getCurrentUser(): User | null {
    return this.authState.user
  }

  getToken(): string | null {
    return this.authState.token
  }

  isAuthenticated(): boolean {
    return this.authState.isAuthenticated && !!this.authState.token
  }

  private loadAuthState(): void {
    try {
      const token = localStorage.getItem('token')
      const userJson = localStorage.getItem('user')

      if (token && userJson) {
        const user = JSON.parse(userJson)
        this.authState = {
          user,
          token,
          isAuthenticated: true
        }
      }
    } catch (error) {
      console.warn('Failed to load auth state:', error)
      this.clearAuthState()
    }
  }

  private clearAuthState(): void {
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
    
    // Clear session cookies
    this.clearSessionCookies()

    this.authState = {
      user: null,
      token: null,
      isAuthenticated: false
    }
  }

  private setSessionCookies(rememberMe: boolean): void {
    // Set session cookie for E2E tests
    const expires = rememberMe 
      ? new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      : new Date(Date.now() + 24 * 60 * 60 * 1000) // 1 day

    document.cookie = `session=active; expires=${expires.toUTCString()}; path=/; SameSite=Lax`
    
    if (rememberMe) {
      const rememberExpires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days
      document.cookie = `remember_token=active; expires=${rememberExpires.toUTCString()}; path=/; SameSite=Lax`
    }
  }

  private clearSessionCookies(): void {
    document.cookie = 'session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
    document.cookie = 'remember_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
  }

  // Session timeout handling
  handleSessionTimeout(): void {
    this.clearAuthState()
    
    // Add session expired marker for E2E tests
    const currentPath = window.location.pathname
    if (currentPath !== '/login') {
      const url = new URL('/login', window.location.origin)
      url.searchParams.set('redirect', currentPath)
      url.searchParams.set('expired', 'true')
      window.location.href = url.toString()
    }
  }
}

// Export singleton instance
export const authService = AuthService.getInstance()

// Export helper functions for components
export const useAuthState = () => {
  return {
    user: authService.getCurrentUser(),
    token: authService.getToken(),
    isAuthenticated: authService.isAuthenticated()
  }
}