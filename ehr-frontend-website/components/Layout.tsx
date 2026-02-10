import React from 'react';
import { LayoutDashboard, FileText, Search, Settings, Activity, LogOut } from 'lucide-react';
import { User } from '../types';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onNavigate: (tab: string) => void;
  user: User | null;
  onLogout: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeTab, onNavigate, user, onLogout }) => {
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shadow-xl z-20">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-600 rounded-lg">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Traceable Health</h1>
              <p className="text-xs text-slate-400 font-mono">v0.3.1 beta</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          <NavItem 
            icon={<LayoutDashboard size={20} />} 
            label="Dashboard" 
            active={activeTab === 'dashboard'} 
            onClick={() => onNavigate('dashboard')} 
          />
          <NavItem 
            icon={<FileText size={20} />} 
            label="Documents" 
            active={activeTab === 'documents'} 
            onClick={() => onNavigate('documents')} 
          />
          <NavItem 
            icon={<Search size={20} />} 
            label="Global Search" 
            active={activeTab === 'search'} 
            onClick={() => onNavigate('search')} 
          />
        </nav>

        <div className="p-4 border-t border-slate-700 space-y-2">
          <button 
            onClick={() => onNavigate('settings')}
            className={`flex items-center gap-3 px-4 py-2 w-full text-sm font-medium transition-colors rounded-lg ${
                activeTab === 'settings' 
                ? 'bg-slate-800 text-white' 
                : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <Settings size={18} />
            <span>System Settings</span>
          </button>
          <button 
            onClick={onLogout}
            className="flex items-center gap-3 px-4 py-2 w-full text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shadow-sm z-10">
          <div className="flex items-center gap-4">
             <h2 className="text-xl font-semibold text-slate-800 capitalize">{activeTab.replace('-', ' ')}</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end">
              <span className="text-sm font-medium text-slate-700">{user?.name || 'Guest User'}</span>
              <span className="text-xs text-slate-500">{user?.role || 'Clinician'}</span>
            </div>
            <div className="h-10 w-10 rounded-full bg-brand-50 flex items-center justify-center border border-brand-200 text-brand-700 overflow-hidden">
                {user?.profileImage ? (
                    <img src={user.profileImage} alt="Profile" className="w-full h-full object-cover" />
                ) : (
                    <span className="font-bold text-sm">{user ? getInitials(user.name) : 'G'}</span>
                )}
            </div>
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon, label, active, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
        active 
          ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/20' 
          : 'hover:bg-slate-800 text-slate-400 hover:text-white'
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
      {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
    </button>
  );
};

export default Layout;