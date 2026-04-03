import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem('snow_session');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (session) {
      localStorage.setItem('snow_session', JSON.stringify(session));
    } else {
      localStorage.removeItem('snow_session');
    }
  }, [session]);

  const login = (sessionData) => {
    setSession(sessionData);
    navigate('/dashboard');
  };

  const logout = () => {
    setSession(null);
    navigate('/login');
  };

  const updateSessionData = (newData) => {
    setSession(prev => ({ ...prev, ...newData }));
  };

  return (
    <AuthContext.Provider value={{ session, setSession: login, logout, loading, setLoading, updateSessionData }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
