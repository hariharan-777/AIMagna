# Real Estate Data Pipeline - Quick Start Guide

## 🚀 Single Entry Point

All agents are now accessible through one main program:

```powershell
python main.py
```

## 📋 Menu Options

### 1. 📥 Fetch Data from GCS
Download files from Google Cloud Storage bucket to local storage.

### 2. 🔄 Normalize Files
Convert CSV/Excel files to BigQuery-ready format:
- **Single file**: Normalize one specific file
- **Batch process**: Normalize all files in `downloads/multi_agent_workflow/`
- **Excel multi-sheet**: Automatically processes all sheets

### 3. ⬆️ Upload to BigQuery
Upload normalized CSV files to BigQuery tables:
- **All files**: Upload everything in `normalized/` folder
- **Single file**: Select specific file to upload

### 4. 🤖 Query with AI
Ask questions in natural language using Vertex AI:
- Converts questions to SQL automatically
- Executes queries on BigQuery
- Returns AI-generated natural language responses

### 5. 🚀 Full Pipeline
Run complete workflow automatically:
1. Normalize all files in downloads
2. Upload all to BigQuery

### 6. 📊 List Files
View available source and normalized files

### 7. ❌ Exit
Close the program

## 📁 Directory Structure

```
d:\RAG\1512\
├── main.py                          # 👈 START HERE
├── .env                             # Configuration
├── downloads/
│   └── multi_agent_workflow/           # Raw data files
├── normalized/                      # Processed CSV files
└── agents/
    ├── LocalNormalizerAgent.py     # File normalization
    ├── BigQueryAgent.py            # BigQuery uploads
    ├── VertexAIQueryAgent.py       # AI queries
    └── fetch_data.py               # GCS downloads
```

## ⚙️ Configuration (.env file)

Required environment variables:

```env
BQ_PROJECT_ID=your-gcp-project-id
BQ_DATASET_ID=your-bigquery-dataset
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

## 🎯 Quick Workflow

### First Time Setup:
```powershell
# 1. Install dependencies
pip install -r requirements.txt
pip install python-dotenv openpyxl

# 2. Configure .env file
# Add your GCP credentials

# 3. Run main program
python main.py
```

### Typical Usage:
1. Run `python main.py`
2. Choose option **5** (Full Pipeline) to process all files
3. Choose option **4** to start querying your data with AI

### Example AI Queries:
- "What are the top 10 states by flood zone policies?"
- "Show me average SAFMR rates by ZIP code"
- "Which states have the most real estate listings?"
- "What are the total financial losses by state?"

## 🛠️ Individual Agent Usage

You can still run agents directly if needed:

```powershell
# Normalize a single file
python LocalNormalizerAgent.py path/to/file.xlsx normalized/

# Query with AI
python VertexAIQueryAgent.py "your natural language question"
```

## 📊 Supported File Types

- **CSV** (.csv)
- **Excel** (.xlsx, .xls) - all sheets processed automatically
- **Large files** - optimized for files with millions of rows

## ✨ Features

- ✅ Automatic schema detection
- ✅ Multi-sheet Excel support
- ✅ Relationship detection between sheets
- ✅ BigQuery data type optimization
- ✅ Natural language querying with AI
- ✅ Error handling and validation
- ✅ Progress tracking

## 🔧 Troubleshooting

**"Missing .env file"**
- Create `.env` file with required variables

**"File not found"**
- Ensure files are in `downloads/multi_agent_workflow/`

**"BigQuery authentication error"**
- Set `GOOGLE_APPLICATION_CREDENTIALS` in .env
- Or run: `gcloud auth application-default login`

**"openpyxl not found"**
- Run: `pip install openpyxl`

## 📞 Support

For issues or questions, check the error messages in the terminal output.
