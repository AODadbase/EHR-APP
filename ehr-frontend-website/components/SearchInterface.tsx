import React, { useState } from 'react';
import { Search, FileText, ArrowRight } from 'lucide-react';
import { searchDocuments } from '../services/mockService';
import { SearchResult } from '../types';

interface SearchInterfaceProps {
    onNavigateToDoc: (id: string) => void;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onNavigateToDoc }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    const data = await searchDocuments(query);
    setResults(data);
    setIsSearching(false);
    setHasSearched(true);
  };

  return (
    <div className="max-w-4xl mx-auto mt-10">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold text-slate-800 mb-2">Global Semantic Search</h2>
        <p className="text-slate-500">Search across processed PDF elements, clinical entities, and metadata.</p>
      </div>

      <form onSubmit={handleSearch} className="relative mb-12">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., 'hypertension diagnosis', 'patient John', 'lab results > 5.0'"
          className="w-full px-6 py-4 pl-14 rounded-full border border-slate-300 shadow-sm focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none text-lg transition-all"
        />
        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 h-6 w-6" />
        <button 
            type="submit"
            disabled={isSearching}
            className="absolute right-3 top-1/2 -translate-y-1/2 px-6 py-2 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition-colors disabled:opacity-70"
        >
            {isSearching ? 'Searching...' : 'Search'}
        </button>
      </form>

      <div className="space-y-4">
        {hasSearched && results.length === 0 && (
            <div className="text-center py-10 bg-white rounded-xl border border-slate-200">
                <p className="text-slate-500">No matches found for "{query}".</p>
            </div>
        )}

        {results.map((res) => (
          <div key={res.id} className="bg-white p-6 rounded-xl border border-slate-200 hover:border-brand-300 shadow-sm transition-all group">
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2 text-brand-600 font-medium">
                    <FileText size={18} />
                    {res.filename}
                </div>
                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">{res.matchCount} matches</span>
            </div>
            
            {/* Dangerous HTML is used here to render the 'highlighted' search context from the backend */}
            <div 
                className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100 mb-4 font-mono leading-relaxed"
                dangerouslySetInnerHTML={{ __html: res.context }}
            />
            
            <button 
                onClick={() => onNavigateToDoc(res.documentId)}
                className="text-sm font-medium text-slate-900 flex items-center gap-1 hover:gap-2 transition-all"
            >
                Go to Document <ArrowRight size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchInterface;
