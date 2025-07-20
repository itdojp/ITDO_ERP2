import React from "react";

export interface StatusBadgeProps {
  status: "active" | "inactive" | "pending";
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const colors = {
    active: "bg-green-500",
    inactive: "bg-red-500",
    pending: "bg-yellow-500"
  };

  return (
    <span className={`px-2 py-1 rounded text-white ${colors[status]}`}>
      {status}
    </span>
  );
};

export default StatusBadge;