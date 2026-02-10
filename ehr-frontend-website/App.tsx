import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import DocumentDetail from './components/DocumentDetail';
import SearchInterface from './components/SearchInterface';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

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
      case 'documents':
        if (selectedDocId) {
            return (
                <DocumentDetail 
                    documentId={selectedDocId} 
                    onBack={() => setSelectedDocId(null)} 
                />
            );
        }
        // If on 'documents' tab but no specific doc selected, show the list (reuse dashboard list or make a dedicated one)
        // reusing dashboard list for simplicity in this demo, but wrapped differently
        return <Dashboard onSelectDocument={handleDocumentSelect} />;
      default:
        return <Dashboard onSelectDocument={handleDocumentSelect} />;
    }
  };

  return (
    <Layout activeTab={activeTab} onNavigate={navigateTo}>
      {renderContent()}
    </Layout>
  );
};

export default App;
