import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const adminToken = sessionStorage.getItem('medibridge_admin_token');
    const userToken = sessionStorage.getItem('medibridge_token');
    if (!adminToken && !userToken) { setReady(true); return; }
    const restore = adminToken ? api.adminMe() : api.me();
    restore.then(({ user: current }) => setUser(current)).catch(() => {
      sessionStorage.removeItem(adminToken ? 'medibridge_admin_token' : 'medibridge_token');
    }).finally(() => setReady(true));
  }, []);
  const authenticate = async (operation, values) => {
    const result = await api[operation](values);
    const tokenKey = operation === 'adminLogin' ? 'medibridge_admin_token' : 'medibridge_token';
    sessionStorage.removeItem(operation === 'adminLogin' ? 'medibridge_token' : 'medibridge_admin_token');
    sessionStorage.setItem(tokenKey, result.token);
    setUser(result.user);
    return result.user;
  };
  const logout = async () => {
    try { await api.logout(); } finally { sessionStorage.removeItem('medibridge_token'); sessionStorage.removeItem('medibridge_admin_token'); setUser(null); }
  };
  const updateLanguage = (language) => setUser((current) => current ? { ...current, language } : current);
  return <AuthContext.Provider value={{ user, ready, authenticate, logout, updateLanguage }}>{children}</AuthContext.Provider>;
}

export function useAuth() { return useContext(AuthContext); }
