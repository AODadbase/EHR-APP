import { ProcessedDocument, ExtractedData, UploadConfig, SearchResult } from '../types';

const MOCK_DELAY = 1500;

// Helper to generate a dummy document
const generateMockDoc = (id: string, filename: string): ProcessedDocument => {
  const data: ExtractedData = {
    patient_info: {
      name: "John H. Doe",
      mrn: "MRN-88421",
      age: "45",
      gender: "Male",
      date_of_birth: "1979-05-12"
    },
    vital_signs: {
      blood_pressure: "120/80 mmHg",
      heart_rate: "72 bpm",
      temperature: "98.6 F",
      oxygen_saturation: "98%"
    },
    diagnoses: [
      "Acute Bronchitis",
      "Essential Hypertension",
      "Type 2 Diabetes Mellitus"
    ],
    medications: [
      { name: "Lisinopril", dosage: "10mg Daily" },
      { name: "Metformin", dosage: "500mg BID" },
      { name: "Albuterol Inhaler", dosage: "PRN" }
    ],
    allergies: ["Penicillin", "Peanuts"],
    procedures: ["Chest X-Ray", "Physical Exam"],
    clinical_notes: [
      "Patient reports persistent cough for 3 days.",
      "Lungs clear to auscultation bilaterally despite cough.",
      "Advised to rest and hydrate."
    ]
  };

  return {
    id,
    filename,
    uploadDate: new Date().toISOString(),
    status: 'completed',
    use_api: true,
    use_llm: true,
    elements_count: 142,
    extracted_data: data,
    discharge_summary: `DISCHARGE SUMMARY\n\nPatient Name: John H. Doe\nMRN: MRN-88421\nDate: ${new Date().toLocaleDateString()}\n\nDiagnoses:\n- Acute Bronchitis\n- Essential Hypertension\n\nPlan:\nContinue current medications. Follow up with PCP in 2 weeks if symptoms do not improve.\n\nSigned,\nDr. AI Assistant`
  };
};

let documents: ProcessedDocument[] = [
  generateMockDoc('1', 'referral_letter_jane_smith.pdf'),
  { ...generateMockDoc('2', 'lab_results_2024.pdf'), status: 'processing', extracted_data: undefined }
];

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
        status: 'completed', // Simulating instant completion for demo
        use_api: config.use_api,
        use_llm: config.use_llm,
        elements_count: Math.floor(Math.random() * 500) + 50,
        extracted_data: generateMockDoc('temp', 'temp').extracted_data,
        discharge_summary: "Generating discharge summary..."
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
      
      // Simulate partial update based on re-extraction
      const updatedDoc = { ...documents[docIndex] };
      updatedDoc.uploadDate = new Date().toISOString(); // refresh timestamp
      documents[docIndex] = updatedDoc;
      
      resolve(updatedDoc);
    }, MOCK_DELAY);
  });
};

export const searchDocuments = async (query: string): Promise<SearchResult[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      if (!query) resolve([]);
      const results: SearchResult[] = [
        {
          id: 's1',
          documentId: '1',
          filename: 'referral_letter_jane_smith.pdf',
          matchCount: 3,
          context: `...patient reports severe <b>${query}</b> during the night...`
        }
      ];
      resolve(results);
    }, 800);
  });
};
