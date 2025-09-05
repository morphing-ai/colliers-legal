// frontend/src/context/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth, useUser } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  userId: string | null;
  userEmail: string | null;
  refreshToken: () => Promise<string | null>;
  getTokenRemainingTime: () => number;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  isLoading: true,
  userId: null,
  userEmail: null,
  refreshToken: async () => null,
  getTokenRemainingTime: () => 0,
});

export const useAuthContext = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const { getToken, isSignedIn, isLoaded } = useAuth();
  const { user } = useUser();
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [tokenExpiryTime, setTokenExpiryTime] = useState<number | null>(null);

  const getTokenRemainingTime = useCallback(() => {
    if (!tokenExpiryTime) return 0;
    return Math.max(0, tokenExpiryTime - Date.now());
  }, [tokenExpiryTime]);

  const refreshToken = useCallback(async () => {
    if (isLoaded && isSignedIn) {
      try {
        // Check if token is still valid for more than 5 minutes
        if (token && tokenExpiryTime && Date.now() < tokenExpiryTime - 5 * 60 * 1000) {
          // Token is still valid for more than 5 minutes, return current token
          return token;
        }
        
        console.log("[Auth] Token needs refreshing, fetching new token");
        
        try {
          const fetchedToken = await getToken();
          
          if (!fetchedToken) {
            throw new Error("Failed to retrieve token");
          }
          
          setToken(fetchedToken);
          
          // Token typically lasts 1 hour, set expiry accordingly
          const newExpiryTime = Date.now() + 55 * 60 * 1000; // 55 minutes
          setTokenExpiryTime(newExpiryTime);
          
          console.log("[Auth] Token refreshed successfully, expires in 55 minutes");
          return fetchedToken;
        } catch (error) {
          console.error("[Auth] Error getting token:", error);
          setToken(null);
          setTokenExpiryTime(null);
          return null;
        }
      } catch (error) {
        console.error("[Auth] Error in refreshToken:", error);
        
        // Clear token data on error
        setToken(null);
        setTokenExpiryTime(null);
        return null;
      }
    }
    return null;
  }, [getToken, isSignedIn, isLoaded, token, tokenExpiryTime]);

  useEffect(() => {
    const fetchToken = async () => {
      if (isLoaded) {
        try {
          if (isSignedIn) {
            await refreshToken();
          } else {
            setToken(null);
            setTokenExpiryTime(null);
          }
        } catch (error) {
          console.error("[Auth] Error fetching token:", error);
          setToken(null);
          setTokenExpiryTime(null);
        } finally {
          setIsLoading(false);
        }
      }
    };

    fetchToken();
  }, [refreshToken, isSignedIn, isLoaded]);

  // Set up a timer to refresh the token before it expires
  useEffect(() => {
    if (!tokenExpiryTime || !isSignedIn) return;
    
    const timeUntilRefresh = tokenExpiryTime - Date.now() - (5 * 60 * 1000); // Refresh 5 minutes before expiry
    
    if (timeUntilRefresh <= 0) {
      // Token is about to expire or has expired, refresh immediately
      refreshToken();
      return;
    }
    
    console.log(`[Auth] Token refresh scheduled in ${Math.round(timeUntilRefresh/60000)} minutes`);
    
    const refreshTimer = setTimeout(() => {
      console.log('[Auth] Auto-refreshing token before expiry');
      refreshToken();
    }, timeUntilRefresh);
    
    return () => clearTimeout(refreshTimer);
  }, [tokenExpiryTime, refreshToken, isSignedIn]);

  // Removed the global window function entirely

  const value = {
    token,
    isAuthenticated: !!token,
    isLoading,
    userId: user?.id || null,
    userEmail: user?.primaryEmailAddress?.emailAddress || null,
    refreshToken,
    getTokenRemainingTime,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};