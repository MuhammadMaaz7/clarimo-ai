import { createContext, useContext, useState, useEffect, ReactNode, useMemo } from 'react';
import { api, ApiError } from '../lib/api';
import { getTokenManager, SessionState } from '../services/TokenManager';
import { getActivityDetector } from '../services/ActivityDetector';
import { getBackgroundTaskMonitor } from '../services/BackgroundTaskMonitor';
import SessionWarning, { useSessionWarning } from '../components/SessionWarning';

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  checkTokenValidity: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const sessionWarning = useSessionWarning();

  const logout = () => {
    // Use TokenManager for proper cleanup
    const tokenManager = getTokenManager();
    tokenManager.clearToken();
    
    // Stop activity monitoring
    const activityDetector = getActivityDetector();
    activityDetector.stopMonitoring();
    
    // Cancel background tasks
    const taskMonitor = getBackgroundTaskMonitor();
    taskMonitor.cancelAllTasks();
    
    setUser(null);
  };

  // Handle session warning actions
  const handleStayLoggedIn = async () => {
    const tokenManager = getTokenManager();
    tokenManager.extendSession();
    sessionWarning.hideWarning();
  };

  const handleLogoutFromWarning = () => {
    logout();
    sessionWarning.hideWarning();
  };

  const handleAutoLogout = () => {
    console.log('Auto logout triggered from session warning');
    logout();
  };

  useEffect(() => {
    // Initialize smart token management
    const tokenManager = getTokenManager();
    const activityDetector = getActivityDetector();
    const taskMonitor = getBackgroundTaskMonitor();

    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      console.log('Checking auth on app load, token exists:', !!token);
      
      if (token) {
        try {
          const userData = await api.auth.me();
          console.log('Auth check successful, user:', userData);
          setUser(userData);
          
          // Start smart token management
          activityDetector.startMonitoring();
        } catch (error) {
          console.log('Auth check failed:', error);
          if (error instanceof ApiError && error.isTokenExpired) {
            console.log('Token expired, user will be redirected to login');
          }
          setUser(null);
          tokenManager.clearToken();
        }
      } else {
        console.log('No token found in localStorage');
      }
      setLoading(false);
    };

    // Listen for token expiration events from TokenManager
    const handleTokenExpired = () => {
      console.log('Token expired event received from TokenManager');
      setUser(null);
      setLoading(false);
      
      // Stop activity monitoring
      activityDetector.stopMonitoring();
      
      // Clear any background tasks
      taskMonitor.cancelAllTasks();
    };

    // Listen for session state changes
    const handleSessionStateChanged = (newState: SessionState) => {
      console.log('Session state changed:', newState);
      
      if (newState === SessionState.WARNING) {
        sessionWarning.showWarning(2); // Show 2-minute warning
      } else if (newState === SessionState.ACTIVE) {
        sessionWarning.hideWarning();
      } else if (newState === SessionState.EXPIRED) {
        sessionWarning.hideWarning();
        setUser(null);
      }
    };



    // Set up event listeners
    tokenManager.onTokenExpired(handleTokenExpired);
    tokenManager.onSessionStateChanged(handleSessionStateChanged);
    
    // Legacy support for existing token expiration events
    globalThis.addEventListener('auth:token-expired', handleTokenExpired);
    
    checkAuth();

    return () => {
      globalThis.removeEventListener('auth:token-expired', handleTokenExpired);
      
      // Clean up token manager
      tokenManager.destroy();
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const data = await api.auth.login(email, password);
      localStorage.setItem('auth_token', data.access_token);
      setUser(data.user);
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.message);
      }
      throw new Error('Login failed');
    }
  };

  const signup = async (email: string, password: string, fullName: string) => {
    try {
      const data = await api.auth.signup(email, password, fullName);
      localStorage.setItem('auth_token', data.access_token);
      setUser(data.user);
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.message);
      }
      throw new Error('Signup failed');
    }
  };

  const checkTokenValidity = async (): Promise<boolean> => {
    const tokenManager = getTokenManager();
    return await tokenManager.validateToken();
  };

  const contextValue = useMemo(() => ({
    user,
    loading,
    login,
    signup,
    logout,
    checkTokenValidity
  }), [user, loading]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
      <SessionWarning
        isVisible={sessionWarning.isVisible}
        timeRemainingMinutes={sessionWarning.timeRemaining}
        onStayLoggedIn={handleStayLoggedIn}
        onLogout={handleLogoutFromWarning}
        onAutoLogout={handleAutoLogout}
      />
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
