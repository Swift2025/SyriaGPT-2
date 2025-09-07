// src/context/AuthContext.tsx
'use client';

import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import { getCurrentUser, getUserProfile, getUserSettings, updateUserSettings } from '../../services/api';
import { User, UserSettings } from '../app/[lang]/types';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  login: (userData: User) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Debug: مراقبة تغييرات حالة المستخدم
  useEffect(() => {
    console.log('AuthContext - User state changed:', { user, isLoading });
  }, [user, isLoading]);

  useEffect(() => {
    const checkUser = async () => {
      // التحقق من أننا في المتصفح قبل استخدام localStorage
      if (typeof window === 'undefined') {
        setIsLoading(false);
        return;
      }
      
      const token = localStorage.getItem('accessToken');
      console.log('AuthContext - Checking user with token:', token ? 'exists' : 'none');
      if (token) {
        try {
          const currentUser = await getCurrentUser();
          console.log('AuthContext - Current user from API:', currentUser);
          setUser(currentUser);
        } catch (error) {
          console.error("AuthContext - Invalid token:", error);
          localStorage.removeItem('accessToken');
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    checkUser();
  }, []);

  const login = (userData: User) => {
    console.log('AuthContext - Login called with user data:', userData);
    setUser(userData);
    console.log('AuthContext - User state updated to:', userData);
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      setUser(null);
      window.location.reload(); // لإعادة تعيين كل شيء
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};