import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Alert } from "../ui/Alert";
import { Card } from "../ui/Card";
import { Form } from "../ui/Form";
import { Tabs } from "../ui/Tabs";
import { useAuth } from "../../hooks/useAuth";

interface SetupData {
  qr_code: string;
  secret: string;
  backup_codes: string[];
}

export const MFASetup: React.FC = () => {
  const navigate = useNavigate();
  const { setupMFA, verifyMFASetup } = useAuth();
  const [step, setStep] = useState<"setup" | "verify" | "backup">("setup");
  const [setupData, setSetupData] = useState<SetupData | null>(null);
  const [verificationCode, setVerificationCode] = useState("");
  const [deviceName, setDeviceName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [downloadedCodes, setDownloadedCodes] = useState(false);

  useEffect(() => {
    const initSetup = async () => {
      try {
        const data = await setupMFA("totp");
        setSetupData(data);
      } catch (err: any) {
        setError(err.message || "セットアップの初期化に失敗しました");
      }
    };

    initSetup();
  }, [setupMFA]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await verifyMFASetup(verificationCode, deviceName || "My Device");
      setStep("backup");
    } catch (err: any) {
      setError(err.message || "認証に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const handleCopySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

  const handleDownloadCodes = () => {
    if (setupData?.backup_codes) {
      const content = `ITDO ERP バックアップコード
生成日: ${new Date().toLocaleString("ja-JP")}

以下のバックアップコードは、認証アプリにアクセスできない場合に使用できます。
各コードは一度だけ使用できます。安全な場所に保管してください。

${setupData.backup_codes.join("\n")}

重要: このファイルは安全な場所に保管し、他の人と共有しないでください。`;

      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `itdo-erp-backup-codes-${Date.now()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      setDownloadedCodes(true);
    }
  };

  const handleComplete = () => {
    if (!downloadedCodes) {
      setError("続行する前にバックアップコードをダウンロードしてください");
      return;
    }
    navigate("/dashboard");
  };

  if (step === "setup") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              2段階認証の設定
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              アカウントのセキュリティを強化します
            </p>
          </div>
          <Card>
            <Tabs
              tabs={[
                { id: "app", label: "認証アプリ" },
                { id: "manual", label: "手動設定" },
              ]}
              defaultTab="app"
            >
              <div id="app" className="space-y-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-4">
                    認証アプリでQRコードをスキャンしてください
                  </p>
                  {setupData?.qr_code && (
                    <div className="inline-block p-4 bg-white border-2 border-gray-300 rounded-lg">
                      <img
                        src={setupData.qr_code}
                        alt="QR Code"
                        className="w-48 h-48"
                      />
                    </div>
                  )}
                  <div className="mt-4 space-y-2">
                    <p className="text-sm font-medium text-gray-700">
                      推奨認証アプリ:
                    </p>
                    <ul className="text-sm text-gray-600">
                      <li>• Google Authenticator</li>
                      <li>• Microsoft Authenticator</li>
                      <li>• Authy</li>
                    </ul>
                  </div>
                </div>
                <Button
                  onClick={() => setStep("verify")}
                  variant="primary"
                  className="w-full"
                >
                  次へ: コードを確認
                </Button>
              </div>

              <div id="manual" className="space-y-6">
                <div>
                  <p className="text-sm text-gray-600 mb-4">
                    QRコードをスキャンできない場合は、以下のキーを認証アプリに手動で入力してください
                  </p>
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <code className="text-sm font-mono break-all">
                        {setupData?.secret || "読み込み中..."}
                      </code>
                      <Button
                        onClick={handleCopySecret}
                        variant="outline"
                        size="small"
                        className="ml-2 flex-shrink-0"
                      >
                        {copiedSecret ? "コピー済み" : "コピー"}
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    <p>設定タイプ: 時間ベース (TOTP)</p>
                    <p>期間: 30秒</p>
                  </div>
                </div>
                <Button
                  onClick={() => setStep("verify")}
                  variant="primary"
                  className="w-full"
                >
                  次へ: コードを確認
                </Button>
              </div>
            </Tabs>
          </Card>
        </div>
      </div>
    );
  }

  if (step === "verify") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              認証コードを確認
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              認証アプリに表示される6桁のコードを入力してください
            </p>
          </div>
          <Card>
            <Form onSubmit={handleVerify} className="space-y-6">
              {error && <Alert type="error" message={error} />}

              <div>
                <label
                  htmlFor="deviceName"
                  className="block text-sm font-medium text-gray-700"
                >
                  デバイス名（任意）
                </label>
                <Input
                  id="deviceName"
                  name="deviceName"
                  type="text"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  className="mt-1"
                  placeholder="例: iPhone, 会社PC"
                />
              </div>

              <div>
                <label
                  htmlFor="code"
                  className="block text-sm font-medium text-gray-700"
                >
                  認証コード
                </label>
                <Input
                  id="code"
                  name="code"
                  type="text"
                  required
                  value={verificationCode}
                  onChange={(e) =>
                    setVerificationCode(e.target.value.replace(/\D/g, ""))
                  }
                  className="mt-1 text-center text-2xl tracking-widest"
                  placeholder="000000"
                  maxLength={6}
                  pattern="[0-9]{6}"
                />
              </div>

              <div className="flex space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep("setup")}
                  className="flex-1"
                >
                  戻る
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  disabled={loading || verificationCode.length !== 6}
                >
                  {loading ? "確認中..." : "確認"}
                </Button>
              </div>
            </Form>
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
            バックアップコード
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            認証アプリにアクセスできない場合の緊急用コードです
          </p>
        </div>
        <Card>
          <div className="space-y-6">
            {error && <Alert type="error" message={error} />}

            <Alert
              type="warning"
              message="これらのコードは一度だけ表示されます。必ずダウンロードして安全な場所に保管してください。"
            />

            <div className="bg-gray-100 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-2">
                {setupData?.backup_codes.map((code, index) => (
                  <code key={index} className="text-sm font-mono">
                    {code}
                  </code>
                ))}
              </div>
            </div>

            <Button
              onClick={handleDownloadCodes}
              variant="outline"
              className="w-full"
            >
              バックアップコードをダウンロード
              {downloadedCodes && " ✓"}
            </Button>

            <Button
              onClick={handleComplete}
              variant="primary"
              className="w-full"
            >
              設定を完了
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
