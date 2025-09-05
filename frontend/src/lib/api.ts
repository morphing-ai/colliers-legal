// frontend/src/lib/api.ts
import { useAuthContext } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/useToast';
import { useCallback, useMemo } from 'react';

/**
 * Custom hook to use the API client with authentication
 */
export function useApiClient() {
  const { token, isAuthenticated, refreshToken } = useAuthContext();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Core API fetch function
  const fetchApi = useCallback(async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    // Base URL from environment or fallback
    const baseUrl = import.meta.env.VITE_API_URL || 'https://api.prettl-demo.morphing.ai';
    const url = `${baseUrl}${endpoint}`;
    const method = options.method || 'GET';
    
    // Check authentication before making request
    if (!token || !isAuthenticated) {
      console.error('[API] Authentication token is missing or invalid');
      
      // Try to refresh token
      const newToken = await refreshToken();
      
      if (!newToken) {
        toast({
          title: 'Authentication Error',
          description: 'Your session has expired. Please sign in again.',
          variant: 'destructive',
        });
        navigate('/sign-in', { replace: true });
        throw new Error('Authentication token is missing or invalid');
      }
    }

    // Ensure we have a fresh token
    await refreshToken();

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    console.log(`[API] ${method} request to ${endpoint}`);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      });
      
      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401) {
          console.log('[API] Received 401, attempting to refresh token');
          
          // Force token refresh
          const newToken = await refreshToken();
          
          if (!newToken) {
            toast({
              title: 'Authentication Error',
              description: 'Your session has expired. Please sign in again.',
              variant: 'destructive',
            });
            navigate('/sign-in', { replace: true });
            throw new Error('Authentication token expired');
          }
          
          // Retry the request with new token
          return fetchApi(endpoint, options);
        }
        
        const error = await response.json().catch(() => ({
          message: response.statusText,
        }));
        throw new Error(error.message || `API request failed with status ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('[API] Request error:', error);
      throw error;
    }
  }, [token, isAuthenticated, refreshToken, navigate, toast]);

  // Simple Hello World API call
  const getHello = useCallback(() => 
    fetchApi<{message: string, user: string}>('/hello'), [fetchApi]);

  // Health checks
  const healthCheck = useCallback(() => 
    fetchApi<any>('/health'), [fetchApi]);
  
  const authCheck = useCallback(() => 
    fetchApi<any>('/health/auth'), [fetchApi]);

  // Return all API methods
  return useMemo(() => ({
    getHello,
    healthCheck,
    authCheck,
  }), [
    getHello,
    healthCheck,
    authCheck
  ]);
}