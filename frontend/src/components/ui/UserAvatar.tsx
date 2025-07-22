import React from 'react';

interface UserAvatarProps {
  name: string;
  imageUrl?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  status?: 'online' | 'offline' | 'away' | 'busy';
}

export const UserAvatar: React.FC<UserAvatarProps> = ({
  name,
  imageUrl,
  size = 'md',
  status
}) => {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-lg'
  };

  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-gray-400',
    away: 'bg-yellow-500',
    busy: 'bg-red-500'
  };

  const initials = name.split(' ').map(n => n[0]).join('').toUpperCase();

  return (
    <div className="relative inline-block">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={name}
          className={`rounded-full object-cover ${sizeClasses[size]}`}
        />
      ) : (
        <div
          className={`rounded-full bg-blue-500 text-white flex items-center justify-center font-semibold ${sizeClasses[size]}`}
        >
          {initials}
        </div>
      )}
      {status && (
        <span
          className={`absolute bottom-0 right-0 block rounded-full ring-2 ring-white ${
            size === 'sm' ? 'w-2 h-2' : size === 'xl' ? 'w-4 h-4' : 'w-3 h-3'
          } ${statusColors[status]}`}
        />
      )}
    </div>
  );
};

export default UserAvatar;