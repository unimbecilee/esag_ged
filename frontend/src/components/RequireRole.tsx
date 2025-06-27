import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

interface RequireRoleProps {
  roles: string[];
  children: React.ReactNode;
}

const RequireRole: React.FC<RequireRoleProps> = ({ roles, children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user || !roles.includes(user.role.toLowerCase())) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
};

export default RequireRole; 

