import React from 'react';

interface UserProfileProps {
  userId: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({ userId }) => {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">ユーザープロフィール</h1>
      <div className="bg-white shadow rounded-lg p-6">
        <p>ユーザーID: {userId}</p>
      </div>
    </div>
  );
};

export default UserProfile;