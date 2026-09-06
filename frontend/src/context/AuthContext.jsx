import { createContext, useState, useEffect, useContext } from 'react';
import { apiClient } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      
      try {
        const userData = await apiClient('/api/v1/auth/me');
        setUser(userData);
      } catch (error) {
        // Clear token if it's invalid/expired (e.g., 401)
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, [token]);

  const login = async (email, password) => {
    setAuthError(null);
    try {
      const data = await apiClient('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      
      if (data.access_token) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        // User data will be loaded by the useEffect hook since token changed
      }
      return { success: true };
    } catch (error) {
      const message = error.data?.detail || 'Login failed';
      setAuthError(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    authError,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
