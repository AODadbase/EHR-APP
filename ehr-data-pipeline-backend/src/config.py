"""Configuration module for EHR Data Pipeline"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Get the project root directory (where app.py is located)
# This file is in src/, so we go up one level
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file in project root
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

# Also try loading from current directory (for backwards compatibility)
load_dotenv()


class Config:
    """Configuration class for application settings"""
    
    # Unstructured.io API Configuration
    UNSTRUCTURED_API_KEY: Optional[str] = os.getenv("UNSTRUCTURED_API_KEY")
    UNSTRUCTURED_API_URL: str = os.getenv(
        "UNSTRUCTURED_API_URL", 
        "https://api.unstructured.io"
    )
    
    # Data field mappings for extraction
    PATIENT_FIELDS = [
        "patient_name",
        "date_of_birth",
        "mrn",
        "age",
        "gender"
    ]
    
    CLINICAL_FIELDS = [
        "vital_signs",
        "diagnoses",
        "medications",
        "allergies",
        "procedures",
        "clinical_notes"
    ]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.UNSTRUCTURED_API_KEY:
            # Provide helpful error message with file location
            env_file = PROJECT_ROOT / ".env"
            error_msg = (
                f"UNSTRUCTURED_API_KEY not found.\n\n"
                f"Please check:\n"
                f"1. The .env file exists at: {env_file}\n"
                f"2. The .env file contains: UNSTRUCTURED_API_KEY=your_api_key_here\n"
                f"3. There are no spaces around the = sign\n"
                f"4. The API key is not wrapped in quotes (unless it contains spaces)\n\n"
                f"Example .env file content:\n"
                f"UNSTRUCTURED_API_KEY=your_actual_api_key_here\n"
                f"UNSTRUCTURED_API_URL=https://api.unstructured.io"
            )
            raise ValueError(error_msg)
        return True
