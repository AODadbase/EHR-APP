import { ProcessedDocument, UploadConfig, SearchResult } from '../types';

const MOCK_DELAY = 1500;

// Initialize with an empty array. No dummy data.
let documents: ProcessedDocument[] = [];

export const fetchDocuments = async (): Promise<ProcessedDocument[]> => {
  return new Promise((resolve) => {
    setTimeout(() => resolve([...documents]), 600);
  });
};

export const fetchDocumentById = async (id: string): Promise<ProcessedDocument | undefined> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const doc = documents.find(d => d.id === id);
      resolve(doc);
    }, 400);
  });
};

export const uploadDocument = async (file: File, config: UploadConfig): Promise<ProcessedDocument> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newDoc: ProcessedDocument = {
        id: Math.random().toString(36).substring(7),
        filename: file.name,
        uploadDate: new Date().toISOString(),
        status: 'completed', 
        use_api: config.use_api,
        use_llm: config.use_llm,
        elements_count: Math.floor(Math.random() * 500) + 50,
        // Since we removed the mock generator, we initialize empty extracted data.
        // In a real app, this would be populated by the backend response.
        extracted_data: {
          patient_info: { name: null, mrn: null, age: null, gender: null, date_of_birth: null },
          vital_signs: {},
          diagnoses: [],
          medications: [],
          allergies: [],
          procedures: [],
          clinical_notes: ["Data extraction pending backend integration."]
        },
        discharge_summary: "Pending generation..."
      };
      documents = [newDoc, ...documents];
      resolve(newDoc);
    }, MOCK_DELAY);
  });
};

export const reExtractDocument = async (id: string, selectedSections: string[]): Promise<ProcessedDocument> => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const docIndex = documents.findIndex(d => d.id === id);
      if (docIndex === -1) {
        reject("Document not found");
        return;
      }
      
      const updatedDoc = { ...documents[docIndex] };
      updatedDoc.uploadDate = new Date().toISOString(); 
      documents[docIndex] = updatedDoc;
      
      resolve(updatedDoc);
    }, MOCK_DELAY);
  });
};

export const searchDocuments = async (query: string): Promise<SearchResult[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      if (!query) resolve([]);
      // Simple mock search implementation against the in-memory documents
      const results: SearchResult[] = documents
        .filter(d => d.filename.toLowerCase().includes(query.toLowerCase()))
        .map(d => ({
            id: `search-${d.id}`,
            documentId: d.id,
            filename: d.filename,
            matchCount: 1,
            context: `Found match in document filename: <b>${d.filename}</b>`
        }));
      resolve(results);
    }, 800);
  });
};