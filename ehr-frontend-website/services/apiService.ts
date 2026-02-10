import { ProcessedDocument, UploadConfig, SearchResult } from '../types';

const API_BASE = 'http://localhost:8000/api';

// Renamed from 'listDocuments' to 'fetchDocuments' to match Dashboard
export const fetchDocuments = async (): Promise<ProcessedDocument[]> => {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to load documents');
  return res.json();
};

// Renamed from 'getDocument' to 'fetchDocumentById' to match DocumentDetail
export const fetchDocumentById = async (id: string): Promise<ProcessedDocument> => {
  const res = await fetch(`${API_BASE}/documents/${id}`);
  if (!res.ok) throw new Error('Failed to load document');
  return res.json();
};

// Renamed from 'uploadDocumentApi' to 'uploadDocument' to match Dashboard
export const uploadDocument = async (file: File, config: UploadConfig): Promise<ProcessedDocument> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('use_api', String(config.use_api));
  formData.append('use_llm', String(config.use_llm));
  
  if (config.selected_sections) {
    formData.append('selected_sections', JSON.stringify(config.selected_sections));
  }

  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error('Failed to upload document');
  return res.json();
};

// Renamed from 'reextractDocumentApi' to 'reExtractDocument' to match DocumentDetail
export const reExtractDocument = async (id: string, selectedSections: string[]): Promise<ProcessedDocument> => {
  const res = await fetch(`${API_BASE}/documents/${id}/reextract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_sections: selectedSections }),
  });

  if (!res.ok) throw new Error('Failed to re-extract document');
  return res.json();
};

// Renamed from 'searchDocumentsApi' to 'searchDocuments'
export const searchDocuments = async (query: string): Promise<SearchResult[]> => {
  const params = new URLSearchParams({ query });
  const res = await fetch(`${API_BASE}/search?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to search documents');
  return res.json();
};