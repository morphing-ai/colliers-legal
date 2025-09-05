// frontend/src/components/layout/Layout.tsx
import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  // Handle screen resizing to close mobile menu on larger screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Handle sidebar collapse state
  const handleSidebarToggle = (collapsed: boolean) => {
    setIsSidebarCollapsed(collapsed);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <Navbar onMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - hidden on mobile by default */}
        <div 
          className={`${
            isMobileMenuOpen ? 'block absolute inset-y-0 left-0 z-50 mt-16' : 'hidden'
          } lg:relative lg:block lg:mt-0 transition-all duration-300 ease-in-out ${
            isSidebarCollapsed ? 'lg:w-16' : 'lg:w-64'
          }`}
        >
          <Sidebar onToggleCollapse={handleSidebarToggle} />
        </div>

        {/* Mobile overlay */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-gray-800 bg-opacity-50 z-40 lg:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Main content - dynamically adjust width based on sidebar state */}
        <main 
          className={`flex-1 overflow-auto p-4 md:p-6 transition-all duration-300 ease-in-out ${
            isSidebarCollapsed ? 'lg:ml-0' : 'lg:ml-0'
          }`}
        >
          <div className="container mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}