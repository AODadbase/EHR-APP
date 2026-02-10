"""Data extraction module to parse document elements and extract structured clinical data"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Optional LLM extractor import
try:
    from src.llm_extractor import LLMExtractor
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMExtractor = None


class DataExtractor:
    """Extract structured clinical data from unstructured document elements"""
    
    def __init__(self, use_llm: bool = False, llm_extractor: Optional[Any] = None):
        """
        Initialize the data extractor
        
        Args:
            use_llm: If True, use LLM extraction when available (falls back to regex)
            llm_extractor: Optional LLMExtractor instance (will create one if None and use_llm=True)
        """
        self.use_llm = use_llm and LLM_AVAILABLE
        self.llm_extractor = llm_extractor
        
        if self.use_llm and self.llm_extractor is None:
            try:
                self.llm_extractor = LLMExtractor()
                if not self.llm_extractor._is_available():
                    logger.warning("LLM extraction requested but API key not available. Falling back to regex.")
                    self.use_llm = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLM extractor: {str(e)}. Falling back to regex.")
                self.use_llm = False
        # Patient information patterns - improved to handle actual document format
        self.patient_name_patterns = [
            # PATIENT IDENTIFICATION: Ms. J is a...
            r'PATIENT\s+IDENTIFICATION[:\s]+(?:Ms\.|Mr\.|Mrs\.|Dr\.|Miss\.|Mx\.)?\s*([A-Z][a-z]*(?:\s+[A-Z][a-z]*)?)',
            # Fallback patterns
            r'patient\s*name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            # Extract from "Ms. J" format
            r'(?:Ms\.|Mr\.|Mrs\.|Dr\.)\s+([A-Z][a-z]*(?:\s+[A-Z][a-z]*)?)',
        ]
        
        # Date of birth patterns
        self.dob_patterns = [
            r'date\s*of\s*birth[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'dob[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'birth\s*date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        # MRN patterns - search in PATIENT IDENTIFICATION section
        self.mrn_patterns = [
            r'(?:MRN|medical\s+record\s+number|patient\s+id)[:\s]+([A-Z0-9-]+)',
            r'mrn[:\s]+([A-Z0-9-]+)',
        ]
        
        # Age patterns - handle "76-year-old" format
        self.age_patterns = [
            r'(\d+)[-]year[-]old',  # Handles hyphens: "76-year-old"
            r'(\d+)\s*years?\s*old',  # Handles spaces: "76 years old"
            r'age[:\s]+(\d+)',
            # Extract from context: "76-year-old woman"
            r'(\d+)[-]year[-]old\s+(?:man|woman|male|female)',
        ]
        
        # Gender patterns - extract from context
        self.gender_patterns = [
            # Extract from "76-year-old woman/man"
            r'(\d+)[-]year[-]old\s+(man|woman|male|female)',
            r'(\d+)\s*years?\s*old\s+(man|woman|male|female)',
            # Extract from title: "Ms." = Female, "Mr." = Male
            r'(Ms\.|Mrs\.|Miss\.)',  # Female
            r'(Mr\.)',  # Male
            # Explicit gender fields
            r'gender[:\s]+(male|female|m|f)',
            r'sex[:\s]+(male|female|m|f)',
        ]
        
        # Vital signs patterns
        self.vital_signs_patterns = {
            'blood_pressure': r'blood\s*pressure[:\s]+(\d+/\d+)',
            'heart_rate': r'heart\s*rate[:\s]+(\d+)',
            'temperature': r'temperature[:\s]+(\d+\.?\d*)',
            'respiratory_rate': r'respiratory\s*rate[:\s]+(\d+)',
            'oxygen_saturation': r'o2\s*sat[:\s]+(\d+)',
        }
        
        # Diagnosis patterns - also look for ACTIVE MEDICAL ISSUES section
        self.diagnosis_patterns = [
            r'diagnosis[:\s]+([^\.\n]+)',
            r'diagnoses[:\s]+([^\.\n]+)',
            r'condition[:\s]+([^\.\n]+)',
            r'icd[:\s]+([A-Z0-9.]+)',
            # Active medical issues numbered list items
            r'ACTIVE\s+MEDICAL\s+ISSUES[:\s]+(.*?)(?=PAST\s+MEDICAL|RECONCILED|ALLERGIES|$)',
        ]
        
        # Medication patterns - also look for RECONCILED ADMISSION MEDICATION LIST
        self.medication_patterns = [
            # Numbered medication list items: "1. Diltiazem 120 mg..."
            r'(\d+)\.\s+([A-Za-z\s-]+?)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g|units?|mcg)',
            r'RECONCILED\s+ADMISSION\s+MEDICATION\s+LIST[:\s]+(.*?)(?=ALLERGIES|SOCIAL|HISTORY|$)',
            r'medication[:\s]+([^\.\n]+)',
            r'medications[:\s]+([^\.\n]+)',
            r'prescribed[:\s]+([^\.\n]+)',
            r'(\w+)\s+(\d+)\s*(mg|ml|units?)\s*(?:po|iv|im|subq)',  # Drug name with dosage
        ]
        
        # Allergy patterns
        self.allergy_patterns = [
            r'allerg(y|ies)[:\s]+([^\.\n]+)',
            r'no\s+known\s+allergies',
            r'nka[:\s]+([^\.\n]+)',
        ]
        
        # Procedure patterns
        self.procedure_patterns = [
            r'procedure[:\s]+([^\.\n]+)',
            r'procedures[:\s]+([^\.\n]+)',
            r'surgery[:\s]+([^\.\n]+)',
            r'intervention[:\s]+([^\.\n]+)',
        ]
    
    def extract(
        self, 
        elements: List[Dict[str, Any]], 
        selected_sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from document elements using structure-aware approach
        
        Args:
            elements: List of document elements from unstructured.io
            selected_sections: Optional list of section names to extract from (for LLM extraction)
            
        Returns:
            Dictionary containing extracted structured data
        """
        # First pass: Try structure-aware extraction using sections
        sections = self._identify_sections(elements)
        
        # Combine all text for fallback patterns
        full_text = self._combine_text(elements)
        
        # Try LLM extraction first if enabled
        if self.use_llm and self.llm_extractor:
            try:
                llm_data = self.llm_extractor.extract_from_sections(
                    sections, 
                    selected_sections
                )
                
                # Use LLM results, but fallback to regex for missing fields
                extracted_data = {
                    'patient_info': llm_data.get('patient_info', {}) or 
                                   self._extract_patient_info_structured(elements, sections, full_text),
                    'vital_signs': llm_data.get('vital_signs', {}) or 
                                  self._extract_vital_signs(full_text),
                    'diagnoses': llm_data.get('diagnoses', []) or 
                                self._extract_diagnoses_structured(elements, sections, full_text),
                    'medications': llm_data.get('medications', []) or 
                                 self._extract_medications_structured(elements, sections, full_text),
                    'allergies': llm_data.get('allergies', []) or 
                               self._extract_allergies(full_text),
                    'procedures': self._extract_procedures(full_text),  # Not in LLM extractor yet
                    'clinical_notes': self._extract_clinical_notes(elements),
                }
                
                # Merge LLM results with regex fallback (LLM takes precedence)
                if llm_data.get('patient_info'):
                    extracted_data['patient_info'].update(llm_data['patient_info'])
                if llm_data.get('vital_signs'):
                    extracted_data['vital_signs'].update(llm_data['vital_signs'])
                if llm_data.get('diagnoses'):
                    extracted_data['diagnoses'] = llm_data['diagnoses']
                if llm_data.get('medications'):
                    extracted_data['medications'] = llm_data['medications']
                if llm_data.get('allergies'):
                    extracted_data['allergies'] = llm_data['allergies']
                
                return extracted_data
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to regex: {str(e)}")
                # Fall through to regex extraction
        
        # Fallback to regex-based extraction
        extracted_data = {
            'patient_info': self._extract_patient_info_structured(elements, sections, full_text),
            'vital_signs': self._extract_vital_signs(full_text),
            'diagnoses': self._extract_diagnoses_structured(elements, sections, full_text),
            'medications': self._extract_medications_structured(elements, sections, full_text),
            'allergies': self._extract_allergies(full_text),
            'procedures': self._extract_procedures(full_text),
            'clinical_notes': self._extract_clinical_notes(elements),
        }
        
        return extracted_data
    
    def _combine_text(self, elements: List[Dict[str, Any]]) -> str:
        """Combine text from all elements"""
        texts = []
        for elem in elements:
            text = elem.get('text', '')
            if text:
                texts.append(text)
        return '\n'.join(texts)
    
    def _identify_sections(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Identify document sections using element types (Title, ListItem, etc.)"""
        sections = {}
        current_section = None
        
        for elem in elements:
            elem_type = elem.get('type', '').lower()
            text = elem.get('text', '').strip()
            
            # Prioritize Title elements as section headers
            # Title elements are the primary way Unstructured.io marks section headers
            is_header = False
            if elem_type == 'title':
                is_header = True
            # Fallback: check text patterns for section headers (for non-Title elements)
            elif self._is_section_header(text):
                is_header = True
            # Also check if text contains known section headers (even if not Title type)
            elif any(header in text.upper() for header in [
                'PATIENT IDENTIFICATION', 'ACTIVE MEDICAL ISSUES', 'PAST MEDICAL HISTORY',
                'RECONCILED ADMISSION MEDICATION LIST', 'ALLERGIES', 'SOCIAL HISTORY',
                'HISTORY OF PRESENTING ILLNESS', 'REVIEW OF SYSTEMS', 'PHYSICAL EXAMINATION',
                'INVESTIGATIONS', 'ASSESSMENT', 'REASON FOR REFERRAL'
            ]):
                is_header = True
            
            if is_header:
                current_section = self._normalize_section_name(text)
                if current_section not in sections:
                    sections[current_section] = []
                # Include the header element itself in the section
                sections[current_section].append(elem)
            elif current_section:
                sections[current_section].append(elem)
            else:
                # Content before first section - put in 'header' or 'unknown'
                if 'header' not in sections:
                    sections['header'] = []
                sections['header'].append(elem)
        
        return sections
    
    def _is_section_header(self, text: str) -> bool:
        """Check if text is a section header"""
        if not text:
            return False
        
        # Common section header patterns (all caps, ends with colon)
        header_patterns = [
            r'^[A-Z][A-Z\s]+:$',  # All caps with colon
            r'^[A-Z][A-Z\s]+\s*$',  # All caps line
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, text.strip()):
                return True
        
        # Check for known section headers
        known_headers = [
            'PATIENT IDENTIFICATION', 'ACTIVE MEDICAL ISSUES', 'PAST MEDICAL HISTORY',
            'RECONCILED ADMISSION MEDICATION LIST', 'ALLERGIES', 'SOCIAL HISTORY',
            'HISTORY OF PRESENTING ILLNESS', 'REVIEW OF SYSTEMS', 'PHYSICAL EXAMINATION',
            'INVESTIGATIONS', 'ASSESSMENT', 'REASON FOR REFERRAL'
        ]
        
        text_upper = text.upper().strip().rstrip(':')
        return any(header in text_upper for header in known_headers)
    
    def _normalize_section_name(self, text: str) -> str:
        """Normalize section name to standard format"""
        text = text.strip().rstrip(':').upper()
        
        # Map variations to standard names
        mappings = {
            'PATIENT IDENTIFICATION': 'patient_identification',
            'ACTIVE MEDICAL ISSUES': 'active_medical_issues',
            'PAST MEDICAL HISTORY': 'past_medical_history',
            'RECONCILED ADMISSION MEDICATION LIST': 'medications',
            'MEDICATION LIST': 'medications',
            'MEDICATIONS': 'medications',
            'ALLERGIES': 'allergies',
            'SOCIAL HISTORY': 'social_history',
            'HISTORY OF PRESENTING ILLNESS': 'history_presenting_illness',
            'REVIEW OF SYSTEMS': 'review_of_systems',
            'PHYSICAL EXAMINATION': 'physical_examination',
            'INVESTIGATIONS': 'investigations',
            'ASSESSMENT': 'assessment',
        }
        
        for key, value in mappings.items():
            if key in text:
                return value
        
        # Default: convert to lowercase with underscores
        return re.sub(r'[^\w\s]', '', text.lower().replace(' ', '_'))
    
    def _extract_patient_info_structured(
        self, 
        elements: List[Dict[str, Any]], 
        sections: Dict[str, List[Dict[str, Any]]], 
        full_text: str
    ) -> Dict[str, Any]:
        """Extract patient demographic information using structure-aware approach"""
        patient_info = {}
        
        # First, try to extract from PATIENT IDENTIFICATION section
        if 'patient_identification' in sections:
            section_text = self._combine_text(sections['patient_identification'])
            # Extract name from section
            name = self._extract_patient_name_from_identification(section_text)
            if name:
                patient_info['name'] = name
            
            # Extract age and gender together from "76-year-old woman"
            age_gender = self._extract_age_and_gender_from_text(section_text)
            if age_gender:
                patient_info.update(age_gender)
            
            # Extract MRN from section
            mrn = self._extract_mrn_from_section(section_text)
            if mrn:
                patient_info['mrn'] = mrn
        
        # Fallback to full text if section extraction didn't work
        if not patient_info.get('name'):
            for pattern in self.patient_name_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    patient_info['name'] = match.group(1).strip()
                    break
        
        if not patient_info.get('age'):
            for pattern in self.age_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    patient_info['age'] = match.group(1).strip()
                    break
        
        if not patient_info.get('gender'):
            gender = self._extract_gender_from_text(full_text)
            if gender:
                patient_info['gender'] = gender
        
        if not patient_info.get('mrn'):
            for pattern in self.mrn_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    patient_info['mrn'] = match.group(1).strip()
                    break
        
        # Extract date of birth
        for pattern in self.dob_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                patient_info['date_of_birth'] = match.group(1).strip()
                break
        
        return patient_info
    
    def _extract_patient_name_from_identification(self, text: str) -> Optional[str]:
        """Extract patient name from PATIENT IDENTIFICATION section"""
        # Pattern: "PATIENT IDENTIFICATION: Ms. J is a..."
        # Try to extract full name including title
        patterns = [
            # Full pattern: "PATIENT IDENTIFICATION: Ms. J is..."
            r'PATIENT\s+IDENTIFICATION[:\s]+(?:Ms\.|Mr\.|Mrs\.|Dr\.|Miss\.|Mx\.)\s+([A-Z][a-z]*(?:\s+[A-Z][a-z]*)?)',
            # Just title + name: "Ms. J is..."
            r'(?:Ms\.|Mr\.|Mrs\.|Dr\.|Miss\.)\s+([A-Z][a-z]*(?:\s+[A-Z][a-z]*)?)',
            # Without title: "PATIENT IDENTIFICATION: John Doe..."
            r'PATIENT\s+IDENTIFICATION[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Validate it's not just a single letter or common word
                if len(name) > 1 and name.lower() not in ['is', 'a', 'the', 'an', 'who', 'presented']:
                    # If it's just "J", try to get more context
                    if len(name) == 1:
                        # Look for "Ms. J" or "Mr. J" format
                        title_match = re.search(r'(Ms\.|Mr\.|Mrs\.|Dr\.)\s+([A-Z])', text, re.IGNORECASE)
                        if title_match:
                            return f"{title_match.group(1)} {title_match.group(2)}"
                    return name
        
        return None
    
    def _extract_age_and_gender_from_text(self, text: str) -> Optional[Dict[str, str]]:
        """Extract age and gender from text like '76-year-old woman'"""
        # Pattern: "76-year-old woman" or "76 years old man"
        patterns = [
            r'(\d+)[-]year[-]old\s+(man|woman|male|female)',
            r'(\d+)\s*years?\s*old\s+(man|woman|male|female)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = match.group(1).strip()
                gender_word = match.group(2).lower()
                
                # Normalize gender
                if gender_word in ['woman', 'female', 'f']:
                    gender = 'Female'
                elif gender_word in ['man', 'male', 'm']:
                    gender = 'Male'
                else:
                    gender = gender_word.capitalize()
                
                return {'age': age, 'gender': gender}
        
        return None
    
    def _extract_gender_from_text(self, text: str) -> Optional[str]:
        """Extract gender from text using multiple patterns"""
        # Check for title-based gender
        if re.search(r'\b(Ms\.|Mrs\.|Miss\.)', text, re.IGNORECASE):
            return 'Female'
        if re.search(r'\b(Mr\.)', text, re.IGNORECASE):
            return 'Male'
        
        # Check for explicit gender patterns
        for pattern in self.gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 1:
                    gender_word = match.group(2).lower()
                else:
                    gender_word = match.group(1).lower()
                
                if gender_word.startswith('m') and gender_word not in ['miss', 'ms', 'mrs']:
                    return 'Male'
                elif gender_word.startswith('f') or gender_word in ['woman', 'female']:
                    return 'Female'
        
        return None
    
    def _extract_mrn_from_section(self, text: str) -> Optional[str]:
        """Extract MRN from PATIENT IDENTIFICATION section"""
        for pattern in self.mrn_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_vital_signs(self, text: str) -> Dict[str, Any]:
        """Extract vital signs"""
        vitals = {}
        
        for vital_name, pattern in self.vital_signs_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vitals[vital_name] = match.group(1).strip()
        
        return vitals
    
    def _extract_diagnoses_structured(
        self,
        elements: List[Dict[str, Any]],
        sections: Dict[str, List[Dict[str, Any]]],
        full_text: str
    ) -> List[str]:
        """Extract diagnoses using structure-aware approach - prioritize ListItem elements"""
        diagnoses = []
        
        # First, try to extract from ACTIVE MEDICAL ISSUES section using ListItem elements
        if 'active_medical_issues' in sections:
            section_elements = sections['active_medical_issues']
            
            # Prioritize ListItem elements - these are structured list items from Unstructured.io
            for elem in section_elements:
                elem_type = elem.get('type', '').lower()
                text = elem.get('text', '').strip()
                
                if elem_type == 'listitem':
                    # ListItem elements are already structured - just clean them up
                    # Remove leading number and period if present
                    text = re.sub(r'^\d+\.\s*', '', text).strip().rstrip('.')
                    if text and len(text) > 3 and text not in diagnoses:
                        diagnoses.append(text)
                elif elem_type == 'narrativetext' or elem_type == 'text':
                    # Fallback: extract from narrative text using numbered list pattern
                    list_item_pattern = r'(\d+)\.\s+([^\.\n]+?)(?=\d+\.|$)'
                    matches = re.finditer(list_item_pattern, text, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        diagnosis = match.group(2).strip().rstrip('.')
                        if diagnosis and len(diagnosis) > 3 and diagnosis not in diagnoses:
                            diagnoses.append(diagnosis)
        
        # Fallback to full text patterns if no ListItem elements found
        if not diagnoses:
            for pattern in self.diagnosis_patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    diagnosis = match.group(1).strip()
                    if diagnosis and diagnosis not in diagnoses:
                        diagnoses.append(diagnosis)
        
        return diagnoses
    
    def _extract_diagnoses(self, text: str) -> List[str]:
        """Extract diagnoses (fallback method)"""
        diagnoses = []
        
        for pattern in self.diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                diagnosis = match.group(1).strip()
                if diagnosis and diagnosis not in diagnoses:
                    diagnoses.append(diagnosis)
        
        return diagnoses
    
    def _extract_medications_structured(
        self,
        elements: List[Dict[str, Any]],
        sections: Dict[str, List[Dict[str, Any]]],
        full_text: str
    ) -> List[Dict[str, str]]:
        """Extract medications using structure-aware approach - prioritize ListItem elements"""
        medications = []
        
        # First, try to extract from RECONCILED ADMISSION MEDICATION LIST section
        if 'medications' in sections:
            section_elements = sections['medications']
            
            # Prioritize ListItem elements - these are structured medication list items
            for elem in section_elements:
                elem_type = elem.get('type', '').lower()
                text = elem.get('text', '').strip()
                
                if elem_type == 'listitem':
                    # ListItem elements are structured - extract medication info
                    # Pattern: "1. Diltiazem 120 mg p.o. daily..." or "Diltiazem 120 mg"
                    med_match = re.search(
                        r'(?:^\d+\.\s*)?([A-Za-z\s-]+?)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g|units?|mcg|mcg)',
                        text,
                        re.IGNORECASE
                    )
                    if med_match:
                        med_name = med_match.group(1).strip()
                        dosage_value = med_match.group(2).strip()
                        dosage_unit = med_match.group(3).strip()
                        
                        med = {
                            'name': med_name,
                            'dosage': f"{dosage_value} {dosage_unit}"
                        }
                        
                        if med['name'] and med not in medications:
                            medications.append(med)
                elif elem_type in ['narrativetext', 'text']:
                    # Fallback: extract from narrative text using numbered list pattern
                    list_item_pattern = r'(\d+)\.\s+([A-Za-z\s-]+?)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g|units?|mcg)'
                    matches = re.finditer(list_item_pattern, text, re.IGNORECASE)
                    for match in matches:
                        med_name = match.group(2).strip()
                        dosage_value = match.group(3).strip()
                        dosage_unit = match.group(4).strip()
                        
                        med = {
                            'name': med_name,
                            'dosage': f"{dosage_value} {dosage_unit}"
                        }
                        
                        if med['name'] and med not in medications:
                            medications.append(med)
        
        # Fallback: Search in all sections if medications section not found
        if not medications:
            for section_name, section_elems in sections.items():
                if section_name not in ['patient_identification', 'allergies']:
                    # Look for ListItem elements that might be medications
                    for elem in section_elems:
                        if elem.get('type', '').lower() == 'listitem':
                            text = elem.get('text', '').strip()
                            med_match = re.search(
                                r'(?:^\d+\.\s*)?([A-Za-z\s-]+?)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g|units?|mcg)',
                                text,
                                re.IGNORECASE
                            )
                            if med_match:
                                med_name = med_match.group(1).strip()
                                dosage_value = med_match.group(2).strip()
                                dosage_unit = med_match.group(3).strip()
                                
                                med = {
                                    'name': med_name,
                                    'dosage': f"{dosage_value} {dosage_unit}"
                                }
                                
                                if med['name'] and med not in medications:
                                    medications.append(med)
        
        # Final fallback to full text patterns
        if not medications:
            medications = self._extract_medications(full_text)
        
        return medications
    
    def _extract_medications(self, text: str) -> List[Dict[str, str]]:
        """Extract medications (fallback method)"""
        medications = []
        
        for pattern in self.medication_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 1:
                    # Pattern with drug name and dosage
                    med = {
                        'name': match.group(1).strip(),
                        'dosage': f"{match.group(2)} {match.group(3)}"
                    }
                else:
                    # Simple medication name
                    med = {
                        'name': match.group(1).strip(),
                        'dosage': ''
                    }
                
                if med['name'] and med not in medications:
                    medications.append(med)
        
        return medications
    
    def _extract_allergies(self, text: str) -> List[str]:
        """Extract allergies"""
        allergies = []
        
        # Check for "no known allergies"
        if re.search(r'no\s+known\s+allergies', text, re.IGNORECASE):
            return ['No known allergies']
        
        for pattern in self.allergy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                allergy = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if allergy:
                    allergy = allergy.strip()
                    if allergy and allergy not in allergies:
                        allergies.append(allergy)
        
        return allergies
    
    def _extract_procedures(self, text: str) -> List[str]:
        """Extract procedures"""
        procedures = []
        
        for pattern in self.procedure_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                procedure = match.group(1).strip()
                if procedure and procedure not in procedures:
                    procedures.append(procedure)
        
        return procedures
    
    def _extract_clinical_notes(self, elements: List[Dict[str, Any]]) -> List[str]:
        """Extract clinical notes and observations - combine related elements"""
        notes = []
        
        # Look for sections that might contain clinical notes
        note_keywords = ['note', 'observation', 'assessment', 'plan', 'impression', 'history', 'examination']
        note_sections = ['history_presenting_illness', 'physical_examination', 'assessment', 'plan']
        
        # First, try to get notes from specific sections
        sections = self._identify_sections(elements)
        combined_note_texts = []
        
        for section_name in note_sections:
            if section_name in sections:
                section_text = self._combine_text(sections[section_name])
                if section_text.strip():
                    combined_note_texts.append(section_text.strip())
        
        # Also look for narrative text elements that are longer and contain note keywords
        current_note_parts = []
        for elem in elements:
            text = elem.get('text', '').strip()
            elem_type = elem.get('type', '').lower()
            
            # Include longer text blocks that might be notes
            if text and len(text) > 30:
                text_lower = text.lower()
                # Check if it's a note-like element (narrative text or contains keywords)
                if elem_type in ['narrativetext', 'text'] or any(keyword in text_lower for keyword in note_keywords):
                    # If this looks like a continuation of the previous note, combine it
                    if current_note_parts and not text_lower.startswith(('patient', 'she', 'he', 'they', 'we', 'the')):
                        # Likely continuation - add space and append
                        current_note_parts.append(' ' + text)
                    else:
                        # New note - save previous if exists, start new
                        if current_note_parts:
                            combined_note_texts.append(' '.join(current_note_parts))
                        current_note_parts = [text]
        
        # Add final note if exists
        if current_note_parts:
            combined_note_texts.append(' '.join(current_note_parts))
        
        # Combine all note texts into one continuous note
        if combined_note_texts:
            full_note = ' '.join(combined_note_texts)
            # Clean up extra whitespace
            full_note = ' '.join(full_note.split())
            notes.append(full_note)
        
        return notes
