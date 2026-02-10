import React, { useState, useEffect } from 'react';
import { ChevronLeft, RefreshCw, FileText, Code, Stethoscope, Save, Download } from 'lucide-react';
import { ProcessedDocument, ExtractedData } from '../types';
import { fetchDocumentById, reExtractDocument } from '../services/mockService';
import { DataCard, ListCard } from './DataDisplay';

interface DocumentDetailProps {
  documentId: string;
  onBack: () => void;
}

const DocumentDetail: React.FC<DocumentDetailProps> = ({ documentId, onBack }) => {
  const [doc, setDoc] = useState<ProcessedDocument | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'extraction' | 'json' | 'discharge'>('extraction');
  const [isReExtracting, setIsReExtracting] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [selectedSections, setSelectedSections] = useState<string[]>([]);

    // Sections available for re-extraction
  const availableSections = ['patient_info', 'vital_signs', 'medications', 'diagnoses', 'clinical_notes'];

  useEffect(() => {
    loadDoc();
    // Intentionally ignore exhaustive-deps for document reload
  }, [documentId]);

  const loadDoc = async () => {
    setLoading(true);
    const data = await fetchDocumentById(documentId);
    setDoc(data);
    setLoading(false);
  };

  const handleReExtract = async () => {
    if (!doc) return;
    setIsReExtracting(true);
    try {
        await reExtractDocument(doc.id, selectedSections);
        await loadDoc(); // Reload to reflect updated extraction
        setShowConfig(false);
    } catch (e) {
        console.error(e);
    } finally {
        setIsReExtracting(false);
    }
  };

  const toggleSection = (sec: string) => {
    setSelectedSections(prev => 
        prev.includes(sec) ? prev.filter(s => s !== sec) : [...prev, sec]
    );
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96 text-slate-500">Loading document data...</div>;
  }

  if (!doc) {
    return <div className="text-center text-red-500 mt-10">Document not found.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto pb-20">
    {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
            <button onClick={onBack} className="p-2 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors">
                <ChevronLeft className="h-6 w-6" />
            </button>
            <div>
                <h1 className="text-2xl font-bold text-slate-900">{doc.filename}</h1>
                <p className="text-sm text-slate-500 font-mono">ID: {doc.id} • {doc.elements_count} elements processed</p>
            </div>
        </div>
        
        <div className="flex items-center gap-3">
            <div className="relative">
                <button 
                    onClick={() => setShowConfig(!showConfig)}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 shadow-sm font-medium transition-colors"
                >
                    <RefreshCw className={`h-4 w-4 ${isReExtracting ? 'animate-spin' : ''}`} />
                    Re-Extract
                </button>
                {/* Re-extract dropdown */}
                {showConfig && (
                    <div className="absolute top-full right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 p-4 z-30">
                        <h4 className="text-sm font-semibold text-slate-800 mb-3">Select Sections</h4>
                        <div className="space-y-2 mb-4">
                            {availableSections.map(sec => (
                                <label key={sec} className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer hover:text-slate-900">
                                    <input 
                                        type="checkbox" 
                                        checked={selectedSections.includes(sec)}
                                        onChange={() => toggleSection(sec)}
                                        className="rounded border-slate-300 text-brand-600 focus:ring-brand-500" 
                                    />
                                    <span className="capitalize">{sec.replace('_', ' ')}</span>
                                </label>
                            ))}
                        </div>
                        <button 
                            onClick={handleReExtract}
                            disabled={isReExtracting || selectedSections.length === 0}
                            className="w-full py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isReExtracting ? 'Running...' : 'Run Extraction'}
                        </button>
                    </div>
                )}
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg shadow hover:bg-brand-700 font-medium transition-colors">
                <Download className="h-4 w-4" />
                Export JSON
            </button>
        </div>
      </div>

    {/* Tab navigation */}
      <div className="border-b border-slate-200 mb-8">
        <nav className="flex gap-8">
            <TabButton 
                active={activeTab === 'extraction'} 
                onClick={() => setActiveTab('extraction')} 
                icon={<Stethoscope size={18} />} 
                label="Clinical Data" 
            />
             <TabButton 
                active={activeTab === 'discharge'} 
                onClick={() => setActiveTab('discharge')} 
                icon={<FileText size={18} />} 
                label="Discharge Summary" 
            />
            <TabButton 
                active={activeTab === 'json'} 
                onClick={() => setActiveTab('json')} 
                icon={<Code size={18} />} 
                label="Raw Data" 
            />
        </nav>
      </div>

    {/* Tab content */}
      <div className="animate-in fade-in duration-300">
        {activeTab === 'extraction' && doc.extracted_data && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Patient Info */}
                <DataCard title="Patient Identity" className="border-l-4 border-l-brand-500">
                    <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                        <InfoItem label="Name" value={doc.extracted_data.patient_info.name} />
                        <InfoItem label="MRN" value={doc.extracted_data.patient_info.mrn} />
                        <InfoItem label="Age" value={doc.extracted_data.patient_info.age} />
                        <InfoItem label="Gender" value={doc.extracted_data.patient_info.gender} />
                        <InfoItem label="DOB" value={doc.extracted_data.patient_info.date_of_birth} />
                    </div>
                </DataCard>

                {/* Vitals */}
                <DataCard title="Vital Signs" className="border-l-4 border-l-red-500">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                        <VitalItem label="BP" value={doc.extracted_data.vital_signs.blood_pressure} unit="" />
                        <VitalItem label="HR" value={doc.extracted_data.vital_signs.heart_rate} unit="" />
                        <VitalItem label="Temp" value={doc.extracted_data.vital_signs.temperature} unit="" />
                        <VitalItem label="O2 Sat" value={doc.extracted_data.vital_signs.oxygen_saturation} unit="" />
                        <VitalItem label="Resp" value={doc.extracted_data.vital_signs.respiratory_rate} unit="" />
                    </div>
                </DataCard>

                {/* Medications - Full Width on Mobile, Half on Desktop */}
                <ListCard 
                    title="Medications" 
                    count={doc.extracted_data.medications.length}
                    items={doc.extracted_data.medications.map(m => (
                        <div key={m.name} className="flex justify-between items-center w-full">
                            <span className="font-medium text-slate-800">{m.name}</span>
                            <span className="text-sm text-slate-500 bg-slate-100 px-2 py-1 rounded">{m.dosage}</span>
                        </div>
                    ))}
                />

                {/* Diagnoses */}
                <ListCard 
                    title="Diagnoses" 
                    count={doc.extracted_data.diagnoses.length}
                    items={doc.extracted_data.diagnoses.map(d => (
                         <span key={d} className="font-medium text-slate-800">{d}</span>
                    ))}
                />
                 
                 {/* Clinical Notes - Full Width */}
                 <div className="xl:col-span-2">
                    <ListCard 
                        title="Clinical Notes / Findings" 
                        count={doc.extracted_data.clinical_notes.length}
                        items={doc.extracted_data.clinical_notes.map((n, i) => (
                            <p key={i} className="text-slate-700 leading-relaxed text-sm">{n}</p>
                        ))}
                    />
                 </div>
            </div>
        )}

        {activeTab === 'discharge' && (
             <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-6 pb-6 border-b border-slate-100">
                    <h3 className="text-lg font-bold text-slate-800">Generated Discharge Summary</h3>
                    <button className="flex items-center gap-2 text-brand-600 hover:text-brand-800 text-sm font-medium">
                        <Save size={16} /> Save to Record
                    </button>
                </div>
                <div className="prose prose-slate max-w-none font-mono text-sm whitespace-pre-wrap bg-slate-50 p-6 rounded-lg border border-slate-100">
                    {doc.discharge_summary || "No discharge summary generated."}
                </div>
             </div>
        )}

        {activeTab === 'json' && (
             <div className="bg-slate-900 rounded-xl shadow-lg p-6 overflow-x-auto">
                <pre className="text-xs text-brand-300 font-mono leading-relaxed">
                    {JSON.stringify(doc.extracted_data, null, 2)}
                </pre>
             </div>
        )}
      </div>
    </div>
  );
};

// Tab and display helpers
const TabButton = ({ active, onClick, icon, label }: any) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-2 pb-4 px-1 text-sm font-medium border-b-2 transition-colors ${
            active 
            ? 'border-brand-600 text-brand-600' 
            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
        }`}
    >
        {icon}
        {label}
    </button>
);

const InfoItem = ({ label, value }: { label: string, value: string | null }) => (
    <div className="flex flex-col">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{label}</span>
        <span className="text-sm font-medium text-slate-800 border-b border-slate-100 pb-1">{value || 'N/A'}</span>
    </div>
);

const VitalItem = ({ label, value, unit }: { label: string, value?: string, unit: string }) => (
    <div className="bg-slate-50 rounded-lg p-3 text-center border border-slate-100">
        <span className="text-xs text-slate-500 block mb-1">{label}</span>
        <span className="text-lg font-bold text-slate-800">{value || '-'}</span>
        {unit && <span className="text-xs text-slate-400 ml-1">{unit}</span>}
    </div>
);

export default DocumentDetail;
