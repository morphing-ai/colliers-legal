// frontend/src/components/layout/Sidebar.tsx
import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  ChevronLeftIcon, 
  LayoutDashboardIcon,
  ActivityIcon,
  FileCheck,
  BookOpen,
  FolderOpen,
  Settings
} from 'lucide-react';

interface SidebarProps {
  onToggleCollapse?: (collapsed: boolean) => void;
}

export default function Sidebar({ onToggleCollapse }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  
  // Notify parent component when collapse state changes
  useEffect(() => {
    if (onToggleCollapse) {
      onToggleCollapse(collapsed);
    }
  }, [collapsed, onToggleCollapse]);
  
  const navigation = [
    { name: 'Contract Analysis', href: '/', icon: FileCheck },
    { name: 'Neurobot Manager', href: '/neurobots', icon: BookOpen },
    { name: 'Admin', href: '/admin', icon: Settings },
  ];
  
  return (
    <div 
      className={`h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-sm transition-all duration-300 ease-in-out ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="flex items-center justify-end h-16 px-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-md text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <ChevronLeftIcon 
            className={`h-5 w-5 transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} 
          />
        </button>
      </div>
      
      <div className="py-6">
        <div className="px-2 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            const ItemIcon = item.icon;
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-2 py-3 rounded-md transition-colors duration-150 ${
                  isActive
                    ? 'bg-primary/10 text-primary dark:bg-primary/20'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <ItemIcon className={`h-5 w-5 flex-shrink-0 ${isActive ? 'text-primary' : ''}`} />
                {!collapsed && (
                  <span className="ml-3 text-sm font-medium">{item.name}</span>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}