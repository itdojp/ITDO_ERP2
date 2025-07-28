import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../services/api/client";

interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  mfa_required: boolean;
  has_google_account: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface LoginResponse {
  access_token?: string;
  token_type?: string;
  requires_mfa?: boolean;
  mfa_token?: string;
}

export const useAuth = () => {
  const navigate = useNavigate();
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("access_token");
      if (token) {
        try {
          const response = await apiClient.get("/api/v1/users/me");
          setAuthState({
            user: response.data,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          localStorage.removeItem("access_token");
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(
    async (
      email: string,
      password: string,
      rememberMe: boolean = false,
    ): Promise<LoginResponse> => {
      try {
        const response = await apiClient.post("/api/v1/auth/login", {
          email,
          password,
          remember_me: rememberMe,
        });

        const data: LoginResponse = response.data;

        if (data.requires_mfa) {
          // MFA required, return the response for MFA handling
          return data;
        }

        // Login successful
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);

          // Get user info
          const userResponse = await apiClient.get("/api/v1/users/me");
          setAuthState({
            user: userResponse.data,
            isAuthenticated: true,
            isLoading: false,
          });
        }

        return data;
      } catch (error: any) {
        throw new Error(
          error.response?.data?.detail || "ログインに失敗しました",
        );
      }
    },
    [],
  );

  const loginWithGoogle = useCallback(async () => {
    try {
      const response = await apiClient.get("/api/v1/auth/google/authorize");
      const { auth_url } = response.data;

      // Redirect to Google OAuth
      window.location.href = auth_url;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || "Googleログインに失敗しました",
      );
    }
  }, []);

  const verifyMFA = useCallback(
    async (mfaToken: string, code: string, isBackupCode: boolean = false) => {
      try {
        const response = await apiClient.post("/api/v1/auth/mfa/verify", {
          mfa_token: mfaToken,
          code,
          is_backup_code: isBackupCode,
        });

        const { access_token } = response.data;
        localStorage.setItem("access_token", access_token);

        // Get user info
        const userResponse = await apiClient.get("/api/v1/users/me");
        setAuthState({
          user: userResponse.data,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch (error: any) {
        throw new Error(
          error.response?.data?.detail || "MFA認証に失敗しました",
        );
      }
    },
    [],
  );

  const register = useCallback(
    async (userData: {
      email: string;
      password: string;
      full_name: string;
    }) => {
      try {
        await apiClient.post("/api/v1/users/register", userData);
      } catch (error: any) {
        throw new Error(
          error.response?.data?.detail || "アカウント作成に失敗しました",
        );
      }
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await apiClient.post("/api/v1/auth/logout");
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      localStorage.removeItem("access_token");
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
      navigate("/auth/login");
    }
  }, [navigate]);

  const requestPasswordReset = useCallback(async (email: string) => {
    try {
      await apiClient.post("/api/v1/password-reset/request", { email });
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || "リクエストの処理に失敗しました",
      );
    }
  }, []);

  const verifyResetToken = useCallback(async (token: string) => {
    try {
      const response = await apiClient.post("/api/v1/password-reset/verify", {
        token,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || "トークンの検証に失敗しました",
      );
    }
  }, []);

  const resetPassword = useCallback(
    async (token: string, newPassword: string, verificationCode?: string) => {
      try {
        await apiClient.post("/api/v1/password-reset/reset", {
          token,
          new_password: newPassword,
          verification_code: verificationCode,
        });
      } catch (error: any) {
        throw new Error(
          error.response?.data?.detail || "パスワードのリセットに失敗しました",
        );
      }
    },
    [],
  );

  const setupMFA = useCallback(async (method: string = "totp") => {
    try {
      const response = await apiClient.post("/api/v1/mfa/setup", { method });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || "MFAセットアップに失敗しました",
      );
    }
  }, []);

  const verifyMFASetup = useCallback(
    async (code: string, deviceName: string) => {
      try {
        await apiClient.post("/api/v1/mfa/verify-setup", {
          code,
          device_name: deviceName,
        });
      } catch (error: any) {
        throw new Error(
          error.response?.data?.detail || "MFA設定の確認に失敗しました",
        );
      }
    },
    [],
  );

  const disableMFA = useCallback(
    async (password: string) => {
      try {
        await apiClient.post("/api/v1/mfa/disable", { password });

        // Update user state
        if (authState.user) {
          setAuthState({
            ...authState,
            user: { ...authState.user, mfa_required: false },
          });
        }
      } catch (error: any) {
        throw new Error(
          error.response?.data?.detail || "MFAの無効化に失敗しました",
        );
      }
    },
    [authState],
  );

  return {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
    loginWithGoogle,
    verifyMFA,
    register,
    logout,
    requestPasswordReset,
    verifyResetToken,
    resetPassword,
    setupMFA,
    verifyMFASetup,
    disableMFA,
  };
};
