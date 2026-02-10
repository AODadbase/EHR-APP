// Matching schema from DataExtractor (Image 2)

export interface User {
  username: string;
  name: string;
  role: string;
  email: string;
  organization: string;
  secondaryEmail?: string;
  pronoun?: string;
  position?: string;
  profileImage?: string; // Base64 string
}

export interface PatientInfo {
  name: string | null;
  mrn: string | null;
  age: string | null;
  gender: string | null;
  date_of_birth: string | null;
}

export interface VitalSigns {
  blood_pressure?: string;
  heart_rate?: string;
  temperature?: string;
  respiratory_rate?: string;
  oxygen_saturation?: string;
}

export interface Medication {
  name: string;
  dosage: string;
}

export interface ExtractedData {
  patient_info: PatientInfo;
  vital_signs: VitalSigns;
  diagnoses: string[];
  medications: Medication[];
  allergies: string[];
  procedures: string[];
  clinical_notes: string[];
}

export interface ProcessedDocument {
  id: string;
  filename: string;
  uploadDate: string;
  status: 'processing' | 'completed' | 'failed';
  use_api: boolean;
  use_llm: boolean;
  extracted_data?: ExtractedData;
  discharge_summary?: string;
  elements_count?: number;
}

export interface UploadConfig {
  use_api: boolean;
  use_llm: boolean;
  selected_sections?: string[];
}

export interface SearchResult {
  id: string;
  documentId: string;
  filename: string;
  context: string;
  matchCount: number;
}
