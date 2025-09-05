// frontend/src/pages/HealthCheckPage.tsx
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useApiClient } from '@/lib/api';

export default function HealthCheckPage() {
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [authStatus, setAuthStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const { healthCheck, authCheck } = useApiClient();
  
  const fetchHealthStatus = async () => {
    setIsLoading(true);
    try {
      const health = await healthCheck();
      setHealthStatus(health);
      
      try {
        const auth = await authCheck();
        setAuthStatus(auth);
      } catch (error) {
        console.error('Auth health check failed:', error);
        setAuthStatus({ error: 'Auth check failed' });
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ error: 'Health check failed' });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchHealthStatus();
  }, []);
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Health Status</h1>
        <Button onClick={fetchHealthStatus} disabled={isLoading}>
          {isLoading ? 'Checking...' : 'Refresh'}
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>API Health</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-6">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
              </div>
            ) : healthStatus?.error ? (
              <div className="text-red-500">Failed to check API health</div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className="font-semibold">{healthStatus?.status || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span>API Version:</span>
                  <span className="font-semibold">{healthStatus?.api_version || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Debug Mode:</span>
                  <span className="font-semibold">{healthStatus?.debug_mode ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Auth Type:</span>
                  <span className="font-semibold">{healthStatus?.auth_type || 'Unknown'}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Authentication Status</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-6">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
              </div>
            ) : authStatus?.error ? (
              <div className="text-red-500">Failed to check authentication status</div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className="font-semibold">{authStatus?.status || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span>User ID:</span>
                  <span className="font-semibold truncate max-w-64">{authStatus?.user_id || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Email:</span>
                  <span className="font-semibold">{authStatus?.email || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Authenticated:</span>
                  <span className="font-semibold">{authStatus?.authenticated ? 'Yes' : 'No'}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
