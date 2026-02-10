# EHR Data Pipeline Demo

A RAG (Retrieval-Augmented Generation) system demo that processes unstructured patient admission note PDFs using Unstructured.io, extracts key clinical data, and provides a searchable UI for nurses to quickly find and export information for discharge documents.

## Features

- **PDF Processing**: Extract structured data from patient admission notes using Unstructured.io API
- **Data Extraction**: Automatically extract patient demographics, vital signs, diagnoses, medications, allergies, procedures, and clinical notes
- **Searchable UI**: Streamlit-based dashboard for searching and filtering across multiple documents
- **Export Options**: Export data as structured JSON or formatted discharge documents
- **Multi-Document Support**: Process and consolidate data from multiple admission notes

## Architecture

```
PDF Files → Unstructured.io API → Document Elements → Data Extraction → Structured JSON → Streamlit UI
```


## Project Structure

```
ehr-data-pipeline/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py                     # Streamlit main application
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration and API keys
│   ├── pdf_processor.py       # Unstructured.io integration
│   ├── data_extractor.py      # Extract structured data from elements
│   ├── formatter.py           # Format data for discharge documents
│   └── utils.py               # Helper functions
├── data/
│   ├── samples/               # Sample PDF files (add your PDFs here)
│   └── processed/             # Processed JSON outputs
└── templates/
    └── discharge_template.txt # Discharge document template
```

## Setup

### Prerequisites

- Python 3.8 or higher
- Unstructured.io API key (get one at https://www.unstructured.io/)
- OpenAI API key (get one at https://platform.openai.com/)

### Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create a `.env` file in the **project root** (same directory as `app.py`)
   - Add your API keys:
     ```
     UNSTRUCTURED_API_KEY=your_api_key_here
     UNSTRUCTURED_API_URL=https://api.unstructured.io
     OPENAI_API_KEY=your_openai_api_key_here
     OPENAI_MODEL=gpt-4o-mini
     ```
   - **Important**: 
     - File must be in project root (where `app.py` is located)
     - No spaces around `=`
     - File name must be exactly `.env` (not `.env.txt`)
   - **Verify setup**: Run `python check_env.py` to test if the .env file is being read correctly

## Usage

### Quick Start

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to the URL shown in the terminal (typically http://localhost:8501)

3. **Upload & Process**:
   - Go to the "Upload & Process" tab
   - Upload one or more admission note PDFs
   - Click "Process PDFs" and wait for completion

4. **View Data**:
   - **Dashboard**: View all extracted information for a selected document
   - **Search**: Find specific terms across all documents (e.g., "pneumonia", "metoprolol")
   - **Export**: Download data as JSON or formatted discharge documents




