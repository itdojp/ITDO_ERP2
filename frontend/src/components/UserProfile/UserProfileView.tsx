/**
 * User Profile View Component
 * Displays user profile information with privacy-aware rendering
 */

import React from "react";
import {
  User,
  Mail,
  Phone,
  MapPin,
  Globe,
  Calendar,
  Users,
  Building,
} from "lucide-react";
import {
  useUserProfile,
  useCheckProfileVisibility,
} from "../../hooks/useUserProfile";

interface UserProfileViewProps {
  userId: number;
  showEditButton?: boolean;
  onEdit?: () => void;
}

export const UserProfileView: React.FC<UserProfileViewProps> = ({
  userId,
  showEditButton = false,
  onEdit,
}) => {
  const { data: user, isLoading, error } = useUserProfile(userId);
  const { data: profileVisibility } = useCheckProfileVisibility(userId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">プロフィールの読み込みに失敗しました。</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-600">ユーザーが見つかりません。</p>
      </div>
    );
  }

  if (profileVisibility && !profileVisibility.visible) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-700">
          このプロフィールは非公開に設定されています。
          {profileVisibility.reason && ` (${profileVisibility.reason})`}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">プロフィール</h2>
          {showEditButton && (
            <button
              onClick={onEdit}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              編集
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {/* Profile Image and Basic Info */}
        <div className="flex items-start space-x-6 mb-6">
          <div className="flex-shrink-0">
            {user.profile_image_url ? (
              <img
                src={user.profile_image_url}
                alt={user.full_name}
                className="w-20 h-20 rounded-full object-cover"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center">
                <User className="w-8 h-8 text-gray-400" />
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="text-2xl font-bold text-gray-900 mb-1">
              {user.full_name}
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
              <div className="flex items-center">
                <Mail className="w-4 h-4 mr-1" />
                {user.email}
              </div>
              {user.phone && (
                <div className="flex items-center">
                  <Phone className="w-4 h-4 mr-1" />
                  {user.phone}
                </div>
              )}
            </div>

            {user.bio && (
              <p className="text-gray-700 text-sm leading-relaxed">
                {user.bio}
              </p>
            )}
          </div>
        </div>

        {/* Additional Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Contact Information */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">連絡先</h4>
            <div className="space-y-2">
              {user.location && (
                <div className="flex items-center text-sm text-gray-600">
                  <MapPin className="w-4 h-4 mr-2" />
                  {user.location}
                </div>
              )}
              {user.website && (
                <div className="flex items-center text-sm text-gray-600">
                  <Globe className="w-4 h-4 mr-2" />
                  <a
                    href={user.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {user.website}
                  </a>
                </div>
              )}
              {user.last_login_at && (
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="w-4 h-4 mr-2" />
                  最終ログイン:{" "}
                  {new Date(user.last_login_at).toLocaleDateString("ja-JP")}
                </div>
              )}
            </div>
          </div>

          {/* Organization & Roles */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              組織・役職
            </h4>
            <div className="space-y-3">
              {user.organizations.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-1">
                    所属組織
                  </h5>
                  <div className="space-y-1">
                    {user.organizations.map((org) => (
                      <div
                        key={org.id}
                        className="flex items-center text-sm text-gray-600"
                      >
                        <Building className="w-4 h-4 mr-2" />
                        {org.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {user.departments.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-1">
                    所属部門
                  </h5>
                  <div className="space-y-1">
                    {user.departments.map((dept) => (
                      <div
                        key={dept.id}
                        className="flex items-center text-sm text-gray-600"
                      >
                        <Users className="w-4 h-4 mr-2" />
                        {dept.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {user.roles.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-1">
                    役職
                  </h5>
                  <div className="space-y-1">
                    {user.roles.map((userRole, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        <span className="font-medium">
                          {userRole.role.name}
                        </span>
                        {userRole.organization && (
                          <span className="text-gray-500 ml-1">
                            @ {userRole.organization.name}
                          </span>
                        )}
                        {userRole.department && (
                          <span className="text-gray-500 ml-1">
                            ({userRole.department.name})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Account Status */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${
                    user.is_active ? "bg-green-400" : "bg-red-400"
                  }`}
                />
                <span
                  className={user.is_active ? "text-green-600" : "text-red-600"}
                >
                  {user.is_active ? "アクティブ" : "無効"}
                </span>
              </div>
            </div>
            <div className="text-gray-500">
              作成日: {new Date(user.created_at).toLocaleDateString("ja-JP")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfileView;
