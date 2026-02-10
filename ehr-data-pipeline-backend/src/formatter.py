"""Formatter module to convert structured data to discharge document format"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import os


class DischargeFormatter:
    """Format structured clinical data for discharge documents"""
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the formatter
        
        Args:
            template_path: Path to custom discharge template file
        """
        self.template_path = template_path
        self.default_template = self._get_default_template()
    
    def format(self, data: Dict[str, Any], use_template: bool = True) -> str:
        """
        Format structured data into discharge document text
        
        Args:
            data: Dictionary containing extracted clinical data
            use_template: If True, use template. If False, use simple formatting.
            
        Returns:
            Formatted discharge document text
        """
        if use_template and self.template_path and os.path.exists(self.template_path):
            return self._format_with_template(data, self.template_path)
        elif use_template:
            return self._format_with_template(data, None)  # Use default template
        else:
            return self._format_simple(data)
    
    def _format_with_template(self, data: Dict[str, Any], template_path: Optional[str]) -> str:
        """Format using a template file"""
        if template_path:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            template = self.default_template
        
        # Replace template placeholders with actual data
        formatted = template
        
        # Patient information - handle None values explicitly
        patient_info = data.get('patient_info', {})
        # Helper function to safely get values, handling None
        def safe_get(d, key, default='N/A'):
            value = d.get(key, default)
            return default if value is None or (isinstance(value, str) and not value.strip()) else str(value)
        
        formatted = formatted.replace('{patient_name}', safe_get(patient_info, 'name'))
        formatted = formatted.replace('{date_of_birth}', safe_get(patient_info, 'date_of_birth'))
        formatted = formatted.replace('{mrn}', safe_get(patient_info, 'mrn'))
        formatted = formatted.replace('{age}', safe_get(patient_info, 'age'))
        formatted = formatted.replace('{gender}', safe_get(patient_info, 'gender'))
        
        # Vital signs
        vitals = data.get('vital_signs', {})
        vitals_text = self._format_vitals(vitals)
        formatted = formatted.replace('{vital_signs}', vitals_text)
        
        # Diagnoses
        diagnoses = data.get('diagnoses', [])
        diagnoses_text = self._format_list(diagnoses, 'No diagnoses recorded')
        formatted = formatted.replace('{diagnoses}', diagnoses_text)
        
        # Medications
        medications = data.get('medications', [])
        medications_text = self._format_medications(medications)
        formatted = formatted.replace('{medications}', medications_text)
        
        # Allergies
        allergies = data.get('allergies', [])
        allergies_text = self._format_list(allergies, 'No known allergies')
        formatted = formatted.replace('{allergies}', allergies_text)
        
        # Procedures
        procedures = data.get('procedures', [])
        procedures_text = self._format_list(procedures, 'No procedures recorded')
        formatted = formatted.replace('{procedures}', procedures_text)
        
        # Clinical notes
        notes = data.get('clinical_notes', [])
        notes_text = self._format_notes(notes)
        formatted = formatted.replace('{clinical_notes}', notes_text)
        
        # Date
        formatted = formatted.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
        
        return formatted
    
    def _format_simple(self, data: Dict[str, Any]) -> str:
        """Format data in a simple structured format"""
        lines = []
        lines.append("=" * 60)
        lines.append("DISCHARGE SUMMARY")
        lines.append("=" * 60)
        lines.append("")
        
        # Patient Information
        patient_info = data.get('patient_info', {})
        lines.append("PATIENT INFORMATION:")
        lines.append(f"  Name: {patient_info.get('name', 'N/A')}")
        lines.append(f"  Date of Birth: {patient_info.get('date_of_birth', 'N/A')}")
        lines.append(f"  MRN: {patient_info.get('mrn', 'N/A')}")
        lines.append(f"  Age: {patient_info.get('age', 'N/A')}")
        lines.append(f"  Gender: {patient_info.get('gender', 'N/A')}")
        lines.append("")
        
        # Vital Signs
        vitals = data.get('vital_signs', {})
        if vitals:
            lines.append("VITAL SIGNS:")
            for key, value in vitals.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # Diagnoses
        diagnoses = data.get('diagnoses', [])
        if diagnoses:
            lines.append("DIAGNOSES:")
            for i, diagnosis in enumerate(diagnoses, 1):
                lines.append(f"  {i}. {diagnosis}")
            lines.append("")
        
        # Medications
        medications = data.get('medications', [])
        if medications:
            lines.append("MEDICATIONS:")
            for i, med in enumerate(medications, 1):
                med_text = med.get('name', '')
                if med.get('dosage'):
                    med_text += f" - {med['dosage']}"
                lines.append(f"  {i}. {med_text}")
            lines.append("")
        
        # Allergies
        allergies = data.get('allergies', [])
        if allergies:
            lines.append("ALLERGIES:")
            for allergy in allergies:
                lines.append(f"  - {allergy}")
            lines.append("")
        
        # Procedures
        procedures = data.get('procedures', [])
        if procedures:
            lines.append("PROCEDURES:")
            for i, procedure in enumerate(procedures, 1):
                lines.append(f"  {i}. {procedure}")
            lines.append("")
        
        # Clinical Notes
        notes = data.get('clinical_notes', [])
        if notes:
            lines.append("CLINICAL NOTES:")
            for note in notes:
                lines.append(f"  {note}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(lines)
    
    def _format_vitals(self, vitals: Dict[str, str]) -> str:
        """Format vital signs"""
        if not vitals:
            return "No vital signs recorded"
        
        lines = []
        for key, value in vitals.items():
            label = key.replace('_', ' ').title()
            lines.append(f"  {label}: {value}")
        
        return '\n'.join(lines)
    
    def _format_medications(self, medications: List[Dict[str, str]]) -> str:
        """Format medications"""
        if not medications:
            return "No medications recorded"
        
        lines = []
        for i, med in enumerate(medications, 1):
            med_text = med.get('name', '')
            if med.get('dosage'):
                med_text += f" - {med['dosage']}"
            lines.append(f"  {i}. {med_text}")
        
        return '\n'.join(lines)
    
    def _format_list(self, items: List[str], empty_message: str) -> str:
        """Format a simple list"""
        if not items:
            return empty_message
        
        lines = []
        for i, item in enumerate(items, 1):
            lines.append(f"  {i}. {item}")
        
        return '\n'.join(lines)
    
    def _format_notes(self, notes: List[str]) -> str:
        """Format clinical notes"""
        if not notes:
            return "No clinical notes recorded"
        
        return '\n\n'.join([f"  {note}" for note in notes])
    
    def _get_default_template(self) -> str:
        """Get the default discharge document template"""
        return """DISCHARGE SUMMARY
Date: {date}

PATIENT INFORMATION:
  Name: {patient_name}
  Date of Birth: {date_of_birth}
  MRN: {mrn}
  Age: {age}
  Gender: {gender}

VITAL SIGNS:
{vital_signs}

DIAGNOSES:
{diagnoses}

MEDICATIONS:
{medications}

ALLERGIES:
{allergies}

PROCEDURES:
{procedures}

CLINICAL NOTES:
{clinical_notes}

---
Generated on: {date}
"""
