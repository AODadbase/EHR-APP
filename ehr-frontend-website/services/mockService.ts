import { ProcessedDocument, UploadConfig, SearchResult } from '../types';

const API_BASE = '/api';

const handleResponse = async <T>(res: Response): Promise<T> => {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
};

export const fetchDocuments = async (): Promise<ProcessedDocument[]> => {
  const res = await fetch(`${API_BASE}/documents`);
  return handleResponse<ProcessedDocument[]>(res);
};

export const fetchDocumentById = async (id: string): Promise<ProcessedDocument | undefined> => {
  const res = await fetch(`${API_BASE}/documents/${id}`);
  if (res.status === 404) return undefined;
  return handleResponse<ProcessedDocument>(res);
};

export const uploadDocument = async (file: File, config: UploadConfig): Promise<ProcessedDocument> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('use_api', String(config.use_api));
  formData.append('use_llm', String(config.use_llm));
  if (config.selected_sections && config.selected_sections.length > 0) {
    formData.append('selected_sections', JSON.stringify(config.selected_sections));
  }

  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<ProcessedDocument>(res);
};

export const reExtractDocument = async (id: string, selectedSections: string[]): Promise<ProcessedDocument> => {
  const res = await fetch(`${API_BASE}/documents/${id}/reextract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ selected_sections: selectedSections }),
  });
  return handleResponse<ProcessedDocument>(res);
};

export const searchDocuments = async (query: string): Promise<SearchResult[]> => {
  if (!query.trim()) return [];
  const params = new URLSearchParams({ query });
  const res = await fetch(`${API_BASE}/search?${params.toString()}`);
  return handleResponse<SearchResult[]>(res);
};
