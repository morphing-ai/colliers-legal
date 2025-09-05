// frontend/src/pages/SignInPage.tsx
import { useEffect } from 'react';
import { SignIn } from '@clerk/clerk-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthContext } from '@/context/AuthContext';

export default function SignInPage() {
  const { isAuthenticated, isLoading } = useAuthContext();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the path the user was trying to access before redirecting to login
  const from = location.state?.from?.pathname || '/';
  
  // If user becomes authenticated, redirect them
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, from]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center">
            <div className="bg-primary rounded-full p-3 inline-flex">
              <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
              </svg>
            </div>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
            Ticketing System
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Sign in to manage your support tickets
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden">
          <SignIn
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "shadow-none bg-transparent rounded-none",
                formButtonPrimary: "bg-primary hover:bg-primary/90 transition-colors",
                headerTitle: "text-gray-900 dark:text-white",
                headerSubtitle: "text-gray-600 dark:text-gray-400",
                formFieldInput: "border border-gray-300 dark:border-gray-700",
                footerActionLink: "text-primary hover:text-primary/90",
                identityPreviewEditButton: "text-primary hover:text-primary/90",
                // Hide sign-up links and options
                footerAction: "hidden",
                alternativeMethods: "hidden"
              }
            }}
            signUpUrl={null}
            redirectUrl="/"
          />
        </div>
        
        <div className="text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
            Powered by FastAPI • React • Shadcn UI
          </p>
        </div>
      </div>
    </div>
  );
}