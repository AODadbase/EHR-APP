import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, Clock, AlertCircle, ArrowRight } from 'lucide-react';
import { fetchDocuments, uploadDocument } from '../services/mockService';
import { ProcessedDocument } from '../types';

interface DashboardProps {
  onSelectDocument: (id: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onSelectDocument }) => {
  const [docs, setDocs] = useState<ProcessedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadConfig, setUploadConfig] = useState({ use_api: true, use_llm: true });

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    const data = await fetchDocuments();
    setDocs(data);
    setLoading(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setIsUploading(true);
      await uploadDocument(e.target.files[0], uploadConfig);
      await loadDocs();
      setIsUploading(false);
    }
  };

  const stats = [
    { label: 'Total Processed', value: docs.length, icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Pending Review', value: docs.filter(d => d.status === 'processing').length, icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Successful Extractions', value: docs.filter(d => d.status === 'completed').length, icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">{stat.label}</p>
              <p className="text-3xl font-bold text-slate-800 mt-1">{stat.value}</p>
            </div>
            <div className={`p-3 rounded-lg ${stat.bg}`}>
              <stat.icon className={`h-6 w-6 ${stat.color}`} />
            </div>
          </div>
        ))}
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-slate-800">New Analysis</h3>
            <div className="flex gap-4 text-sm text-slate-600">
                <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={uploadConfig.use_api} onChange={e => setUploadConfig(prev => ({...prev, use_api: e.target.checked}))} className="rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
                    Unstructured API
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={uploadConfig.use_llm} onChange={e => setUploadConfig(prev => ({...prev, use_llm: e.target.checked}))} className="rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
                    LLM Extraction
                </label>
            </div>
        </div>
        <div className="p-8">
          <label className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-colors ${isUploading ? 'border-brand-300 bg-brand-50' : 'border-slate-300 hover:border-brand-500 hover:bg-slate-50'}`}>
            <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf" disabled={isUploading} />
            <div className={`p-4 rounded-full mb-4 ${isUploading ? 'bg-brand-100 animate-pulse' : 'bg-slate-100'}`}>
                <Upload className={`h-8 w-8 ${isUploading ? 'text-brand-600' : 'text-slate-500'}`} />
            </div>
            {isUploading ? (
               <div className="text-center">
                   <p className="text-lg font-medium text-brand-700">Processing Document...</p>
                   <p className="text-sm text-brand-500 mt-1">Extracting elements and running inference</p>
               </div>
            ) : (
                <div className="text-center">
                    <p className="text-lg font-medium text-slate-700">Click to upload or drag PDF here</p>
                    <p className="text-sm text-slate-500 mt-1">Supports standard clinical PDF formats</p>
                </div>
            )}
          </label>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h3 className="text-lg font-semibold text-slate-800">Recent Documents</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
              <tr>
                <th className="px-6 py-4">Filename</th>
                <th className="px-6 py-4">Upload Date</th>
                <th className="px-6 py-4">Configuration</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">Loading records...</td>
                </tr>
              ) : docs.length === 0 ? (
                <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">No documents processed yet.</td>
                </tr>
              ) : (
                docs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4 font-medium text-slate-900 flex items-center gap-3">
                        <FileText className="h-4 w-4 text-slate-400" />
                        {doc.filename}
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-mono text-xs">
                        {new Date(doc.uploadDate).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                        <div className="flex gap-2">
                            {doc.use_api && <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">API</span>}
                            {doc.use_llm && <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100">LLM</span>}
                        </div>
                    </td>
                    <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                            doc.status === 'completed' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                            doc.status === 'processing' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                            'bg-red-50 text-red-700 border-red-200'
                        }`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${
                                doc.status === 'completed' ? 'bg-emerald-500' :
                                doc.status === 'processing' ? 'bg-amber-500' : 'bg-red-500'
                            }`} />
                            {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                        </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                        <button 
                            onClick={() => onSelectDocument(doc.id)}
                            className="text-brand-600 hover:text-brand-800 font-medium text-sm inline-flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            View Details <ArrowRight className="h-4 w-4" />
                        </button>
                    </td>
                    </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
