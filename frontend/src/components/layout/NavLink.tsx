import React from 'react';

interface NavLinkProps {
  icon: string;
  label: string;
  path: string;
  showLabel: boolean;
  isActive?: boolean;
}

export const NavLink: React.FC<NavLinkProps> = ({ icon, label, path, showLabel, isActive = false }) => {
  return (
    <a
      href={path}
      className={`flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors ${
        isActive ? 'bg-gray-800 text-white' : ''
      }`}
    >
      <span className="text-xl">{icon}</span>
      {showLabel && (
        <span className="ml-3 text-sm font-medium">{label}</span>
      )}
    </a>
  );
};