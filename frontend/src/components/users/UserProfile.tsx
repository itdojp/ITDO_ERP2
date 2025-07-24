import React, { useState } from "react";

interface UserProfileProps {
  userId?: string;
}

interface ProfileData {
  id: string;
  username: string;
  email: string;
  fullName: string;
  role: string;
  department: string;
  avatar?: string;
  phone?: string;
  address?: string;
  bio?: string;
  joinedDate: string;
  lastLogin: string;
  preferences: {
    theme: "light" | "dark" | "auto";
    language: string;
    notifications: {
      email: boolean;
      push: boolean;
      sms: boolean;
    };
    privacy: {
      profileVisible: boolean;
      activityVisible: boolean;
    };
  };
  stats: {
    totalLogins: number;
    tasksCompleted: number;
    documentsCreated: number;
    lastActiveHours: number;
  };
}

const mockProfileData: ProfileData = {
  id: "1",
  username: "yamada.taro",
  email: "yamada@example.com",
  fullName: "山田太郎",
  role: "管理者",
  department: "システム部",
  phone: "090-1234-5678",
  address: "東京都渋谷区",
  bio: "システム管理とプロジェクト管理を担当しています。効率的なワークフローの構築に興味があります。",
  joinedDate: "2024-01-15",
  lastLogin: "2024-07-22T14:30:00Z",
  preferences: {
    theme: "light",
    language: "ja",
    notifications: {
      email: true,
      push: true,
      sms: false,
    },
    privacy: {
      profileVisible: true,
      activityVisible: false,
    },
  },
  stats: {
    totalLogins: 342,
    tasksCompleted: 128,
    documentsCreated: 45,
    lastActiveHours: 2,
  },
};

