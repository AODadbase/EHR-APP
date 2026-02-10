"""Section Editor module for interactive section management and element visualization"""

from typing import List, Dict, Any, Optional, Set
import streamlit as st
from src.data_extractor import DataExtractor


class SectionEditor:
    """Interactive section editor for visualizing and managing document elements"""
    
    def __init__(self):
        """Initialize the section editor"""
        self.extractor = DataExtractor()
    
    def identify_sections(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Identify sections in the document"""
        return self.extractor._identify_sections(elements)
    
    def get_element_types(self, elements: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of each element type"""
        type_counts = {}
        for elem in elements:
            elem_type = elem.get('type', 'unknown')
            type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
        return type_counts
    
    def filter_elements_by_type(
        self, 
        elements: List[Dict[str, Any]], 
        element_types: Set[str]
    ) -> List[Dict[str, Any]]:
        """Filter elements by type"""
        return [
            elem for elem in elements 
            if elem.get('type', 'unknown').lower() in {t.lower() for t in element_types}
        ]
    
    def create_custom_section(
        self,
        section_name: str,
        selected_elements: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Create a custom section from selected elements"""
        return {section_name: selected_elements}
    
    def get_section_text(self, section_elements: List[Dict[str, Any]]) -> str:
        """Get combined text from section elements"""
        texts = []
        for elem in section_elements:
            text = elem.get('text', '')
            if text:
                texts.append(text)
        return '\n'.join(texts)
    
    def get_element_preview(self, elem: Dict[str, Any], max_length: int = 200) -> str:
        """Get a preview of element text"""
        text = elem.get('text', '')
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text
    
    def render_element_browser(
        self,
        elements: List[Dict[str, Any]],
        selected_indices: Optional[Set[int]] = None
    ) -> Set[int]:
        """Render element browser UI and return selected element indices"""
        if selected_indices is None:
            selected_indices = set()
        
        st.subheader("Element Browser")
        st.markdown("Browse all document elements with their types and content")
        
        # Filter options
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_type = st.selectbox(
                "Filter by Type",
                ["All Types"] + sorted(set(elem.get('type', 'unknown') for elem in elements)),
                key="element_filter_type"
            )
        with col2:
            show_count = st.number_input("Elements to show", min_value=10, max_value=500, value=50, step=10)
        
        # Filter elements
        filtered_elements = elements
        if filter_type != "All Types":
            filtered_elements = [
                elem for elem in elements 
                if elem.get('type', 'unknown') == filter_type
            ]
        
        # Display elements
        st.markdown(f"**Showing {len(filtered_elements[:show_count])} of {len(filtered_elements)} elements**")
        
        selected_indices = set()
        for idx, elem in enumerate(filtered_elements[:show_count]):
            elem_type = elem.get('type', 'unknown')
            text = elem.get('text', '')
            preview = self.get_element_preview(elem, 150)
            
            # Checkbox for selection
            checkbox_key = f"elem_select_{idx}"
            is_selected = st.checkbox(
                f"**{elem_type}** (Index {idx})",
                value=idx in selected_indices,
                key=checkbox_key
            )
            
            if is_selected:
                selected_indices.add(idx)
            
            # Show preview
            with st.expander(f"Preview: {preview[:50]}..."):
                st.write(f"**Type**: `{elem_type}`")
                st.write(f"**Index**: {idx}")
                st.write(f"**Text**:")
                st.text_area("", value=text, height=100, disabled=True, key=f"elem_text_{idx}")
                
                # Show metadata if available
                metadata = elem.get('metadata', {})
                if metadata:
                    st.write("**Metadata**:")
                    st.json(metadata)
        
        return selected_indices
    
    def render_section_manager(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        selected_sections: Optional[Set[str]] = None
    ) -> Set[str]:
        """Render section manager UI and return selected section names"""
        if selected_sections is None:
            selected_sections = set()
        
        st.subheader("Section Manager")
        st.markdown("Select sections to include in extraction")
        
        # Section selection checkboxes
        for section_name, section_elements in sections.items():
            checkbox_key = f"section_select_{section_name}"
            is_selected = st.checkbox(
                f"**{section_name}** ({len(section_elements)} elements)",
                value=section_name in selected_sections,
                key=checkbox_key
            )
            
            if is_selected:
                selected_sections.add(section_name)
            elif section_name in selected_sections:
                selected_sections.remove(section_name)
            
            # Show section preview
            with st.expander(f"View {section_name} elements"):
                section_text = self.get_section_text(section_elements)
                st.text_area(
                    f"Section Text ({section_name})",
                    value=section_text,
                    height=200,
                    disabled=True,
                    key=f"section_text_{section_name}"
                )
                
                # Show element types in this section
                type_counts = {}
                for elem in section_elements:
                    elem_type = elem.get('type', 'unknown')
                    type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
                
                if type_counts:
                    st.write("**Element Types in Section:**")
                    for elem_type, count in sorted(type_counts.items()):
                        st.write(f"- {elem_type}: {count}")
        
        return selected_sections
    
    def render_custom_section_creator(
        self,
        elements: List[Dict[str, Any]]
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """Render UI for creating custom sections"""
        st.subheader("Create Custom Section")
        st.markdown("Select elements to create a custom section")
        
        # Element selection
        selected_indices = st.multiselect(
            "Select Elements (by index)",
            options=list(range(len(elements))),
            format_func=lambda idx: f"Element {idx}: {self.get_element_preview(elements[idx], 50)}"
        )
        
        if selected_indices:
            selected_elements = [elements[idx] for idx in selected_indices]
            
            # Section name input
            section_name = st.text_input(
                "Section Name",
                value="custom_section",
                help="Enter a name for this custom section"
            )
            
            # Preview
            st.write("**Preview:**")
            section_text = self.get_section_text(selected_elements)
            st.text_area("Section Text", value=section_text, height=200, disabled=True)
            
            # Create button
            if st.button("Create Section", type="primary"):
                if section_name:
                    return {section_name: selected_elements}
        
        return None
