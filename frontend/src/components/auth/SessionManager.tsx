import React, { useState, useEffect } from "react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Alert } from "../ui/Alert";
import { Badge } from "../ui/Badge";
import { Modal } from "../ui/Modal";
import { DataTable } from "../ui/DataTable";
import { Switch } from "../ui/Switch";
import { Select } from "../ui/Select";
import { useAuth } from "../../hooks/useAuth";
import { apiClient } from "../../services/api/client";

interface Session {
  id: number;
  ip_address: string;
  user_agent: string;
  device_info: {
    browser: string;
    os: string;
    is_mobile: boolean;
  };
  location?: string;
  last_activity: string;
  created_at: string;
  is_current: boolean;
  is_trusted: boolean;
}

interface SessionConfig {
  session_timeout_minutes: number;
  remember_me_duration_days: number;
  max_concurrent_sessions: number;
  require_mfa_for_new_device: boolean;
}

export const SessionManager: React.FC = () => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [config, setConfig] = useState<SessionConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [showRevokeModal, setShowRevokeModal] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);

  useEffect(() => {
    fetchSessions();
    fetchConfig();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await apiClient.get("/api/v1/sessions");
      setSessions(response.data);
    } catch (err: any) {
      setError("セッション情報の取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await apiClient.get("/api/v1/sessions/config");
      setConfig(response.data);
    } catch (err: any) {
      console.error("Failed to fetch session config:", err);
    }
  };

  const revokeSession = async (sessionId: number) => {
    try {
      await apiClient.delete(`/api/v1/sessions/${sessionId}`);
      setSessions(sessions.filter((s) => s.id !== sessionId));
      setShowRevokeModal(false);
      setSelectedSession(null);
    } catch (err: any) {
      setError("セッションの無効化に失敗しました");
    }
  };

  const revokeAllOtherSessions = async () => {
    try {
      await apiClient.post("/api/v1/sessions/revoke-all");
      fetchSessions();
    } catch (err: any) {
      setError("セッションの無効化に失敗しました");
    }
  };

  const updateConfig = async (newConfig: SessionConfig) => {
    setSavingConfig(true);
    try {
      await apiClient.put("/api/v1/sessions/config", newConfig);
      setConfig(newConfig);
    } catch (err: any) {
      setError("設定の更新に失敗しました");
    } finally {
      setSavingConfig(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("ja-JP");
  };

  const getDeviceIcon = (deviceInfo: Session["device_info"]) => {
    if (deviceInfo.is_mobile) {
      return "📱";
    }
    return "💻";
  };

  const columns = [
    {
      key: "device",
      label: "デバイス",
      render: (session: Session) => (
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getDeviceIcon(session.device_info)}</span>
          <div>
            <p className="font-medium">
              {session.device_info.browser} on {session.device_info.os}
            </p>
            <p className="text-sm text-gray-500">{session.ip_address}</p>
            {session.location && (
              <p className="text-sm text-gray-500">{session.location}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      label: "ステータス",
      render: (session: Session) => (
        <div className="space-y-1">
          {session.is_current && (
            <Badge variant="success">現在のセッション</Badge>
          )}
          {session.is_trusted && <Badge variant="info">信頼済み</Badge>}
        </div>
      ),
    },
    {
      key: "activity",
      label: "アクティビティ",
      render: (session: Session) => (
        <div>
          <p className="text-sm">最終アクティビティ:</p>
          <p className="text-sm text-gray-600">
            {formatDate(session.last_activity)}
          </p>
          <p className="text-sm mt-1">ログイン日時:</p>
          <p className="text-sm text-gray-600">
            {formatDate(session.created_at)}
          </p>
        </div>
      ),
    },
    {
      key: "actions",
      label: "アクション",
      render: (session: Session) => (
        <Button
          variant="outline"
          size="small"
          onClick={() => {
            setSelectedSession(session);
            setShowRevokeModal(true);
          }}
          disabled={session.is_current}
        >
          無効化
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">アクティブなセッション</h3>
          <Button
            variant="outline"
            onClick={revokeAllOtherSessions}
            disabled={sessions.filter((s) => !s.is_current).length === 0}
          >
            他のすべてのセッションを無効化
          </Button>
        </div>

        {error && <Alert type="error" message={error} className="mb-4" />}

        <DataTable data={sessions} columns={columns} keyField="id" />
      </Card>

      {config && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">セッション設定</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                セッションタイムアウト
              </label>
              <Select
                value={config.session_timeout_minutes.toString()}
                onChange={(value) =>
                  updateConfig({
                    ...config,
                    session_timeout_minutes: parseInt(value),
                  })
                }
                disabled={savingConfig}
              >
                <option value="60">1時間</option>
                <option value="240">4時間</option>
                <option value="480">8時間</option>
                <option value="720">12時間</option>
                <option value="1440">24時間</option>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ログイン状態の保持期間
              </label>
              <Select
                value={config.remember_me_duration_days.toString()}
                onChange={(value) =>
                  updateConfig({
                    ...config,
                    remember_me_duration_days: parseInt(value),
                  })
                }
                disabled={savingConfig}
              >
                <option value="7">7日間</option>
                <option value="14">14日間</option>
                <option value="30">30日間</option>
                <option value="90">90日間</option>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最大同時セッション数
              </label>
              <Select
                value={config.max_concurrent_sessions.toString()}
                onChange={(value) =>
                  updateConfig({
                    ...config,
                    max_concurrent_sessions: parseInt(value),
                  })
                }
                disabled={savingConfig}
              >
                <option value="3">3</option>
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="0">無制限</option>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">
                  新しいデバイスからのログインにMFAを要求
                </p>
                <p className="text-sm text-gray-500">
                  未知のデバイスからログインする際に2段階認証を要求します
                </p>
              </div>
              <Switch
                checked={config.require_mfa_for_new_device}
                onChange={(checked) =>
                  updateConfig({
                    ...config,
                    require_mfa_for_new_device: checked,
                  })
                }
                disabled={savingConfig}
              />
            </div>
          </div>
        </Card>
      )}

      <Modal
        isOpen={showRevokeModal}
        onClose={() => {
          setShowRevokeModal(false);
          setSelectedSession(null);
        }}
        title="セッションを無効化"
      >
        <p className="text-gray-600 mb-4">
          このセッションを無効化すると、そのデバイスからは再度ログインが必要になります。
        </p>
        <div className="flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={() => {
              setShowRevokeModal(false);
              setSelectedSession(null);
            }}
          >
            キャンセル
          </Button>
          <Button
            variant="primary"
            onClick={() => selectedSession && revokeSession(selectedSession.id)}
          >
            無効化
          </Button>
        </div>
      </Modal>
    </div>
  );
};
