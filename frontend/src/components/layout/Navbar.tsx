import { Link } from 'react-router-dom';
import { UserButton } from '@clerk/clerk-react';
import { MenuIcon } from 'lucide-react';

interface NavbarProps {
  onMenuToggle?: () => void;
}

export default function Navbar({ onMenuToggle }: NavbarProps) {
  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm z-10">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side - Logo and mobile menu button */}
          <div className="flex items-center">
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary lg:hidden"
              onClick={onMenuToggle}
              aria-label="Open main menu"
            >
              <MenuIcon className="h-6 w-6" />
            </button>
            
            <Link to="/" className="flex items-center ml-4 lg:ml-0">
              <div className="bg-blue-600 rounded-md p-1.5 mr-2">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="text-xl font-semibold text-gray-900 dark:text-white">Compliance Analyzer</span>
            </Link>
          </div>
          
          {/* Right side - User menu */}
          <div className="flex items-center user-menu">
            <UserButton 
              afterSignOutUrl="/sign-in" 
              appearance={{
                elements: {
                  userButtonAvatarBox: "h-8 w-8",
                  // Hide sign-up option in user dropdown
                  userPreviewMainIdentifier: "font-medium",
                  userPreviewSecondaryIdentifier: "text-sm text-gray-500",
                  userButtonPopoverCard: "shadow-lg rounded-lg",
                  userButtonPopoverActionButton: "text-gray-700 dark:text-gray-300",
                  userButtonPopoverActionButtonText: "text-sm font-medium",
                  userButtonPopoverFooter: "hidden" // Hide sign-up links in popover
                }
              }}
            />
          </div>
        </div>
      </div>
    </nav>
  );
}
