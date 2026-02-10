"""LLM-based extraction module to replace regex patterns with intelligent extraction

NOTE ON RETRY BEHAVIOR:
The OpenAI client has built-in retry logic that can continue running in background threads
even after the Streamlit app is stopped. This module disables automatic retries (max_retries=0)
and handles retries manually to prevent background retry loops. However, if you see retries
continuing after stopping the app, you may need to:
1. Wait for ongoing requests to complete
2. Kill the Python process if necessary
3. Check that max_retries=0 is being respected by your OpenAI client version
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from src.utils import save_json, sanitize_filename

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LLMExtractor:
    """Extract structured data using LLM instead of regex patterns"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", 
                 max_retries: int = 5, rate_limit_delay: float = 0.5):
        """
        Initialize the LLM extractor
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: Model to use for extraction (default: gpt-4o-mini for cost efficiency)
            max_retries: Maximum number of retry attempts for rate limit errors (default: 5)
            rate_limit_delay: Delay in seconds between sequential API calls (default: 0.5)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._client = None  # Lazy initialization
        
        if not self.api_key:
            logger.warning(
                "OPENAI_API_KEY not found. LLM extraction will not be available. "
                "Set OPENAI_API_KEY in .env file or pass api_key parameter."
            )
    
    def _is_available(self) -> bool:
        """Check if LLM extraction is available"""
        return self.api_key is not None
    
    def extract_patient_info(self, section_text: str) -> Dict[str, Any]:
        """
        Extract patient information using LLM
        
        Args:
            section_text: Text from PATIENT IDENTIFICATION section
            
        Returns:
            Dictionary with patient info fields
        """
        if not self._is_available():
            return {}
        
        prompt = f"""Extract patient information from the following text. Return ONLY a valid JSON object with these fields:
- name: Full patient name (include title like Ms./Mr. if present)
- mrn: Medical Record Number
- age: Age as a number
- gender: Gender (Male/Female/Other)
- date_of_birth: Date of birth if mentioned

Text:
{section_text}

Return ONLY the JSON object, no other text:"""

        try:
            response = self._call_llm(prompt)
            patient_info = json.loads(response)
            return patient_info
        except Exception as e:
            logger.error(f"Error extracting patient info with LLM: {str(e)}")
            return {}
    
    def extract_diagnoses(self, section_text: str) -> List[str]:
        """
        Extract diagnoses from section text using LLM
        
        Args:
            section_text: Text from ACTIVE MEDICAL ISSUES section
            
        Returns:
            List of diagnosis strings
        """
        if not self._is_available():
            return []
        
        prompt = f"""Extract all diagnoses from the following medical text. Return ONLY a valid JSON array of diagnosis strings.
Each diagnosis should be a clear, complete medical condition name.

Text:
{section_text}

Return ONLY the JSON array, no other text. Example format: ["Diagnosis 1", "Diagnosis 2"]"""

        try:
            response = self._call_llm(prompt)
            diagnoses = json.loads(response)
            if isinstance(diagnoses, list):
                return [d.strip() for d in diagnoses if d.strip()]
            return []
        except Exception as e:
            logger.error(f"Error extracting diagnoses with LLM: {str(e)}")
            return []
    
    def extract_medications(self, section_text: str) -> List[Dict[str, str]]:
        """
        Extract medications from section text using LLM
        
        Args:
            section_text: Text from medication section
            
        Returns:
            List of medication dictionaries with 'name' and 'dosage' keys
        """
        if not self._is_available():
            return []
        
        prompt = f"""Extract all medications from the following medical text. Return ONLY a valid JSON array of medication objects.
Each medication object should have:
- name: Medication name
- dosage: Dosage information (e.g., "120 mg", "10 mg daily")

Text:
{section_text}

