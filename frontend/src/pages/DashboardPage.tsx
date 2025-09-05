// frontend/src/pages/DashboardPage.tsx
import { useState, useEffect } from 'react';
import { RefreshCwIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useApiClient } from '@/lib/api';
import { useUser } from '@clerk/clerk-react';

export default function DashboardPage() {
  const { user } = useUser();
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  
  // Create a simple API client hook
  const apiClient = useApiClient();
  
  // Function to fetch hello world message
  const fetchHelloMessage = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      const response = await apiClient.getHello();
      setMessage(response.message);
    } catch (err) {
      console.error('Error fetching hello message:', err);
      setError("Failed to fetch message. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch message on component mount
  useEffect(() => {
    fetchHelloMessage();
  }, []);
  
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">
            Hello, {user?.primaryEmailAddress?.emailAddress || 'User'}!
          </p>
        </div>
        <Button variant="outline" onClick={fetchHelloMessage} disabled={isLoading}>
          <RefreshCwIcon className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>API Response</CardTitle>
          <CardDescription>
            A response from the hello world API endpoint
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-6">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
            </div>
          ) : error ? (
            <div className="py-6 text-center text-red-500">{error}</div>
          ) : (
            <div className="py-6 text-center text-xl font-semibold">
              {message}
            </div>
          )}
        </CardContent>
        <CardFooter className="text-sm text-gray-500">
          This response is only visible to authenticated users.
        </CardFooter>
      </Card>
    </div>
  );
}