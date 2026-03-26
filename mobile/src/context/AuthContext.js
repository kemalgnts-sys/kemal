import React, { createContext, useContext, useState, useEffect } from 'react';
import { storage } from '../services/api';
import { setLanguage as setI18nLanguage, getLanguage } from '../i18n';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguageState] = useState('en');

  useEffect(() => {
    loadUser();
    loadLanguage();
  }, []);

  const loadUser = async () => {
    try {
      const savedUser = await storage.getUser();
      if (savedUser) {
        setUser(savedUser);
      }
    } catch (e) {
      console.error('Error loading user:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadLanguage = async () => {
    try {
      const savedLang = await storage.getLanguage();
      if (savedLang) {
        setLanguageState(savedLang);
        setI18nLanguage(savedLang);
      }
    } catch (e) {
      console.error('Error loading language:', e);
    }
  };

  const login = async (userData) => {
    setUser(userData);
    await storage.setUser(userData);
  };

  const logout = async () => {
    setUser(null);
    await storage.removeUser();
  };

  const setLanguage = async (lang) => {
    setLanguageState(lang);
    setI18nLanguage(lang);
    await storage.setLanguage(lang);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      logout, 
      loading,
      language,
      setLanguage,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
