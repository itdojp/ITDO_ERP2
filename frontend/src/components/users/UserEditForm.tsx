import React, { useState } from "react";

interface UserEditFormProps {
  user?: {
    id: string;
    email: string;
    username: string;
    fullName: string;
  };
  onSubmit: (data: any) => void;
}

export const UserEditForm: React.FC<UserEditFormProps> = ({
  user,
  onSubmit,
}) => {
  const [email, setEmail] = useState(user?.email || "");
  const [username, setUsername] = useState(user?.username || "");
  const [fullName, setFullName] = useState(user?.fullName || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ email, username, fullName });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">メールアドレス</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium">ユーザー名</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium">氏名</label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300"
        />
      </div>
      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
      >
        保存
      </button>
    </form>
  );
};

export default UserEditForm;