Return ONLY the JSON array, no other text. Example format: [{{"name": "Medication Name", "dosage": "120 mg"}}]"""

        try:
            response = self._call_llm(prompt)
            medications = json.loads(response)
            if isinstance(medications, list):
                # Validate structure
                valid_meds = []
                for med in medications:
                    if isinstance(med, dict) and 'name' in med:
                        valid_meds.append({
                            'name': med.get('name', '').strip(),
                            'dosage': med.get('dosage', '').strip()
                        })
                return valid_meds
            return []
        except Exception as e:
            logger.error(f"Error extracting medications with LLM: {str(e)}")
            return []
    
    def extract_allergies(self, section_text: str) -> List[str]:
        """
        Extract allergies from section text using LLM
        
        Args:
            section_text: Text from allergies section
            
        Returns:
            List of allergy strings
        """
        if not self._is_available():
            return []
        
        prompt = f"""Extract allergies from the following medical text. Return ONLY a valid JSON array of allergy strings.
If the text says "no known allergies" or "NKA", return an empty array [].
Otherwise, extract each allergy mentioned.

Text:
{section_text}

Return ONLY the JSON array, no other text. Example format: ["Allergy 1", "Allergy 2"]"""

        try:
            response = self._call_llm(prompt)
            allergies = json.loads(response)
            if isinstance(allergies, list):
                return [a.strip() for a in allergies if a.strip()]
            return []
        except Exception as e:
            logger.error(f"Error extracting allergies with LLM: {str(e)}")
            return []
    
    def extract_vital_signs(self, text: str) -> Dict[str, Any]:
        """
        Extract vital signs from text using LLM
        
        Args:
            text: Text containing vital signs
            
        Returns:
            Dictionary with vital signs
        """
        if not self._is_available():
            return {}
        
        prompt = f"""Extract vital signs from the following medical text. Return ONLY a valid JSON object with these fields (only include fields that are present):
- blood_pressure: Blood pressure (e.g., "120/80")
- heart_rate: Heart rate as number
- temperature: Temperature as number
- respiratory_rate: Respiratory rate as number
- oxygen_saturation: O2 saturation as number

Text:
{text}

