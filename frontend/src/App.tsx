// frontend/src/App.tsx
import { Route, Routes, Navigate } from 'react-router-dom';
import { useUser } from '@clerk/clerk-react';
import Layout from '@/components/layout/Layout';
import DashboardPage from '@/pages/DashboardPage';
import ComplianceAnalyzer from '@/pages/ComplianceAnalyzer';
import ContractAnalysis from '@/pages/ContractAnalysis';
import HealthCheckPage from '@/pages/HealthCheckPage';
import NeurobotManager from '@/pages/NeurobotManager';
import AdminPage from '@/pages/AdminPage';
import SignInPage from '@/pages/SignInPage';
import SignOutPage from '@/pages/SignOutPage';
import AuthWrapper from '@/components/auth/AuthWrapper';
import { Toaster } from '@/components/ui/toaster';
import { AuthProvider } from '@/context/AuthContext';

function App() {
  const { isLoaded } = useUser();

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading application...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/sign-in" element={<SignInPage />} />
        <Route path="/sign-out" element={<SignOutPage />} />
        
        {/* Protected routes with layout */}
        <Route element={<AuthWrapper><Layout /></AuthWrapper>}>
          <Route path="/" element={<ContractAnalysis />} />
          <Route path="/contracts" element={<ContractAnalysis />} />
          <Route path="/compliance" element={<ComplianceAnalyzer />} />
          <Route path="/compliance/analysis/:sessionId" element={<ComplianceAnalyzer />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/neurobots" element={<NeurobotManager />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/health" element={<HealthCheckPage />} />
        </Route>
        
        {/* Catch-all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      
      {/* Toast notifications */}
      <Toaster />
    </AuthProvider>
  );
}

export default App;