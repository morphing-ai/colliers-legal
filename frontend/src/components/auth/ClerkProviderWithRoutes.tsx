// frontend/src/components/auth/ClerkProviderWithRoutes.tsx
import { ClerkProvider, ClerkLoaded, ClerkLoading } from '@clerk/clerk-react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DashboardPage from '@/pages/DashboardPage';
import TicketsPage from '@/pages/TicketsPage';
import TicketDetailPage from '@/pages/TicketDetailPage';
import NewTicketPage from '@/pages/NewTicketPage';
import SignInPage from '@/pages/SignInPage';
import SignOutPage from '@/pages/SignOutPage';
import Layout from '@/components/layout/Layout';
import AuthWrapper from '@/components/auth/AuthWrapper';
import { Toaster } from '@/components/ui/toaster';

// Get environment variables with proper type checking
const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string;

if (!clerkPubKey) {
  console.error('Missing Clerk Publishable Key');
}

export default function ClerkProviderWithRoutes() {
  return (
    <ClerkProvider 
      publishableKey={clerkPubKey}
      // Disable sign-ups
      signUpUrl={null}
    >
      <ClerkLoading>
        <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
            <p className="text-gray-600 dark:text-gray-300">Loading application...</p>
          </div>
        </div>
      </ClerkLoading>
      
      <ClerkLoaded>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/sign-in/*" element={<SignInPage />} />
            <Route path="/sign-out" element={<SignOutPage />} />
            
            {/* Protected routes */}
            <Route element={<AuthWrapper><Layout /></AuthWrapper>}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/tickets" element={<TicketsPage />} />
              <Route path="/tickets/new" element={<NewTicketPage />} />
              <Route path="/tickets/:id" element={<TicketDetailPage />} />
            </Route>
            
            {/* Redirect all other routes to sign-in or dashboard */}
            <Route path="*" element={
              <AuthWrapper>
                <Navigate to="/" replace />
              </AuthWrapper>
            } />
          </Routes>
          <Toaster />
        </Router>
      </ClerkLoaded>
    </ClerkProvider>
  );
}
