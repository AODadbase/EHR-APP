"""Utility functions for EHR Data Pipeline"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any


def ensure_dir(path: str) -> None:
    """Ensure a directory exists, create if it doesn't"""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """Save data to a JSON file"""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Dict[str, Any]:
    """Load data from a JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_file_basename(filepath: str) -> str:
    """Get the base name of a file without extension"""
    return Path(filepath).stem


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
