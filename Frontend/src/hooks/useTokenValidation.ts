import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Hook to periodically validate token and handle expiration
 */
export const useTokenValidation = (intervalMinutes: number = 5) => {
  const { checkTokenValidity, logout, user } = useAuth();

  useEffect(() => {
    if (!user) return;

    const validateToken = async () => {
      const isValid = await checkTokenValidity();
      if (!isValid) {
        console.log('Token validation failed, logging out user');
        logout();
      }
    };

    // Validate immediately
    validateToken();

    // Set up periodic validation
    const interval = setInterval(validateToken, intervalMinutes * 60 * 1000);

    return () => clearInterval(interval);
  }, [user, checkTokenValidity, logout, intervalMinutes]);
};

export default useTokenValidation;