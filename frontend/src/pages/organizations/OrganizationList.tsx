import React from "react";

interface Organization {
  id: string;
  name: string;
  code: string;
  isActive: boolean;
}

const mockOrganizations: Organization[] = [
  { id: "1", name: "営業部", code: "SALES", isActive: true },
  { id: "2", name: "開発部", code: "DEV", isActive: true },
  { id: "3", name: "マーケティング部", code: "MKT", isActive: true },
  { id: "4", name: "人事部", code: "HR", isActive: false },
];

export const OrganizationList: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">組織管理</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          新規作成
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                組織名
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                コード
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                状態
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {mockOrganizations.map((org) => (
              <tr key={org.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {org.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                  {org.code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      org.isActive
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {org.isActive ? "有効" : "無効"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OrganizationList;
