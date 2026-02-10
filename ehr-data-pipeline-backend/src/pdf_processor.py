"""PDF processing module using Unstructured.io SDK"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import json
from datetime import datetime

from src.config import Config
from src.utils import save_json, get_file_basename, sanitize_filename

logger = logging.getLogger(__name__)

# Try to import unstructured.io SDK - support both API client and direct library
# Suppress warnings at import time to avoid cluttering logs
# We'll check availability when actually needed to avoid event loop issues

def _check_api_client_available():
    """Check if API can be used (we use partition_via_api from unstructured SDK)"""
    try:
        from unstructured.partition.api import partition_via_api
        return True
    except ImportError:
        return False

def _check_direct_lib_available():
    """Check if direct library is available (deferred to avoid torch import issues)"""
    try:
        import importlib
        importlib.import_module('unstructured.partition.pdf')
        return True
    except ImportError:
        return False


class PDFProcessor:
    """Process PDF files using Unstructured.io API or library"""
    
    def __init__(self, use_api: bool = True):
        """
        Initialize the PDF processor
        
        Args:
            use_api: If True, use API client. If False, use direct library.
        """
        self.use_api = use_api
        
        if use_api:
            Config.validate()
            if not _check_api_client_available():
                raise ImportError(
                    "unstructured library not installed. "
                    "Install with: pip install unstructured[pdf]"
                )
            # We use partition_via_api from the unstructured SDK
            # This is the recommended way to access the API
            self.api_key = Config.UNSTRUCTURED_API_KEY
            self.api_url = Config.UNSTRUCTURED_API_URL
        else:
            if not _check_direct_lib_available():
                raise ImportError(
                    "unstructured library not installed. "
                    "Install with: pip install unstructured[pdf]"
                )
    
    def process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a single PDF file and return document elements
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of document elements (dictionaries)
        """
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            if self.use_api:
                return self._process_with_api(file_path)
            else:
                return self._process_with_library(file_path)
                
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise
    
    def _process_with_api(self, file_path: str) -> List[Dict[str, Any]]:
        """Process PDF using Unstructured.io API via partition_via_api"""
        # Import here to avoid event loop issues
        try:
            from unstructured.partition.api import partition_via_api
        except ImportError:
            raise ImportError(
                "unstructured library not installed. "
                "Install with: pip install unstructured[pdf]"
            )
        
        # Prepare API URL - handle both platform and legacy endpoints
        base_url = Config.UNSTRUCTURED_API_URL.rstrip('/')
        api_url = None
        
        # Check if it's the platform API (contains platform.unstructuredapp.io/api/v1)
        if 'platform.unstructuredapp.io/api/v1' in base_url:
            # Platform API - use as-is (partition_via_api will handle it)
            api_url = base_url
        # Check if it's the legacy endpoint format
        elif 'api.unstructuredapp.io' in base_url or 'api.unstructured.io' in base_url:
            # Legacy Partition Endpoint format
            if '/general/v0/general' in base_url:
                # Already has the full path
                api_url = base_url
            else:
                # Add the legacy endpoint path
                api_url = f"{base_url}/general/v0/general"
        else:
            # Use as-is
            api_url = base_url
        
        logger.info(f"Using API URL: {api_url}")
        logger.info(f"Base URL from config: {Config.UNSTRUCTURED_API_URL}")
        
        try:
            # Use partition_via_api from the SDK
            # This handles all the HTTP details for us
            elements = partition_via_api(
                filename=file_path,
                api_key=Config.UNSTRUCTURED_API_KEY,
                api_url=api_url,
                strategy="hi_res",
                hi_res_model_name="yolox",
            )
            
            logger.info(f"Successfully processed PDF via API: {len(elements)} elements extracted")
            
            # Convert elements to dict
            elements_dict = self._convert_elements_to_dict(elements)
            
            # Save raw API response to JSON file
            self._save_unstructured_api_response(file_path, elements_dict)
            
            return elements_dict
            
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _process_with_library(self, file_path: str) -> List[Dict[str, Any]]:
        """Process PDF using unstructured library directly"""
        # Import here to avoid event loop issues at module level
        try:
            from unstructured.partition.pdf import partition_pdf
        except ImportError:
            raise ImportError(
                "unstructured library not installed. "
                "Install with: pip install unstructured[pdf]"
            )
        
        try:
            elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",
                hi_res_model_name="yolox",
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "poppler" in error_msg or "page count" in error_msg:
                raise RuntimeError(
                    "Poppler is required for local PDF processing but is not installed.\n\n"
                    "SOLUTION OPTIONS:\n"
                    "1. Use API mode instead (recommended): Select 'API (Cloud)' in the Streamlit sidebar\n"
                    "2. Install Poppler:\n"
                    "   - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/\n"
                    "             Extract and add bin/ folder to your PATH\n"
                    "   - Or use: choco install poppler (if you have Chocolatey)\n"
                    "   - macOS: brew install poppler\n"
                    "   - Linux: sudo apt-get install poppler-utils\n\n"
                    f"Original error: {str(e)}"
                )
            raise
        
        return self._convert_elements_to_dict(elements)
    
    def _convert_elements_to_dict(self, elements: List[Any]) -> List[Dict[str, Any]]:
        """Convert element objects to dictionaries, preserving element types and metadata"""
        result = []
        
        for idx, elem in enumerate(elements):
            if isinstance(elem, dict):
                # Already a dict, but ensure it has all fields we need
                elem_dict = elem.copy()
                # Ensure type is preserved
                if 'type' not in elem_dict:
                    elem_dict['type'] = elem_dict.get('element_type', 'unknown')
                # Add index for ordering
                elem_dict['index'] = idx
                result.append(elem_dict)
            else:
                # Extract attributes from element object
                elem_dict = {
                    'type': getattr(elem, 'type', getattr(elem, 'element_type', 'unknown')),
                    'text': getattr(elem, 'text', ''),
                    'metadata': {},
                    'index': idx
                }
                
                # Try to get metadata - preserve all available metadata
                if hasattr(elem, 'metadata'):
                    metadata = elem.metadata
                    if isinstance(metadata, dict):
                        elem_dict['metadata'] = metadata.copy()
                    elif hasattr(metadata, '__dict__'):
                        elem_dict['metadata'] = metadata.__dict__.copy()
                
                # Extract additional attributes that might be useful
                # Page number
                if hasattr(elem, 'metadata') and hasattr(elem.metadata, 'page_number'):
                    elem_dict['metadata']['page_number'] = elem.metadata.page_number
                elif hasattr(elem, 'page_number'):
                    elem_dict['metadata']['page_number'] = elem.page_number
                
                # Coordinates (bounding box)
                if hasattr(elem, 'metadata'):
                    for coord_attr in ['coordinates', 'bbox', 'x0', 'y0', 'x1', 'y1']:
                        if hasattr(elem.metadata, coord_attr):
                            elem_dict['metadata'][coord_attr] = getattr(elem.metadata, coord_attr)
                
                # Parent/child relationships
                if hasattr(elem, 'parent_id'):
                    elem_dict['parent_id'] = elem.parent_id
                if hasattr(elem, 'element_id'):
                    elem_dict['element_id'] = elem.element_id
                
                # Category (if available)
                if hasattr(elem, 'category'):
                    elem_dict['category'] = elem.category
                
                result.append(elem_dict)
        
        return result
    
    def process_multiple_pdfs(self, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process multiple PDF files
        
        Args:
            file_paths: List of paths to PDF files
            
        Returns:
            Dictionary mapping file names to their document elements
        """
        results = {}
        
        for file_path in file_paths:
            try:
                basename = get_file_basename(file_path)
                elements = self.process_pdf(file_path)
                results[basename] = elements
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                results[get_file_basename(file_path)] = []
        
        return results
    
    def _save_unstructured_api_response(self, file_path: str, elements: List[Dict[str, Any]]) -> None:
        """
        Save raw Unstructured API response to JSON file
        
        Args:
            file_path: Path to the original PDF file
            elements: List of elements returned from the API
        """
        try:
            output_dir = "data/api_outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            # Get base filename without extension
            base_name = get_file_basename(file_path)
            sanitized_name = sanitize_filename(base_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save the raw API response
            output_path = os.path.join(output_dir, f"{sanitized_name}_unstructured_api_{timestamp}.json")
            save_json({
                'source_file': file_path,
                'timestamp': datetime.now().isoformat(),
                'element_count': len(elements),
                'elements': elements
            }, output_path)
            
            logger.info(f"Saved Unstructured API response to {output_path}")
        except Exception as e:
            logger.warning(f"Failed to save Unstructured API response: {str(e)}")
    
    def save_processed_results(
        self, 
        results: Dict[str, List[Dict[str, Any]]], 
        output_dir: str = "data/processed"
    ) -> None:
        """
        Save processed results to JSON files
        
        Args:
            results: Dictionary mapping file names to document elements
            output_dir: Directory to save the JSON files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for filename, elements in results.items():
            output_path = os.path.join(output_dir, f"{filename}_processed.json")
            save_json({
                'filename': filename,
                'elements': elements,
                'element_count': len(elements)
            }, output_path)
            logger.info(f"Saved processed results to {output_path}")
