import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Alert } from "../ui/Alert";
import { Card } from "../ui/Card";
import { Form } from "../ui/Form";
import { useAuth } from "../../hooks/useAuth";

interface PasswordStrength {
  score: number;
  feedback: string[];
}

export const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { resetPassword, verifyResetToken } = useAuth();
  const [formData, setFormData] = useState({
    password: "",
    confirmPassword: "",
    verificationCode: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
    score: 0,
    feedback: [],
  });

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      navigate("/auth/forgot-password");
      return;
    }

    const verifyToken = async () => {
      try {
        await verifyResetToken(token);
        setTokenValid(true);
      } catch (err) {
        setError("無効または期限切れのリンクです");
      } finally {
        setVerifying(false);
      }
    };

    verifyToken();
  }, [token, navigate, verifyResetToken]);

  const checkPasswordStrength = (password: string): PasswordStrength => {
    const feedback: string[] = [];
    let score = 0;

    if (password.length >= 8) score++;
    else feedback.push("8文字以上必要です");

    if (/[A-Z]/.test(password)) score++;
    else feedback.push("大文字を含めてください");

    if (/[a-z]/.test(password)) score++;
    else feedback.push("小文字を含めてください");

    if (/\d/.test(password)) score++;
    else feedback.push("数字を含めてください");

    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;
    else feedback.push("特殊文字を含めてください");

    return { score, feedback };
  };

  const handlePasswordChange = (password: string) => {
    setFormData({ ...formData, password });
    setPasswordStrength(checkPasswordStrength(password));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError("パスワードが一致しません");
      return;
    }

    if (passwordStrength.score < 3) {
      setError(
        "パスワードが弱すぎます。より強力なパスワードを設定してください",
      );
      return;
    }

    setLoading(true);

    try {
      await resetPassword(
        token!,
        formData.password,
        formData.verificationCode || undefined,
      );

      // Reset successful
      navigate("/auth/login", {
        state: {
          message:
            "パスワードがリセットされました。新しいパスワードでログインしてください。",
        },
      });
    } catch (err: any) {
      setError(err.message || "パスワードのリセットに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength.score <= 2) return "bg-red-500";
    if (passwordStrength.score === 3) return "bg-yellow-500";
    return "bg-green-500";
  };

  if (verifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">確認中...</p>
        </div>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <Card className="text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              リンクが無効です
            </h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button
              onClick={() => navigate("/auth/forgot-password")}
              variant="primary"
              className="w-full"
            >
              パスワードリセットを再リクエスト
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            新しいパスワードを設定
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            安全なパスワードを設定してください
          </p>
        </div>
        <Card className="mt-8">
          <Form onSubmit={handleSubmit} className="space-y-6">
            {error && <Alert type="error" message={error} />}

            <div>
              <label
                htmlFor="verificationCode"
                className="block text-sm font-medium text-gray-700"
              >
                確認コード（メールに記載）
              </label>
              <Input
                id="verificationCode"
                name="verificationCode"
                type="text"
                value={formData.verificationCode}
                onChange={(e) =>
                  setFormData({ ...formData, verificationCode: e.target.value })
                }
                className="mt-1"
                placeholder="123456"
                maxLength={6}
                pattern="[0-9]{6}"
              />
              <p className="mt-1 text-sm text-gray-500">
                メールに記載された6桁の確認コードを入力してください（任意）
              </p>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                新しいパスワード
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                className="mt-1"
                placeholder="••••••••"
              />
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${getPasswordStrengthColor()}`}
                        style={{
                          width: `${(passwordStrength.score / 5) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-600">
                      {passwordStrength.score <= 2
                        ? "弱い"
                        : passwordStrength.score === 3
                          ? "普通"
                          : "強い"}
                    </span>
                  </div>
                  {passwordStrength.feedback.length > 0 && (
                    <ul className="mt-1 text-xs text-gray-600">
                      {passwordStrength.feedback.map((item, index) => (
                        <li key={index}>• {item}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700"
              >
                新しいパスワード（確認）
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={(e) =>
                  setFormData({ ...formData, confirmPassword: e.target.value })
                }
                className="mt-1"
                placeholder="••••••••"
              />
              {formData.confirmPassword &&
                formData.password !== formData.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">
                    パスワードが一致しません
                  </p>
                )}
            </div>

            <div>
              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={loading}
              >
                {loading ? "パスワードを変更中..." : "パスワードを変更"}
              </Button>
            </div>
          </Form>
        </Card>
      </div>
    </div>
  );
};
