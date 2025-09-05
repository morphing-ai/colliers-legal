// frontend/src/pages/SignOutPage.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClerk } from '@clerk/clerk-react';

export default function SignOutPage() {
  const { signOut } = useClerk();
  const navigate = useNavigate();

  useEffect(() => {
    const performSignOut = async () => {
      await signOut();
      navigate('/sign-in');
    };

    performSignOut();
  }, [signOut, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div className="inline-flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
        <h2 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
          Signing out...
        </h2>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Please wait while we securely sign you out.
        </p>
      </div>
    </div>
  );
}