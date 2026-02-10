"""Streamlit application for EHR Data Pipeline Demo"""

import streamlit as st
import pandas as pd
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Defer imports to avoid event loop issues with torch/unstructured
# Import modules only when needed, not at module level
def _lazy_imports():
    """Lazy import modules to avoid event loop issues"""
    from src.pdf_processor import PDFProcessor
    from src.data_extractor import DataExtractor
    from src.formatter import DischargeFormatter
    from src.section_editor import SectionEditor
    return PDFProcessor, DataExtractor, DischargeFormatter, SectionEditor

from src.utils import save_json, load_json, sanitize_filename

# Page configuration
st.set_page_config(
    page_title="EHR Data Pipeline Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = {}
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}


def process_uploaded_pdfs(uploaded_files: List) -> Dict[str, Any]:
    """Process uploaded PDF files"""
    PDFProcessor, DataExtractor, _, _ = _lazy_imports()
    processor = PDFProcessor(use_api=True)
    extractor = DataExtractor()
    
    results = {}
    
    for uploaded_file in uploaded_files:
        try:
            # Save uploaded file temporarily
            temp_path = os.path.join("data/samples", uploaded_file.name)
            os.makedirs("data/samples", exist_ok=True)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process PDF
            elements = processor.process_pdf(temp_path)
            
            # Get selected sections from session state if available
            selected_sections = None
            doc_key = f"{uploaded_file.name}_selected_sections"
            if doc_key in st.session_state:
                selected_sections = list(st.session_state[doc_key])
            
            # Extract structured data
            extracted = extractor.extract(elements, selected_sections=selected_sections)
            
            results[uploaded_file.name] = {
                'elements': elements,
                'extracted_data': extracted,
                'file_path': temp_path
            }
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    return results


def display_patient_info(data: Dict[str, Any]):
    """Display patient information section"""
    patient_info = data.get('patient_info', {})
    
    if patient_info:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Name", patient_info.get('name', 'N/A'))
        with col2:
            st.metric("MRN", patient_info.get('mrn', 'N/A'))
        with col3:
            st.metric("Age", patient_info.get('age', 'N/A'))
        with col4:
            st.metric("Gender", patient_info.get('gender', 'N/A'))
        
        if patient_info.get('date_of_birth'):
            st.caption(f"Date of Birth: {patient_info.get('date_of_birth')}")


def display_vital_signs(vitals: Dict[str, Any]):
    """Display vital signs"""
    if vitals:
        st.subheader("Vital Signs")
        cols = st.columns(len(vitals))
        
        for idx, (key, value) in enumerate(vitals.items()):
            with cols[idx]:
                label = key.replace('_', ' ').title()
                st.metric(label, value)
    else:
        st.info("No vital signs recorded")


def display_diagnoses(diagnoses: List[str]):
    """Display diagnoses"""
    st.subheader("Diagnoses")
    if diagnoses:
        for i, diagnosis in enumerate(diagnoses, 1):
            st.write(f"{i}. {diagnosis}")
    else:
        st.info("No diagnoses recorded")


def display_medications(medications: List[Dict[str, str]]):
    """Display medications"""
    st.subheader("Medications")
    if medications:
        df = pd.DataFrame(medications)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No medications recorded")


def display_allergies(allergies: List[str]):
    """Display allergies"""
    st.subheader("Allergies")
    if allergies:
        for allergy in allergies:
            st.warning(f"⚠️ {allergy}")
    else:
        st.success("No known allergies")


def display_procedures(procedures: List[str]):
    """Display procedures"""
    st.subheader("Procedures")
    if procedures:
        for i, procedure in enumerate(procedures, 1):
            st.write(f"{i}. {procedure}")
    else:
        st.info("No procedures recorded")


def display_clinical_notes(notes: List[str]):
    """Display clinical notes - combine fragmented notes into continuous text"""
    st.subheader("Clinical Notes")
    if notes:
        # Combine all notes into one continuous text, handling fragmentation
        combined_text = []
        for note in notes:
            note_clean = note.strip()
            if note_clean:
                combined_text.append(note_clean)
        
        # Join notes with proper spacing
        full_text = ' '.join(combined_text)
        
        # Display as a single continuous text area
        st.text_area(
            "", 
            value=full_text, 
            height=400, 
            disabled=True, 
            key="clinical_notes_combined",
            help="Combined clinical notes from all document sections"
        )
    else:
        st.info("No clinical notes recorded")