export const UserProfile: React.FC<UserProfileProps> = ({ userId }) => {
  const [activeTab, setActiveTab] = useState<
    "profile" | "preferences" | "security" | "stats"
  >("profile");
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState(mockProfileData);

  const tabs = [
    { key: "profile", label: "プロフィール", icon: "👤" },
    { key: "preferences", label: "設定", icon: "⚙️" },
    { key: "security", label: "セキュリティ", icon: "🔒" },
    { key: "stats", label: "統計", icon: "📊" },
  ];

  const handleSave = () => {
    // 実際の実装では、APIを呼び出してプロフィールを更新
    setIsEditing(false);
    console.log("Profile saved:", profileData);
  };

  const handlePreferenceChange = (
    category: string,
    key: string,
    value: any,
  ) => {
    setProfileData((prev) => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [category]: {
          ...prev.preferences[category as keyof typeof prev.preferences],
          [key]: value,
        },
      },
    }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ja-JP");
  };

  const formatLastLogin = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60),
    );

    if (diffInHours < 1) return "1時間以内";
    if (diffInHours < 24) return `${diffInHours}時間前`;
    return date.toLocaleString("ja-JP");
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-20 w-20 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {profileData.fullName.charAt(0)}
              </span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {profileData.fullName}
              </h1>
              <p className="text-sm text-gray-500">
                {profileData.role} • {profileData.department}
              </p>
              <p className="text-sm text-gray-400">@{profileData.username}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            {activeTab === "profile" && (
              <button
                onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                {isEditing ? "保存" : "編集"}
              </button>
            )}
            {isEditing && (
              <button
                onClick={() => setIsEditing(false)}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
              >
                キャンセル
              </button>
            )}
          </div>
        </div>
      </div>

      {/* タブナビゲーション */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2
                ${
                  activeTab === tab.key
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }
              `}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* タブコンテンツ */}
      <div className="p-6">
        {activeTab === "profile" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  基本情報
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      氏名
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={profileData.fullName}
                        onChange={(e) =>
                          setProfileData((prev) => ({
                            ...prev,
                            fullName: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">
                        {profileData.fullName}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      メールアドレス
                    </label>
                    {isEditing ? (
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) =>
                          setProfileData((prev) => ({
                            ...prev,
                            email: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">
                        {profileData.email}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      電話番号
                    </label>
                    {isEditing ? (
                      <input
                        type="tel"
                        value={profileData.phone || ""}
                        onChange={(e) =>
                          setProfileData((prev) => ({
                            ...prev,
                            phone: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">
                        {profileData.phone || "未設定"}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      住所
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={profileData.address || ""}
                        onChange={(e) =>
                          setProfileData((prev) => ({
                            ...prev,
                            address: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">
                        {profileData.address || "未設定"}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  システム情報
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      役割
                    </label>
                    <p className="text-sm text-gray-900">{profileData.role}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      部署
                    </label>
                    <p className="text-sm text-gray-900">
                      {profileData.department}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      参加日
                    </label>
                    <p className="text-sm text-gray-900">
                      {formatDate(profileData.joinedDate)}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      最終ログイン
                    </label>
                    <p className="text-sm text-gray-900">
                      {formatLastLogin(profileData.lastLogin)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                自己紹介
              </h3>
              {isEditing ? (
                <textarea
                  value={profileData.bio || ""}
                  onChange={(e) =>
                    setProfileData((prev) => ({ ...prev, bio: e.target.value }))
                  }
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="自己紹介を入力してください..."
                />
              ) : (
                <p className="text-sm text-gray-700">
                  {profileData.bio || "自己紹介が設定されていません。"}
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === "preferences" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                表示設定
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    テーマ
                  </label>
                  <select
                    value={profileData.preferences.theme}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "preferences",
                        "theme",
                        e.target.value,
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="light">ライト</option>
                    <option value="dark">ダーク</option>
                    <option value="auto">自動</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    言語
                  </label>
                  <select
                    value={profileData.preferences.language}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "preferences",
                        "language",
                        e.target.value,
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="ja">日本語</option>
                    <option value="en">English</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                通知設定
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">メール通知</span>
                  <input
                    type="checkbox"
                    checked={profileData.preferences.notifications.email}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "notifications",
                        "email",
                        e.target.checked,
                      )
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">プッシュ通知</span>
                  <input
                    type="checkbox"
                    checked={profileData.preferences.notifications.push}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "notifications",
                        "push",
                        e.target.checked,
                      )
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">SMS通知</span>
                  <input
                    type="checkbox"
                    checked={profileData.preferences.notifications.sms}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "notifications",
                        "sms",
                        e.target.checked,
                      )
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                プライバシー設定
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">
                    プロフィールを公開
                  </span>
                  <input
                    type="checkbox"
                    checked={profileData.preferences.privacy.profileVisible}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "privacy",
                        "profileVisible",
                        e.target.checked,
                      )
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">活動履歴を公開</span>
                  <input
                    type="checkbox"
                    checked={profileData.preferences.privacy.activityVisible}
                    onChange={(e) =>
                      handlePreferenceChange(
                        "privacy",
                        "activityVisible",
                        e.target.checked,
                      )
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "security" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                パスワード変更
              </h3>
              <div className="space-y-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    現在のパスワード
                  </label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="現在のパスワードを入力"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    新しいパスワード
                  </label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="新しいパスワードを入力"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    パスワード確認
                  </label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="新しいパスワードを再入力"
                  />
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                  パスワードを変更
                </button>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                二段階認証
              </h3>
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">SMS認証</p>
                  <p className="text-sm text-gray-500">
                    ログイン時にSMSで認証コードを受信
                  </p>
                </div>
                <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm">
                  有効化
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "stats" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                利用統計
              </h3>
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {profileData.stats.totalLogins}
                  </div>
                  <div className="text-sm text-gray-600">総ログイン回数</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {profileData.stats.tasksCompleted}
                  </div>
                  <div className="text-sm text-gray-600">完了タスク数</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {profileData.stats.documentsCreated}
                  </div>
                  <div className="text-sm text-gray-600">作成文書数</div>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {profileData.stats.lastActiveHours}
                  </div>
                  <div className="text-sm text-gray-600">
                    最終活動時間（時間前）
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
