/**
 * プロジェクトメンバー一覧コンポーネント
 */

import React, { useState } from "react";
import {
  ProjectMember,
  ProjectMemberCreate,
} from "../../services/projectManagement";
import { projectManagementService } from "../../services/projectManagementExtended";
import {
  UserPlusIcon,
  TrashIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

interface ProjectMemberListProps {
  projectId: number;
  members: ProjectMember[];
  onUpdate: () => void;
}

export const ProjectMemberList: React.FC<ProjectMemberListProps> = ({
  projectId,
  members,
  onUpdate,
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingMemberId, setEditingMemberId] = useState<number | null>(null);
  const [newMember, setNewMember] = useState<ProjectMemberCreate>({
    projectId,
    userId: 0,
    role: "member",
    allocationPercentage: 100,
  });
  const [editingMember, setEditingMember] = useState<Partial<ProjectMember>>(
    {},
  );

  const handleAddMember = async () => {
    try {
      await projectManagementService.members.add(newMember);
      setShowAddForm(false);
      setNewMember({
        projectId,
        userId: 0,
        role: "member",
        allocationPercentage: 100,
      });
      onUpdate();
    } catch (err) {
      // console.error('Failed to add member:', err);
      alert("メンバーの追加に失敗しました");
    }
  };

  const handleUpdateMember = async (memberId: number) => {
    try {
      await projectManagementService.members.update(memberId, {
        role: editingMember.role,
        allocationPercentage: editingMember.allocationPercentage,
      });
      setEditingMemberId(null);
      setEditingMember({});
      onUpdate();
    } catch (err) {
      // console.error('Failed to update member:', err);
      alert("メンバー情報の更新に失敗しました");
    }
  };

  const handleRemoveMember = async (memberId: number) => {
    if (
      !window.confirm(
        "このメンバーをプロジェクトから削除してもよろしいですか？",
      )
    ) {
      return;
    }

    try {
      await projectManagementService.members.remove(memberId);
      onUpdate();
    } catch (err) {
      // console.error('Failed to remove member:', err);
      alert("メンバーの削除に失敗しました");
    }
  };

  const getRoleLabel = (role: string): string => {
    const labels: Record<string, string> = {
      manager: "マネージャー",
      leader: "リーダー",
      member: "メンバー",
      observer: "オブザーバー",
    };
    return labels[role] || role;
  };

  const getRoleColor = (role: string): string => {
    const colors: Record<string, string> = {
      manager: "bg-purple-100 text-purple-800",
      leader: "bg-blue-100 text-blue-800",
      member: "bg-green-100 text-green-800",
      observer: "bg-gray-100 text-gray-800",
    };
    return colors[role] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">メンバー一覧</h3>
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center px-3 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700"
          >
            <UserPlusIcon className="h-4 w-4 mr-2" />
            メンバーを追加
          </button>
        </div>

        {/* メンバー追加フォーム */}
        {showAddForm && (
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">
                  ユーザーID
                </label>
                <input
                  type="number"
                  value={newMember.userId}
                  onChange={(e) =>
                    setNewMember({
                      ...newMember,
                      userId: parseInt(e.target.value),
                    })
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="ユーザーIDを入力"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  役割
                </label>
                <select
                  value={newMember.role}
                  onChange={(e) =>
                    setNewMember({ ...newMember, role: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="manager">マネージャー</option>
                  <option value="leader">リーダー</option>
                  <option value="member">メンバー</option>
                  <option value="observer">オブザーバー</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  稼働率 (%)
                </label>
                <input
                  type="number"
                  value={newMember.allocationPercentage}
                  onChange={(e) =>
                    setNewMember({
                      ...newMember,
                      allocationPercentage: parseInt(e.target.value),
                    })
                  }
                  min="0"
                  max="100"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                キャンセル
              </button>
              <button
                onClick={handleAddMember}
                className="px-3 py-2 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
              >
                追加
              </button>
            </div>
          </div>
        )}

        {/* メンバーリスト */}
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  メンバー
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  役割
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  稼働率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  参加日
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {members.map((member) => (
                <tr key={member.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            {member.userName?.charAt(0) || "U"}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {member.userName || `User ${member.userId}`}
                        </div>
                        <div className="text-sm text-gray-500">
                          {member.userEmail ||
                            `user${member.userId}@example.com`}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingMemberId === member.id ? (
                      <select
                        value={editingMember.role || member.role}
                        onChange={(e) =>
                          setEditingMember({
                            ...editingMember,
                            role: e.target.value,
                          })
                        }
                        className="text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                      >
                        <option value="manager">マネージャー</option>
                        <option value="leader">リーダー</option>
                        <option value="member">メンバー</option>
                        <option value="observer">オブザーバー</option>
                      </select>
                    ) : (
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleColor(member.role)}`}
                      >
                        {getRoleLabel(member.role)}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingMemberId === member.id ? (
                      <input
                        type="number"
                        value={
                          editingMember.allocationPercentage ??
                          member.allocationPercentage
                        }
                        onChange={(e) =>
                          setEditingMember({
                            ...editingMember,
                            allocationPercentage: parseInt(e.target.value),
                          })
                        }
                        min="0"
                        max="100"
                        className="w-20 text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                      />
                    ) : (
                      `${member.allocationPercentage}%`
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(member.joinedAt).toLocaleDateString("ja-JP")}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {editingMemberId === member.id ? (
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => handleUpdateMember(member.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          <CheckIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => {
                            setEditingMemberId(null);
                            setEditingMember({});
                          }}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          <XMarkIcon className="h-5 w-5" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => {
                            setEditingMemberId(member.id);
                            setEditingMember({
                              role: member.role,
                              allocationPercentage: member.allocationPercentage,
                            });
                          }}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleRemoveMember(member.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {members.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              メンバーがいません
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectMemberList;
