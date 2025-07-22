import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

// 認証関連の型定義
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  permissions: string[];
  avatar?: string;
  lastLoginAt?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const TOKEN_KEY = 'auth_tokens';
const USER_KEY = 'auth_user';
const REMEMBER_ME_KEY = 'remember_me';

// API関数（実際の実装では外部サービスファイルに分離）
const authAPI = {
  login: async (credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> => {
    // モックAPIレスポンス（実際の実装では外部API呼び出し）
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (credentials.username === 'admin' && credentials.password === 'password') {
          resolve({
            user: {
              id: '1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Admin',
              lastName: 'User',
              roles: ['admin'],
              permissions: ['read', 'write', 'delete'],
              lastLoginAt: new Date().toISOString(),
            },
            tokens: {
              accessToken: 'mock_access_token_' + Date.now(),
              refreshToken: 'mock_refresh_token_' + Date.now(),
              expiresIn: 3600, // 1時間
              tokenType: 'Bearer',
            },
          });
        } else {
          reject(new Error('無効なユーザー名またはパスワードです'));
        }
      }, 1000);
    });
  },

  logout: async (): Promise<void> => {
    return new Promise(resolve => {
      setTimeout(resolve, 500);
    });
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (refreshToken) {
          resolve({
            accessToken: 'new_mock_access_token_' + Date.now(),
            refreshToken: 'new_mock_refresh_token_' + Date.now(),
            expiresIn: 3600,
            tokenType: 'Bearer',
          });
        } else {
          reject(new Error('リフレッシュトークンが無効です'));
        }
      }, 500);
    });
  },

  getCurrentUser: async (): Promise<User> => {
    return new Promise(resolve => {
      const savedUser = localStorage.getItem(USER_KEY);
      if (savedUser) {
        resolve(JSON.parse(savedUser));
      } else {
        resolve({
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          firstName: 'Admin',
          lastName: 'User',
          roles: ['admin'],
          permissions: ['read', 'write', 'delete'],
        });
      }
    });
  },
};

export const useAuth = () => {
  const [state, setState] = useState<AuthState>({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  const navigate = useNavigate();

  // トークンをローカルストレージに保存
  const saveTokens = useCallback((tokens: AuthTokens, rememberMe: boolean = false) => {
    if (rememberMe) {
      localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
      localStorage.setItem(REMEMBER_ME_KEY, 'true');
    } else {
      sessionStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
      localStorage.removeItem(REMEMBER_ME_KEY);
    }
  }, []);

  // トークンをストレージから取得
  const getStoredTokens = useCallback((): AuthTokens | null => {
    const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
    const storage = rememberMe ? localStorage : sessionStorage;
    const tokensStr = storage.getItem(TOKEN_KEY);
    
    if (tokensStr) {
      try {
        return JSON.parse(tokensStr);
      } catch {
        return null;
      }
    }
    return null;
  }, []);

  // トークンをストレージから削除
  const removeTokens = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(REMEMBER_ME_KEY);
  }, []);

  // ユーザー情報を保存
  const saveUser = useCallback((user: User) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }, []);

  // トークンの有効性をチェック
  const isTokenValid = useCallback((tokens: AuthTokens): boolean => {
    if (!tokens) return false;
    
    // JWT トークンのデコード（簡易版）
    try {
      const payload = JSON.parse(atob(tokens.accessToken.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp > currentTime;
    } catch {
      // モックトークンの場合は常にtrueを返す
      return true;
    }
  }, []);

  // ログイン
  const login = useCallback(async (credentials: LoginCredentials) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const { user, tokens } = await authAPI.login(credentials);
      
      saveTokens(tokens, credentials.rememberMe || false);
      saveUser(user);
      
      setState({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      navigate('/dashboard');
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'ログインに失敗しました',
      }));
    }
  }, [navigate, saveTokens, saveUser]);

  // ログアウト
  const logout = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      await authAPI.logout();
    } catch (error) {
      console.warn('ログアウト処理でエラーが発生しました:', error);
    } finally {
      removeTokens();
      setState({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
      navigate('/login');
    }
  }, [navigate, removeTokens]);

  // トークンリフレッシュ
  const refreshAccessToken = useCallback(async () => {
    const tokens = getStoredTokens();
    if (!tokens) return false;

    try {
      const newTokens = await authAPI.refreshToken(tokens.refreshToken);
      const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
      
      saveTokens(newTokens, rememberMe);
      setState(prev => ({ ...prev, tokens: newTokens }));
      
      return true;
    } catch (error) {
      console.error('トークンリフレッシュに失敗:', error);
      logout();
      return false;
    }
  }, [getStoredTokens, saveTokens, logout]);

  // 権限チェック
  const hasPermission = useCallback((permission: string): boolean => {
    return state.user?.permissions.includes(permission) || false;
  }, [state.user]);

  const hasRole = useCallback((role: string): boolean => {
    return state.user?.roles.includes(role) || false;
  }, [state.user]);

  // 初期化処理
  useEffect(() => {
    const initializeAuth = async () => {
      const tokens = getStoredTokens();
      
      if (tokens && isTokenValid(tokens)) {
        try {
          const user = await authAPI.getCurrentUser();
          setState({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          console.error('ユーザー情報の取得に失敗:', error);
          removeTokens();
          setState({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } else {
        setState(prev => ({ ...prev, isLoading: false }));
      }
    };

    initializeAuth();
  }, [getStoredTokens, isTokenValid, removeTokens]);

  // 自動ログアウト（トークン期限切れ）
  useEffect(() => {
    if (!state.tokens) return;

    const checkTokenExpiration = () => {
      if (!isTokenValid(state.tokens!)) {
        logout();
      }
    };

    // 1分おきにトークンをチェック
    const interval = setInterval(checkTokenExpiration, 60000);
    
    return () => clearInterval(interval);
  }, [state.tokens, isTokenValid, logout]);

  return {
    ...state,
    login,
    logout,
    refreshAccessToken,
    hasPermission,
    hasRole,
  };
};