def main():
    """Main application"""
    st.title("🏥 EHR Data Pipeline Demo")
    st.markdown("Extract and consolidate patient data from admission notes using Unstructured.io")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        use_api = st.radio(
            "Processing Method",
            ["API (Cloud)", "Local Library"],
            help="Choose between Unstructured.io API or local processing"
        )
        
        # LLM Extraction toggle
        use_llm = st.checkbox(
            "Use LLM Extraction",
            value=False,
            help="Use LLM (OpenAI) for intelligent extraction instead of regex patterns. Requires OPENAI_API_KEY in .env file."
        )
        
        st.divider()
        
        st.header("Instructions")
        st.markdown("""
        1. Upload one or more PDF admission notes
        2. Wait for processing to complete
        3. Review extracted data in the dashboard
        4. Use search to find specific information
        5. Export data as JSON or formatted discharge document
        """)
        
        st.divider()
        
        # Clear button
        if st.button("Clear All Data", type="secondary"):
            st.session_state.processed_documents = {}
            st.session_state.extracted_data = {}
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 Upload & Process", 
        "📊 Dashboard", 
        "🔍 Search", 
        "📥 Export", 
        "🤖 LLM Report Generator",
        "✏️ Section Editor"
    ])
    
    # Tab 1: Upload & Process
    with tab1:
        st.header("Upload PDF Files")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload patient admission note PDFs"
        )
        
        if uploaded_files:
            if st.button("Process PDFs", type="primary"):
                with st.spinner("Processing PDFs... This may take a moment."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = {}
                    total_files = len(uploaded_files)
                    
                    try:
                        PDFProcessor, DataExtractor, _, _ = _lazy_imports()
                        processor = PDFProcessor(use_api=(use_api == "API (Cloud)"))
                        extractor = DataExtractor(use_llm=use_llm)
                        
                        for idx, uploaded_file in enumerate(uploaded_files):
                            status_text.text(f"Processing {uploaded_file.name} ({idx + 1}/{total_files})...")
                            
                            # Save uploaded file temporarily
                            temp_path = os.path.join("data/samples", uploaded_file.name)
                            os.makedirs("data/samples", exist_ok=True)
                            
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            try:
                                # Process PDF
                                elements = processor.process_pdf(temp_path)
                                
                                # Get selected sections from session state if available
                                selected_sections = None
                                if uploaded_file.name in st.session_state.get('selected_sections_by_doc', {}):
                                    selected_sections = list(st.session_state.selected_sections_by_doc[uploaded_file.name])
                                
                                # If LLM extraction is enabled, extract and cache LLM data separately
                                llm_extracted_data = None
                                if use_llm and extractor.use_llm and extractor.llm_extractor:
                                    try:
                                        # Identify sections once
                                        sections = extractor._identify_sections(elements)
                                        # Run LLM extraction and cache the raw results
                                        llm_extracted_data = extractor.llm_extractor.extract_from_sections(
                                            sections, 
                                            selected_sections,
                                            document_name=uploaded_file.name
                                        )
                                        logger.info(f"Cached LLM extraction results for {uploaded_file.name}")
                                    except Exception as e:
                                        logger.warning(f"Failed to cache LLM data for {uploaded_file.name}: {str(e)}")
                                        llm_extracted_data = None
                                
                                # Extract structured data (this will use LLM if available, or fall back to regex)
                                extracted = extractor.extract(elements, selected_sections=selected_sections)
                                
                                results[uploaded_file.name] = {
                                    'elements': elements,
                                    'extracted_data': extracted,  # Merged LLM + regex fallback
                                    'llm_extracted_data': llm_extracted_data,  # Raw LLM-only data
                                    'file_path': temp_path
                                }
                                
                            except RuntimeError as e:
                                # Check if it's a poppler error
                                if "poppler" in str(e).lower():
                                    st.error(f"**Poppler Error**: {str(e)}")
                                    st.info("💡 **Tip**: Switch to 'API (Cloud)' mode in the sidebar to avoid needing Poppler!")
                                else:
                                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                                logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                                logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
                            
                            progress_bar.progress((idx + 1) / total_files)
                        
                        # Store in session state
                        st.session_state.processed_documents.update(results)
                        for filename, data in results.items():
                            st.session_state.extracted_data[filename] = data['extracted_data']
                        
                        status_text.text("Processing complete!")
                        st.success(f"Successfully processed {len(results)} file(s)")
                        
                    except Exception as e:
                        st.error(f"Error during processing: {str(e)}")
                        logger.error(f"Error during processing: {str(e)}")
    
    # Tab 2: Dashboard
    with tab2:
        st.header("Data Dashboard")
        
        if not st.session_state.extracted_data:
            st.info("No data available. Please upload and process PDF files first.")
        else:
            # Document selector
            selected_doc = st.selectbox(
                "Select Document",
                list(st.session_state.extracted_data.keys())
            )
            
            if selected_doc:
                data = st.session_state.extracted_data[selected_doc]
                
                # Patient Information
                st.divider()
                display_patient_info(data)
                
                # Vital Signs
                st.divider()
                display_vital_signs(data.get('vital_signs', {}))
                
                # Diagnoses
                st.divider()
                display_diagnoses(data.get('diagnoses', []))
                
                # Medications
                st.divider()
                display_medications(data.get('medications', []))
                
                # Allergies
                st.divider()
                display_allergies(data.get('allergies', []))
                
                # Procedures
                st.divider()
                display_procedures(data.get('procedures', []))
                
                # Clinical Notes
                st.divider()
                display_clinical_notes(data.get('clinical_notes', []))
    
    # Tab 3: Search
    with tab3:
        st.header("🔍 Search Across All Documents")
        st.markdown("Search for specific terms across all processed admission notes. Find patients by condition, medication, symptom, or any keyword.")
        
        if not st.session_state.extracted_data:
            st.info("No data available. Please upload and process PDF files first.")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_query = st.text_input(
                    "Search query", 
                    placeholder="e.g., 'pneumonia', 'metoprolol', 'allergy', 'hypertension'...",
                    help="Search across all documents for any term"
                )
            
            with col2:
                search_in = st.selectbox(
                    "Search in",
                    ["All Fields", "Diagnoses", "Medications", "Allergies", "Clinical Notes", "Patient Info"],
                    help="Filter search to specific sections"
                )
            
            if search_query:
                results = []
                search_lower = search_query.lower()
                
                for filename, data in st.session_state.extracted_data.items():
                    matches = []
                    match_count = 0
                    raw_text_matches = []
                    
                    # Search in structured extracted data
                    if search_in == "All Fields" or search_in == "Diagnoses":
                        diagnoses = data.get('diagnoses', [])
                        for diag in diagnoses:
                            if search_lower in diag.lower():
                                matches.append(f"Diagnosis: {diag}")
                                match_count += diag.lower().count(search_lower)
                    
                    if search_in == "All Fields" or search_in == "Medications":
                        medications = data.get('medications', [])
                        for med in medications:
                            med_text = f"{med.get('name', '')} {med.get('dosage', '')}".lower()
                            if search_lower in med_text:
                                matches.append(f"Medication: {med.get('name', '')} {med.get('dosage', '')}")
                                match_count += med_text.count(search_lower)
                    
                    if search_in == "All Fields" or search_in == "Allergies":
                        allergies = data.get('allergies', [])
                        for allergy in allergies:
                            if search_lower in allergy.lower():
                                matches.append(f"Allergy: {allergy}")
                                match_count += allergy.lower().count(search_lower)
                    
                    if search_in == "All Fields" or search_in == "Clinical Notes":
                        notes = data.get('clinical_notes', [])
                        for note in notes:
                            if search_lower in note.lower():
                                # Extract context around match
                                note_lower = note.lower()
                                idx = note_lower.find(search_lower)
                                start = max(0, idx - 50)
                                end = min(len(note), idx + len(search_query) + 50)
                                context = note[start:end]
                                matches.append(f"Note: ...{context}...")
                                match_count += note_lower.count(search_lower)
                    
                    if search_in == "All Fields" or search_in == "Patient Info":
                        patient_info = data.get('patient_info', {})
                        patient_text = json.dumps(patient_info).lower()
                        if search_lower in patient_text:
                            matches.append("Patient Information")
                            match_count += patient_text.count(search_lower)
                    
                    # Also search in vital signs and procedures
                    if search_in == "All Fields":
                        vitals = json.dumps(data.get('vital_signs', {})).lower()
                        if search_lower in vitals:
                            match_count += vitals.count(search_lower)
                        
                        procedures = data.get('procedures', [])
                        for proc in procedures:
                            if search_lower in proc.lower():
                                matches.append(f"Procedure: {proc}")
                                match_count += proc.lower().count(search_lower)
                    
                    # Search in raw document elements (fallback/comprehensive search)
                    # This ensures we find terms even if extraction missed them
                    if filename in st.session_state.processed_documents:
                        raw_elements = st.session_state.processed_documents[filename].get('elements', [])
                        for element in raw_elements:
                            element_text = element.get('text', '')
                            if element_text and search_lower in element_text.lower():
                                # Count matches in this element
                                element_matches = element_text.lower().count(search_lower)
                                match_count += element_matches
                                
                                # Extract context around first match
                                element_lower = element_text.lower()
                                idx = element_lower.find(search_lower)
                                if idx != -1:
                                    start = max(0, idx - 80)
                                    end = min(len(element_text), idx + len(search_query) + 80)
                                    context = element_text[start:end]
                                    
                                    # Clean up context (remove extra whitespace)
                                    context = ' '.join(context.split())
                                    
                                    # Only add if we haven't found it in structured data already
                                    # or if search_in is "All Fields" (show both)
                                    if search_in == "All Fields" or match_count == element_matches:
                                        element_type = element.get('type', 'Text')
                                        raw_text_matches.append(f"Raw Text ({element_type}): ...{context}...")
                    
                    # Combine structured and raw matches
                    all_matches = matches + raw_text_matches[:3]  # Limit raw matches to avoid clutter
                    
                    if match_count > 0:
                        patient_info = data.get('patient_info', {})
                        results.append({
                            'Document': filename,
                            'Patient Name': patient_info.get('name', 'N/A'),
                            'Age': patient_info.get('age', 'N/A'),
                            'MRN': patient_info.get('mrn', 'N/A'),
                            'Matches Found': match_count,
                            'Match Details': ' | '.join(all_matches[:3]) + ('...' if len(all_matches) > 3 else '')
                        })
                
                if results:
                    st.success(f"Found {len(results)} document(s) containing '{search_query}'")
                    
                    # Sort by match count (most matches first)
                    results_df = pd.DataFrame(results)
                    results_df = results_df.sort_values('Matches Found', ascending=False)
                    
                    st.dataframe(
                        results_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Match Details": st.column_config.TextColumn(
                                "Where Found",
                                width="large",
                                help="Shows where the search term was found"
                            )
                        }
                    )
                    
                    st.divider()
                    st.subheader("View Full Document Details")
                    
                    # Show details for selected document
                    selected = st.selectbox(
                        "Select document to view full details",
                        results_df['Document'].tolist(),
                        key="search_doc_selector"
                    )
                    
                    if selected:
                        st.divider()
                        selected_data = st.session_state.extracted_data[selected]
                        
                        # Show patient info first
                        display_patient_info(selected_data)
                        
                        # Highlight matches in context
                        st.subheader("🔍 Search Matches in Context")
                        for section_name, section_data in [
                            ("Diagnoses", selected_data.get('diagnoses', [])),
                            ("Medications", selected_data.get('medications', [])),
                            ("Allergies", selected_data.get('allergies', [])),
                            ("Procedures", selected_data.get('procedures', [])),
                        ]:
                            if section_data:
                                matching_items = [
                                    item for item in section_data 
                                    if search_lower in str(item).lower()
                                ]
                                if matching_items:
                                    st.write(f"**{section_name}:**")
                                    for item in matching_items:
                                        if isinstance(item, dict):
                                            item_str = f"{item.get('name', '')} {item.get('dosage', '')}"
                                        else:
                                            item_str = str(item)
                                        # Highlight the search term
                                        highlighted = item_str.replace(
                                            search_query,
                                            f"**{search_query}**"
                                        )
                                        st.write(f"  • {highlighted}")
                        
                        # Show clinical notes with matches
                        notes = selected_data.get('clinical_notes', [])
                        matching_notes = [
                            note for note in notes 
                            if search_lower in note.lower()
                        ]
                        if matching_notes:
                            st.write("**Clinical Notes (containing search term):**")
                            for idx, note in enumerate(matching_notes):
                                # Find and highlight matches
                                note_lower = note.lower()
                                highlighted_note = note
                                # Simple highlighting - find all occurrences
                                start = 0
                                while True:
                                    match_idx = note_lower.find(search_lower, start)
                                    if match_idx == -1:
                                        break
                                    highlighted_note = (
                                        highlighted_note[:match_idx] +
                                        f"**{note[match_idx:match_idx+len(search_query)]}**" +
                                        highlighted_note[match_idx+len(search_query):]
                                    )
                                    note_lower = highlighted_note.lower()
                                    start = match_idx + len(search_query) + 4  # Account for **
                                st.text_area("", value=highlighted_note, height=150, disabled=True, key=f"note_{selected}_{idx}_{hash(note)}")
                        
                        # Show raw document text matches if found
                        if selected in st.session_state.processed_documents:
                            raw_elements = st.session_state.processed_documents[selected].get('elements', [])
                            matching_elements = [
                                elem for elem in raw_elements
                                if elem.get('text', '') and search_lower in elem.get('text', '').lower()
                            ]
                            
                            if matching_elements and (search_in == "All Fields" or len(matching_notes) == 0):
                                st.subheader("📄 Raw Document Text Matches")
                                st.info("These matches were found in the original document text but may not have been extracted into structured fields.")
                                
                                for idx, elem in enumerate(matching_elements[:5]):  # Limit to 5 to avoid clutter
                                    elem_text = elem.get('text', '')
                                    elem_type = elem.get('type', 'Text')
                                    
                                    # Highlight the search term
                                    highlighted_text = elem_text
                                    elem_lower = elem_text.lower()
                                    start_pos = 0
                                    while True:
                                        idx_pos = elem_lower.find(search_lower, start_pos)
                                        if idx_pos == -1:
                                            break
                                        highlighted_text = (
                                            highlighted_text[:idx_pos] +
                                            f"**{elem_text[idx_pos:idx_pos+len(search_query)]}**" +
                                            highlighted_text[idx_pos+len(search_query):]
                                        )
                                        elem_lower = highlighted_text.lower()
                                        start_pos = idx_pos + len(search_query) + 4
                                    
                                    st.write(f"**{elem_type}:**")
                                    st.text_area("", value=highlighted_text, height=100, disabled=True, key=f"raw_{selected}_{idx}_{hash(elem_text)}")
                else:
                    st.warning(f"No documents found containing '{search_query}'")
                    st.info("💡 **Tips:**\n- Try different spellings or partial words\n- Search is case-insensitive\n- Try searching in specific sections using the dropdown")
    
    # Tab 4: Export
    with tab4:
        st.header("Export Data")
        
        if not st.session_state.extracted_data:
            st.info("No data available. Please upload and process PDF files first.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Export as JSON")
                selected_doc_json = st.selectbox(
                    "Select Document",
                    list(st.session_state.extracted_data.keys()),
                    key="export_json"
                )
                
                if selected_doc_json:
                    json_data = st.session_state.extracted_data[selected_doc_json]
                    json_str = json.dumps(json_data, indent=2)
                    
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"{sanitize_filename(selected_doc_json)}_data.json",
                        mime="application/json"
                    )
                    
                    st.code(json_str, language="json")
            
            with col2:
                st.subheader("Export as Discharge Document")
                selected_doc_discharge = st.selectbox(
                    "Select Document",
                    list(st.session_state.extracted_data.keys()),
                    key="export_discharge"
                )
                
                if selected_doc_discharge:
                    _, _, DischargeFormatter, _ = _lazy_imports()
                    formatter = DischargeFormatter()
                    discharge_text = formatter.format(
                        st.session_state.extracted_data[selected_doc_discharge]
                    )
                    
                    st.download_button(
                        label="Download Discharge Document",
                        data=discharge_text,
                        file_name=f"{sanitize_filename(selected_doc_discharge)}_discharge.txt",
                        mime="text/plain"
                    )
                    
                    st.text_area("Preview", value=discharge_text, height=400, disabled=True)
            
            # Export all documents
            st.divider()
            st.subheader("Export All Documents")
            
            if st.button("Export All as JSON"):
                all_data = {
                    'documents': st.session_state.extracted_data,
                    'metadata': {
                        'total_documents': len(st.session_state.extracted_data),
                        'export_date': pd.Timestamp.now().isoformat()
                    }
                }
                json_str = json.dumps(all_data, indent=2)
                
                st.download_button(
                        label="Download All Data (JSON)",
                        data=json_str,
                        file_name="all_patient_data.json",
                        mime="application/json"
                    )
    
    # Tab 5: LLM Report Generator
    with tab5:
        st.header("🤖 LLM Extraction Viewer & Report Builder")
        st.markdown("View LLM extraction results, select items, and build your output document")
        
        if not st.session_state.processed_documents:
            st.info("No data available. Please upload and process PDF files first.")
        elif not use_llm:
            st.warning("⚠️ LLM Extraction is disabled. Enable it in the sidebar to use this feature.")
        else:
            # Document selector
            selected_doc = st.selectbox(
                "Select Document",
                list(st.session_state.processed_documents.keys()),
                key="llm_report_doc"
            )
            
            if selected_doc:
                doc_data = st.session_state.processed_documents[selected_doc]
                elements = doc_data.get('elements', [])
                
                if elements:
                    # Initialize session state for selections and report
                    report_key = f"llm_report_{selected_doc}"
                    selections_key = f"llm_selections_{selected_doc}"
                    
                    if report_key not in st.session_state:
                        st.session_state[report_key] = ""
                    if selections_key not in st.session_state:
                        st.session_state[selections_key] = {
                            'patient_info': {},
                            'diagnoses': [],
                            'medications': [],
                            'allergies': [],
                            'vital_signs': {},
                            'clinical_notes': []
                        }
                    
                    # Check if LLM data is already cached from initial processing
                    llm_data = doc_data.get('llm_extracted_data')
                    extraction_status = "pending"
                    
                    # Check if we have valid cached LLM data (not None and not empty dict)
                    if llm_data is not None and llm_data != {}:
                        # Use cached LLM data - no API calls needed!
                        extraction_status = "cached"
                        # Show info message only once, not on every interaction
                        if f"llm_cache_info_shown_{selected_doc}" not in st.session_state:
                            st.info("ℹ️ Using cached LLM extraction results from initial processing")
                            st.session_state[f"llm_cache_info_shown_{selected_doc}"] = True
                    elif llm_data == {}:
                        # LLM data was cached but is empty - this means LLM extraction ran but found nothing
                        # Still use it, but mark as cached with empty results
                        extraction_status = "cached_empty"
                    else:
                        # LLM data not cached - this shouldn't happen if processing was done correctly
                        # But handle gracefully: try to extract now (only if LLM is enabled)
                        if use_llm:
                            _, DataExtractor, _, _ = _lazy_imports()
                            extractor = DataExtractor(use_llm=True)
                            sections = extractor._identify_sections(elements)
                            
                            if extractor.use_llm and extractor.llm_extractor:
                                try:
                                    with st.spinner("Extracting data with LLM... This may take a moment."):
                                        llm_data = extractor.llm_extractor.extract_from_sections(
                                            sections,
                                            document_name=selected_doc
                                        )
                                    extraction_status = "success"
                                    # Cache the results for future use
                                    doc_data['llm_extracted_data'] = llm_data
                                    st.session_state.processed_documents[selected_doc] = doc_data
                                    st.success("✅ LLM extraction completed successfully!")
                                except Exception as e:
                                    extraction_status = "failed"
                                    st.warning(f"⚠️ LLM extraction failed: {str(e)}. Using regex extraction instead.")
                                    # Fallback: use the merged extracted_data from initial processing
                                    llm_data = doc_data.get('extracted_data', {})
                        else:
                            # LLM not enabled - use the merged extracted_data from initial processing
                            llm_data = doc_data.get('extracted_data', {})
                            extraction_status = "regex"
                    
                    # Use LLM data for display if we have cached LLM data (even if empty)
                    # Only fallback to extracted_data if LLM data was never cached
                    if extraction_status in ['cached', 'cached_empty', 'success']:
                        display_data = llm_data if llm_data else {}
                    else:
                        # Fallback to merged extracted_data if LLM wasn't used or failed
                        display_data = doc_data.get('extracted_data', {})
                    
                    # Side-by-side layout
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("📋 LLM Extraction Results")
                        # Determine source label based on extraction status
                        if extraction_status == 'cached' or extraction_status == 'cached_empty' or extraction_status == 'success':
                            if extraction_status == 'cached':
                                source_label = "LLM (cached)"
                            elif extraction_status == 'cached_empty':
                                source_label = "LLM (cached, empty results)"
                            else:
                                source_label = "LLM"
                        elif extraction_status == 'failed':
                            source_label = "Regex (LLM failed)"
                        elif extraction_status == 'regex':
                            source_label = "Regex"
                        else:
                            source_label = "Unknown"
                        st.caption(f"Source: {source_label}")
                        
                        # Patient Information Section
                        with st.expander("👤 Patient Information", expanded=True):
                            patient_info = display_data.get('patient_info', {})
                            if patient_info:
                                # Initialize patient info selections
                                if 'patient_info_selected' not in st.session_state[selections_key]:
                                    st.session_state[selections_key]['patient_info_selected'] = {}
                                
                                selected_patient_fields = {}
                                for field, value in patient_info.items():
                                    if value:  # Only show non-empty fields
                                        checkbox_key = f"patient_{field}_{selected_doc}"
                                        if st.checkbox(
                                            f"**{field.replace('_', ' ').title()}**: {value}",
                                            value=st.session_state[selections_key]['patient_info_selected'].get(field, False),
                                            key=checkbox_key
                                        ):
                                            selected_patient_fields[field] = value
                                
                                st.session_state[selections_key]['patient_info_selected'] = selected_patient_fields
                                
                                # Add selected patient info button
                                if st.button("➕ Add Selected Patient Info", key=f"add_patient_{selected_doc}"):
                                    if selected_patient_fields:
                                        patient_text = "**PATIENT INFORMATION**\n\n"
                                        for field, value in selected_patient_fields.items():
                                            patient_text += f"{field.replace('_', ' ').title()}: {value}\n"
                                        patient_text += "\n"
                                        st.session_state[report_key] += patient_text
                                        st.success("Added patient information to document!")
                                        st.rerun()
                            else:
                                st.info("No patient information extracted")
                        
                        # Diagnoses Section
                        with st.expander("🩺 Diagnoses", expanded=True):
                            diagnoses = display_data.get('diagnoses', [])
                            if diagnoses:
                                # Initialize diagnoses selections
                                if 'diagnoses_selected' not in st.session_state[selections_key]:
                                    st.session_state[selections_key]['diagnoses_selected'] = []
                                
                                selected_diagnoses = []
                                for idx, diag in enumerate(diagnoses):
                                    checkbox_key = f"diag_{idx}_{selected_doc}"
                                    is_selected = diag in st.session_state[selections_key]['diagnoses_selected']
                                    if st.checkbox(
                                        diag,
                                        value=is_selected,
                                        key=checkbox_key
                                    ):
                                        selected_diagnoses.append(diag)
                                
                                st.session_state[selections_key]['diagnoses_selected'] = selected_diagnoses
                                
                                # Select All / Deselect All buttons
                                col_sel1, col_sel2 = st.columns(2)
                                with col_sel1:
                                    if st.button("✓ Select All", key=f"select_all_diag_{selected_doc}"):
                                        st.session_state[selections_key]['diagnoses_selected'] = diagnoses.copy()
                                        st.rerun()
                                with col_sel2:
                                    if st.button("✗ Deselect All", key=f"deselect_all_diag_{selected_doc}"):
                                        st.session_state[selections_key]['diagnoses_selected'] = []
                                        st.rerun()
                                
                                # Add selected diagnoses button
                                if st.button("➕ Add Selected Diagnoses", key=f"add_diag_{selected_doc}"):
                                    if selected_diagnoses:
                                        diag_text = "**DIAGNOSES**\n\n"
                                        for diag in selected_diagnoses:
                                            diag_text += f"- {diag}\n"
                                        diag_text += "\n"
                                        st.session_state[report_key] += diag_text
                                        st.success(f"Added {len(selected_diagnoses)} diagnosis(es) to document!")
                                        st.rerun()
                            else:
                                st.info("No diagnoses extracted")
                        
                        # Medications Section
                        with st.expander("💊 Medications", expanded=True):
                            medications = display_data.get('medications', [])
                            if medications:
                                # Initialize medications selections
                                if 'medications_selected' not in st.session_state[selections_key]:
                                    st.session_state[selections_key]['medications_selected'] = []
                                
                                selected_medications = []
                                for idx, med in enumerate(medications):
                                    med_display = f"{med.get('name', 'Unknown')} - {med.get('dosage', 'N/A')}"
                                    checkbox_key = f"med_{idx}_{selected_doc}"
                                    med_id = f"{med.get('name', '')}_{med.get('dosage', '')}"
                                    is_selected = med_id in [f"{m.get('name', '')}_{m.get('dosage', '')}" for m in st.session_state[selections_key]['medications_selected']]
                                    if st.checkbox(
                                        med_display,
                                        value=is_selected,
                                        key=checkbox_key
                                    ):
                                        selected_medications.append(med)
                                
                                st.session_state[selections_key]['medications_selected'] = selected_medications
                                
                                # Select All / Deselect All buttons
                                col_sel1, col_sel2 = st.columns(2)
                                with col_sel1:
                                    if st.button("✓ Select All", key=f"select_all_med_{selected_doc}"):
                                        st.session_state[selections_key]['medications_selected'] = medications.copy()
                                        st.rerun()
                                with col_sel2:
                                    if st.button("✗ Deselect All", key=f"deselect_all_med_{selected_doc}"):
                                        st.session_state[selections_key]['medications_selected'] = []
                                        st.rerun()
                                
                                # Add selected medications button
                                if st.button("➕ Add Selected Medications", key=f"add_med_{selected_doc}"):
                                    if selected_medications:
                                        med_text = "**MEDICATIONS**\n\n"
                                        for med in selected_medications:
                                            med_text += f"- {med.get('name', 'Unknown')} - {med.get('dosage', 'N/A')}\n"
                                        med_text += "\n"
                                        st.session_state[report_key] += med_text
                                        st.success(f"Added {len(selected_medications)} medication(s) to document!")
                                        st.rerun()
                            else:
                                st.info("No medications extracted")
                        
                        # Allergies Section
                        with st.expander("⚠️ Allergies", expanded=True):
                            allergies = display_data.get('allergies', [])
                            if allergies:
                                # Initialize allergies selections
                                if 'allergies_selected' not in st.session_state[selections_key]:
                                    st.session_state[selections_key]['allergies_selected'] = []
                                
                                selected_allergies = []
                                for idx, allergy in enumerate(allergies):
                                    checkbox_key = f"allergy_{idx}_{selected_doc}"
                                    is_selected = allergy in st.session_state[selections_key]['allergies_selected']
                                    if st.checkbox(
                                        allergy,
                                        value=is_selected,
                                        key=checkbox_key
                                    ):
                                        selected_allergies.append(allergy)
                                
                                st.session_state[selections_key]['allergies_selected'] = selected_allergies
                                
                                # Select All / Deselect All buttons
                                col_sel1, col_sel2 = st.columns(2)
                                with col_sel1:
                                    if st.button("✓ Select All", key=f"select_all_allergy_{selected_doc}"):
                                        st.session_state[selections_key]['allergies_selected'] = allergies.copy()
                                        st.rerun()
                                with col_sel2:
                                    if st.button("✗ Deselect All", key=f"deselect_all_allergy_{selected_doc}"):
                                        st.session_state[selections_key]['allergies_selected'] = []
                                        st.rerun()
                                
                                # Add selected allergies button
                                if st.button("➕ Add Selected Allergies", key=f"add_allergy_{selected_doc}"):
                                    if selected_allergies:
                                        allergy_text = "**ALLERGIES**\n\n"
                                        for allergy in selected_allergies:
                                            allergy_text += f"- {allergy}\n"
                                        allergy_text += "\n"
                                        st.session_state[report_key] += allergy_text
                                        st.success(f"Added {len(selected_allergies)} allergy/allergies to document!")
                                        st.rerun()
                            else:
                                st.info("No allergies extracted")
                        
                        # Vital Signs Section
                        with st.expander("📊 Vital Signs", expanded=False):
                            vital_signs = display_data.get('vital_signs', {})
                            if vital_signs:
                                # Initialize vital signs selections
                                if 'vital_signs_selected' not in st.session_state[selections_key]:
                                    st.session_state[selections_key]['vital_signs_selected'] = {}
                                
                                selected_vitals = {}
                                for field, value in vital_signs.items():
                                    if value:  # Only show non-empty fields
                                        checkbox_key = f"vital_{field}_{selected_doc}"
                                        is_selected = st.session_state[selections_key]['vital_signs_selected'].get(field, False)
                                        if st.checkbox(
                                            f"**{field.replace('_', ' ').title()}**: {value}",
                                            value=is_selected,
                                            key=checkbox_key
                                        ):
                                            selected_vitals[field] = value
                                
                                st.session_state[selections_key]['vital_signs_selected'] = selected_vitals
                                
                                # Add selected vital signs button
                                if st.button("➕ Add Selected Vital Signs", key=f"add_vitals_{selected_doc}"):
                                    if selected_vitals:
                                        vitals_text = "**VITAL SIGNS**\n\n"
                                        for field, value in selected_vitals.items():
                                            vitals_text += f"{field.replace('_', ' ').title()}: {value}\n"
                                        vitals_text += "\n"
                                        st.session_state[report_key] += vitals_text
                                        st.success("Added vital signs to document!")
                                        st.rerun()
                            else:
                                st.info("No vital signs extracted")
                        
                        # Clinical Notes Section
                        with st.expander("📝 Clinical Notes", expanded=False):
                            clinical_notes = display_data.get('clinical_notes', [])
                            if clinical_notes:
                                # Initialize clinical notes selections
                                if 'clinical_notes_selected' not in st.session_state[selections_key]:
                                    st.session_state[selections_key]['clinical_notes_selected'] = []
                                
                                selected_notes = []
                                for idx, note in enumerate(clinical_notes):
                                    # Truncate for display
                                    note_preview = note[:200] + "..." if len(note) > 200 else note
                                    checkbox_key = f"note_{idx}_{selected_doc}"
                                    is_selected = idx in st.session_state[selections_key]['clinical_notes_selected']
                                    if st.checkbox(
                                        note_preview,
                                        value=is_selected,
                                        key=checkbox_key
                                    ):
                                        selected_notes.append((idx, note))
                                
                                st.session_state[selections_key]['clinical_notes_selected'] = [idx for idx, _ in selected_notes]
                                
                                # Add selected clinical notes button
                                if st.button("➕ Add Selected Clinical Notes", key=f"add_notes_{selected_doc}"):
                                    if selected_notes:
                                        notes_text = "**CLINICAL NOTES**\n\n"
                                        for _, note in selected_notes:
                                            notes_text += f"{note}\n\n"
                                        st.session_state[report_key] += notes_text
                                        st.success(f"Added {len(selected_notes)} clinical note(s) to document!")
                                        st.rerun()
                            else:
                                st.info("No clinical notes extracted")
                    
                    with col2:
                        st.subheader("📝 Output Document Builder")
                        st.markdown("Build your document by selecting items from the left and adding them here")
                        
                        # Report editor
                        report_text = st.text_area(
                            "Document Content",
                            value=st.session_state[report_key],
                            height=600,
                            key=f"report_editor_{selected_doc}",
                            help="Edit the document content directly or use the 'Add Selected' buttons to add items"
                        )
                        
                        # Update session state
                        st.session_state[report_key] = report_text
                        
                        # Quick add all selected button
                        st.divider()
                        if st.button("➕ Add All Selected Items", key=f"add_all_{selected_doc}", type="primary"):
                            added_count = 0
                            all_text = ""
                            
                            # Patient info
                            patient_selected = st.session_state[selections_key].get('patient_info_selected', {})
                            if patient_selected:
                                all_text += "**PATIENT INFORMATION**\n\n"
                                for field, value in patient_selected.items():
                                    all_text += f"{field.replace('_', ' ').title()}: {value}\n"
                                all_text += "\n"
                                added_count += len(patient_selected)
                            
                            # Diagnoses
                            diag_selected = st.session_state[selections_key].get('diagnoses_selected', [])
                            if diag_selected:
                                all_text += "**DIAGNOSES**\n\n"
                                for diag in diag_selected:
                                    all_text += f"- {diag}\n"
                                all_text += "\n"
                                added_count += len(diag_selected)
                            
                            # Medications
                            med_selected = st.session_state[selections_key].get('medications_selected', [])
                            if med_selected:
                                all_text += "**MEDICATIONS**\n\n"
                                for med in med_selected:
                                    all_text += f"- {med.get('name', 'Unknown')} - {med.get('dosage', 'N/A')}\n"
                                all_text += "\n"
                                added_count += len(med_selected)
                            
                            # Allergies
                            allergy_selected = st.session_state[selections_key].get('allergies_selected', [])
                            if allergy_selected:
                                all_text += "**ALLERGIES**\n\n"
                                for allergy in allergy_selected:
                                    all_text += f"- {allergy}\n"
                                all_text += "\n"
                                added_count += len(allergy_selected)
                            
                            # Vital signs
                            vitals_selected = st.session_state[selections_key].get('vital_signs_selected', {})
                            if vitals_selected:
                                all_text += "**VITAL SIGNS**\n\n"
                                for field, value in vitals_selected.items():
                                    all_text += f"{field.replace('_', ' ').title()}: {value}\n"
                                all_text += "\n"
                                added_count += len(vitals_selected)
                            
                            # Clinical notes
                            notes_selected_indices = st.session_state[selections_key].get('clinical_notes_selected', [])
                            clinical_notes = display_data.get('clinical_notes', [])
                            if notes_selected_indices:
                                all_text += "**CLINICAL NOTES**\n\n"
                                for idx in notes_selected_indices:
                                    if idx < len(clinical_notes):
                                        all_text += f"{clinical_notes[idx]}\n\n"
                                added_count += len(notes_selected_indices)
                            
                            if all_text:
                                st.session_state[report_key] += all_text
                                st.success(f"Added {added_count} item(s) to document!")
                                st.rerun()
                            else:
                                st.info("No items selected. Please select items from the left column first.")
                        
                        # Action buttons
                        st.divider()
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            if st.button("🔄 Clear Document", key=f"clear_{selected_doc}"):
                                st.session_state[report_key] = ""
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("💾 Save Document", key=f"save_{selected_doc}"):
                                st.success("Document saved to session state!")
                        
                        with col_btn3:
                            # Download button
                            if report_text:
                                st.download_button(
                                    label="📥 Download",
                                    data=report_text,
                                    file_name=f"{sanitize_filename(selected_doc)}_llm_report.txt",
                                    mime="text/plain",
                                    key=f"download_{selected_doc}"
                                )
                else:
                    st.warning("No elements found in processed document")
    
    # Tab 6: Section Editor
    with tab6:
        st.header("✏️ Section Editor")
        st.markdown("Visualize document elements, manage sections, and create custom section mappings")
        
        if not st.session_state.processed_documents:
            st.info("No data available. Please upload and process PDF files first.")
        else:
            # Document selector
            selected_doc = st.selectbox(
                "Select Document",
                list(st.session_state.processed_documents.keys()),
                key="section_editor_doc"
            )
            
            if selected_doc:
                doc_data = st.session_state.processed_documents[selected_doc]
                elements = doc_data.get('elements', [])
                
                if elements:
                    _, _, _, SectionEditor = _lazy_imports()
                    editor = SectionEditor()
                    
                    # Identify sections
                    sections = editor.identify_sections(elements)
                    
                    # Initialize session state for section editor
                    if 'selected_sections' not in st.session_state:
                        st.session_state.selected_sections = set(sections.keys())
                    if 'custom_sections' not in st.session_state:
                        st.session_state.custom_sections = {}
                    
                    # Tabs within Section Editor
                    editor_tab1, editor_tab2, editor_tab3 = st.tabs([
                        "📋 Section Manager",
                        "🔍 Element Browser",
                        "➕ Custom Sections"
                    ])
                    
                    with editor_tab1:
                        st.subheader("Section Manager")
                        st.markdown("Select which sections to include in data extraction")
                        
                        # Section selection
                        selected_sections = editor.render_section_manager(
                            sections,
                            st.session_state.selected_sections
                        )
                        st.session_state.selected_sections = selected_sections
                        
                        # Summary
                        st.divider()
                        st.subheader("Summary")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Sections", len(sections))
                            st.metric("Selected Sections", len(selected_sections))
                        with col2:
                            total_elements = sum(len(elems) for elems in sections.values())
                            selected_elements = sum(
                                len(elems) for name, elems in sections.items()
                                if name in selected_sections
                            )
                            st.metric("Total Elements", total_elements)
                            st.metric("Selected Elements", selected_elements)
                        
                        # Show selected sections
                        if selected_sections:
                            st.write("**Selected Sections:**")
                            for section_name in sorted(selected_sections):
                                st.write(f"- {section_name} ({len(sections[section_name])} elements)")
                            
                            # Store selected sections for this document
                            doc_key = f"{selected_doc}_selected_sections"
                            st.session_state[doc_key] = selected_sections
                            
                            # Button to re-extract with selected sections
                            st.divider()
                            if st.button("Re-extract Data with Selected Sections", type="primary"):
                                with st.spinner("Re-extracting data..."):
                                    _, DataExtractor, _, _ = _lazy_imports()
                                    extractor = DataExtractor(use_llm=use_llm)
                                    re_extracted = extractor.extract(elements, selected_sections=list(selected_sections))
                                    
                                    # Update extracted data
                                    st.session_state.extracted_data[selected_doc] = re_extracted
                                    st.success("Data re-extracted successfully! Check the Dashboard tab to see updated results.")
                    
                    with editor_tab2:
                        st.subheader("Element Browser")
                        st.markdown("Browse all document elements with their types and content")
                        
                        # Element type statistics
                        type_counts = editor.get_element_types(elements)
                        st.write("**Element Type Distribution:**")
                        for elem_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                            st.write(f"- **{elem_type}**: {count} elements")
                        
                        st.divider()
                        
                        # Element browser
                        selected_indices = editor.render_element_browser(elements)
                        
                        if selected_indices:
                            st.success(f"Selected {len(selected_indices)} elements")
                    
                    with editor_tab3:
                        st.subheader("Create Custom Section")
                        st.markdown("Select elements to create a custom section for extraction")
                        
                        custom_section = editor.render_custom_section_creator(elements)
                        
                        if custom_section:
                            section_name = list(custom_section.keys())[0]
                            st.session_state.custom_sections[section_name] = custom_section[section_name]
                            st.success(f"Created custom section: {section_name}")
                        
                        # Show existing custom sections
                        if st.session_state.custom_sections:
                            st.divider()
                            st.subheader("Existing Custom Sections")
                            for section_name, section_elements in st.session_state.custom_sections.items():
                                with st.expander(f"Custom Section: {section_name}"):
                                    st.write(f"**Elements**: {len(section_elements)}")
                                    section_text = editor.get_section_text(section_elements)
                                    st.text_area(
                                        "Section Content",
                                        value=section_text,
                                        height=200,
                                        disabled=True,
                                        key=f"custom_section_{section_name}"
                                    )
                                    
                                    if st.button(f"Delete {section_name}", key=f"delete_{section_name}"):
                                        del st.session_state.custom_sections[section_name]
                                        st.rerun()
                else:
                    st.warning("No elements found in processed document")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        if "no running event loop" in str(e).lower():
            st.error("""
            **Event Loop Error Detected**
            
            This error is typically caused by compatibility issues between Streamlit and 
            certain libraries (like torch/unstructured). 
            
            **Try these solutions:**
            1. Restart the Streamlit app: Stop and run `streamlit run app.py` again
            2. Use the API mode instead of local library mode (check sidebar)
            3. Ensure you have the latest versions: `pip install --upgrade streamlit unstructured[pdf]`
            
            If the error persists, please check your Python environment and dependencies.
            """)
            st.exception(e)
        else:
            raise