Return ONLY the JSON object, no other text:"""

        try:
            response = self._call_llm(prompt)
            vitals = json.loads(response)
            if isinstance(vitals, dict):
                return vitals
            return {}
        except Exception as e:
            logger.error(f"Error extracting vital signs with LLM: {str(e)}")
            return {}
    
    def extract_from_sections(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        selected_sections: Optional[List[str]] = None,
        document_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from selected sections using LLM in a single batched API call
        
        Args:
            sections: Dictionary mapping section names to elements
            selected_sections: List of section names to extract from (if None, extract from all)
            document_name: Optional document name for saving API response
            
        Returns:
            Dictionary with extracted structured data
        """
        if not self._is_available():
            return {}
        
        # Combine text from sections
        sections_to_process = selected_sections if selected_sections else list(sections.keys())
        
        # Build combined text with section labels for context
        combined_text_parts = []
        for section_name in sections_to_process:
            if section_name not in sections:
                continue
            section_elements = sections[section_name]
            section_text = self._combine_text(section_elements)
            if section_text.strip():
                combined_text_parts.append(f"=== {section_name.upper().replace('_', ' ')} ===\n{section_text}\n")
        
        if not combined_text_parts:
            return {
                'patient_info': {},
                'diagnoses': [],
                'medications': [],
                'allergies': [],
                'vital_signs': {},
            }
        
        # Combine all sections into one text
        full_text = "\n".join(combined_text_parts)
        
        # Single batched extraction prompt
        prompt = f"""Extract all structured medical data from the following document sections. Return ONLY a valid JSON object with these fields:

- patient_info: Object with fields: name, mrn, age, gender, date_of_birth (all optional)
- diagnoses: Array of diagnosis strings
- medications: Array of objects with "name" and "dosage" fields
- allergies: Array of allergy strings (empty array if "no known allergies" or "NKA")
- vital_signs: Object with fields: blood_pressure, heart_rate, temperature, respiratory_rate, oxygen_saturation (all optional)

Document Text:
{full_text}

Return ONLY the JSON object, no other text. Example format:
{{
  "patient_info": {{"name": "John Doe", "mrn": "12345", "age": "45", "gender": "Male"}},
  "diagnoses": ["Hypertension", "Diabetes"],
  "medications": [{{"name": "Metformin", "dosage": "500 mg"}}],
  "allergies": [],
  "vital_signs": {{"blood_pressure": "120/80", "heart_rate": "72"}}
}}"""

        try:
            response = self._call_llm(prompt, document_name=document_name)
            # Clean response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            extracted_data = json.loads(response)
            
            # Validate and normalize structure
            result = {
                'patient_info': extracted_data.get('patient_info', {}) or {},
                'diagnoses': extracted_data.get('diagnoses', []) or [],
                'medications': extracted_data.get('medications', []) or [],
                'allergies': extracted_data.get('allergies', []) or [],
                'vital_signs': extracted_data.get('vital_signs', {}) or {},
            }
            
            # Ensure medications have correct structure
            normalized_meds = []
            for med in result['medications']:
                if isinstance(med, dict):
                    normalized_meds.append({
                        'name': med.get('name', '').strip(),
                        'dosage': med.get('dosage', '').strip()
                    })
            result['medications'] = normalized_meds
            
            # Clean up empty strings and None values in patient_info
            cleaned_patient_info = {}
            for key, value in result['patient_info'].items():
                if value is not None and str(value).strip():
                    cleaned_patient_info[key] = str(value).strip()
            result['patient_info'] = cleaned_patient_info
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            # Fallback: return empty structure
            return {
                'patient_info': {},
                'diagnoses': [],
                'medications': [],
                'allergies': [],
                'vital_signs': {},
            }
        except Exception as e:
            logger.error(f"Error in batched extraction: {str(e)}")
            return {
                'patient_info': {},
                'diagnoses': [],
                'medications': [],
                'allergies': [],
                'vital_signs': {},
            }
    
    def _combine_text(self, elements: List[Dict[str, Any]]) -> str:
        """Combine text from elements"""
        texts = []
        for elem in elements:
            text = elem.get('text', '')
            if text:
                texts.append(text)
        return '\n'.join(texts)
    
    def _get_client(self):
        """Get or create OpenAI client with retries disabled"""
        if self._client is None:
            try:
                from openai import OpenAI
                import httpx
                
                # IMPORTANT: Disable all automatic retries to prevent background retry loops
                # The OpenAI client has built-in retry logic that can continue running
                # even after the app stops. We disable it completely and handle retries manually.
                
                # Try to create transport with retries=0 (newer httpx versions)
                try:
                    transport = httpx.HTTPTransport(retries=0)
                    http_client = httpx.Client(
                        transport=transport,
                        timeout=httpx.Timeout(30.0, connect=10.0),
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                    )
                except (TypeError, AttributeError):
                    # Fallback for older httpx versions that don't support retries parameter
                    # Create client without transport - httpx will use default
                    http_client = httpx.Client(
                        timeout=httpx.Timeout(30.0, connect=10.0),
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                    )
                
                # Create OpenAI client with max_retries=0 to disable automatic retries
                # This is critical - without this, the client will retry in the background
                self._client = OpenAI(
                    api_key=self.api_key,
                    max_retries=0,  # CRITICAL: Disable automatic retries - we handle them manually
                    http_client=http_client
                )
                
                # Double-check that retries are disabled by inspecting the client
                # Some versions might ignore max_retries, so we verify
                if hasattr(self._client, '_client') and hasattr(self._client._client, 'max_retries'):
                    if self._client._client.max_retries != 0:
                        logger.warning("OpenAI client retries not properly disabled, may cause background retries")
                        
            except ImportError:
                raise ImportError(
                    "openai library not installed. Install with: pip install openai>=1.0.0"
                )
        return self._client
    
    def close(self):
        """Close the HTTP client and clean up resources"""
        if self._client is not None:
            try:
                # Close the underlying httpx client if it exists
                if hasattr(self._client, '_client') and hasattr(self._client._client, 'close'):
                    self._client._client.close()
                elif hasattr(self._client, 'http_client') and hasattr(self._client.http_client, 'close'):
                    self._client.http_client.close()
            except Exception as e:
                logger.warning(f"Error closing client: {str(e)}")
            finally:
                self._client = None
    
    def _call_llm(self, prompt: str, document_name: Optional[str] = None) -> str:
        """
        Call the LLM API with exponential backoff retry for rate limit errors
        
        Args:
            prompt: The prompt to send
            document_name: Optional document name for saving API response
            
        Returns:
            Response text from LLM
            
        Raises:
            Exception: If all retry attempts fail or other errors occur
        """
        try:
            from openai import RateLimitError, APIError
            
            client = self._get_client()
            
            base_delay = 1.0  # Start with 1 second
            max_delay = 60.0  # Max 60 seconds
            
            for attempt in range(self.max_retries):
                try:
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a medical data extraction assistant. Extract structured data from medical documents and return ONLY valid JSON, no explanations or additional text."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,  # Low temperature for consistent extraction
                        max_tokens=1000,
                        timeout=30.0  # Add timeout to prevent hanging requests
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    
                    # Save raw API response to JSON file
                    self._save_openai_api_response(response_text, document_name, prompt)
                    
                    return response_text
                    
                except RateLimitError as e:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s, 8s, 16s (capped at max_delay)
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Rate limit hit (429), retrying in {delay:.1f}s... "
                            f"(Attempt {attempt + 1}/{self.max_retries})"
                        )
                        # Use time.sleep with interruptible sleep
                        time.sleep(delay)
                    else:
                        logger.error(f"Rate limit error after {self.max_retries} attempts: {str(e)}")
                        raise Exception(
                            f"Rate limit exceeded after {self.max_retries} retry attempts. "
                            "Please wait a moment and try again, or reduce the number of documents being processed."
                        ) from e
                
                except APIError as e:
                    # For other API errors, retry with exponential backoff
                    if attempt < self.max_retries - 1 and hasattr(e, 'status_code') and e.status_code == 429:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"API error 429, retrying in {delay:.1f}s... "
                            f"(Attempt {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"LLM API error: {str(e)}")
                        raise
                
                except KeyboardInterrupt:
                    # Allow interruption during retries
                    logger.info("LLM extraction interrupted by user")
                    raise
            
            # Should not reach here, but just in case
            raise Exception("Failed to get response from LLM after all retry attempts")
            
        except ImportError:
            raise ImportError(
                "openai library not installed. Install with: pip install openai>=1.0.0"
            )
        except KeyboardInterrupt:
            # Re-raise keyboard interrupts
            raise
        except Exception as e:
            # Re-raise if it's already been handled above
            if "Rate limit" in str(e) or "after all retry attempts" in str(e):
                raise
            logger.error(f"LLM API call failed: {str(e)}")
            raise
    
    def _save_openai_api_response(self, response_text: str, document_name: Optional[str] = None, prompt: Optional[str] = None) -> None:
        """
        Save raw OpenAI API response to JSON file
        
        Args:
            response_text: The raw JSON response text from OpenAI
            document_name: Optional document name for filename
            prompt: Optional prompt that was sent (for reference)
        """
        try:
            output_dir = "data/api_outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            # Try to parse the response as JSON to validate it
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError:
                # If it's not valid JSON, save it as-is
                parsed_response = {"raw_response": response_text}
            
            # Create filename
            if document_name:
                base_name = sanitize_filename(Path(document_name).stem)
            else:
                base_name = "unknown_document"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"{base_name}_openai_api_{timestamp}.json")
            
            # Save the API response
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'response': parsed_response,
                'raw_response_text': response_text
            }
            
            # Optionally include prompt (truncated if too long)
            if prompt:
                save_data['prompt_preview'] = prompt[:500] + "..." if len(prompt) > 500 else prompt
            
            save_json(save_data, output_path)
            
            logger.info(f"Saved OpenAI API response to {output_path}")
        except Exception as e:
            logger.warning(f"Failed to save OpenAI API response: {str(e)}")