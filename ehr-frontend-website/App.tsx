import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import DocumentDetail from './components/DocumentDetail';
import SearchInterface from './components/SearchInterface';
import SystemSettings from './components/SystemSettings';
import Auth from './components/Auth';
import { authService } from './services/authService';
import { User } from './types';

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  useEffect(() => {
    // Check for existing session
    const currentUser = authService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    setLoadingAuth(false);
  }, []);

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setActiveTab('dashboard');
    setSelectedDocId(null);
  };

  const navigateTo = (tab: string) => {
    setActiveTab(tab);
    if (tab !== 'documents') {
        setSelectedDocId(null);
    }
  };

  const handleDocumentSelect = (id: string) => {
    setSelectedDocId(id);
    setActiveTab('documents');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onSelectDocument={handleDocumentSelect} />;
      case 'search':
        return <SearchInterface onNavigateToDoc={handleDocumentSelect} />;
      case 'settings':
        return user ? (
            <SystemSettings 
                currentUser={user} 
                onUpdateUser={setUser} 
            />
        ) : null;
      case 'documents':
        if (selectedDocId) {
            return (
                <DocumentDetail 
                    documentId={selectedDocId} 
                    onBack={() => setSelectedDocId(null)} 
                />
            );
        }
        return <Dashboard onSelectDocument={handleDocumentSelect} />;
      default:
        return <Dashboard onSelectDocument={handleDocumentSelect} />;
    }
  };

  if (loadingAuth) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <Layout 
      activeTab={activeTab} 
      onNavigate={navigateTo} 
      user={user}
      onLogout={handleLogout}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;
