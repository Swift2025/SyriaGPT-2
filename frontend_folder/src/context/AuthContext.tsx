// src/context/AuthContext.tsx (الكود الكامل والنهائي)
'use client';

import React, { createContext, useState, useEffect, useContext } from 'react';
import { getCurrentUser } from '../../services/api';

interface LoginData {
  user: object;
  access: string; // <-- تم التصحيح من access_token
  refresh?: string; // <-- تم التصحيح من refresh_token
}

interface AuthContextType {
  user: object | null;
  login: (data: LoginData) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<object | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkUser = async () => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error("Failed to auto-login with existing token:", error);
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    checkUser();
  }, []);

  const login = (loginData: LoginData) => {
    // --- هذا هو التعديل الحاسم ---
    // استخدم 'access' و 'refresh' لتتطابق مع استجابة الواجهة الخلفية
    if (loginData.access) {
      localStorage.setItem('accessToken', loginData.access);
    }
    if (loginData.refresh) {
      localStorage.setItem('refreshToken', loginData.refresh);
    }
    // -----------------------------
    setUser(loginData.user);
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setUser(null);
    window.location.href = '/login'; 
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};