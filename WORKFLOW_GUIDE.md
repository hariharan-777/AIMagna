# Updated Workflow - Main Entry Point

## ✨ Simplified User Experience

The `main.py` has been updated with a streamlined, automatic workflow:

## 📋 New Behavior

### Option 1: 📥 Fetch Data from GCS
**Smart Download Prevention:**
- ✅ Checks if files already exist in `downloads/multi_agent_workflow/`
- ✅ If files exist → **Skips download** (prevents overwriting)
- ✅ If no files → **Proceeds with download**
- 💡 Shows message: "Delete files in downloads/multi_agent_workflow/ to re-download"

### Option 2: 🔄 Normalize Files
**Fully Automatic Processing:**
- ✅ **No file selection needed** - automatically processes ALL files in downloads
- ✅ **Clears old normalized files first** (deletes normalized/ folder contents)
- ✅ **Creates fresh normalized files** with latest data
- ✅ **Processes all formats**: CSV, Excel (.xlsx, .xls)
- ✅ **Multi-sheet support**: Excel files → multiple CSV files

**What happens:**
1. Finds all CSV/Excel files in `downloads/multi_agent_workflow/`
2. Deletes old `normalized/` folder contents
3. Processes each file automatically
4. Shows progress for each file
5. Creates BigQuery-ready CSV files

### Option 3: ⬆️ Upload to BigQuery
**Automatic Bulk Upload:**
- ✅ **Uploads ALL normalized files** automatically
- ✅ No file selection or confirmation needed
- ✅ Auto-generates table names from filenames
- ✅ Shows progress: `file.csv → dataset.table_name`
- ✅ Summary: successful/failed counts

**What happens:**
1. Scans `normalized/` folder for CSV files
2. Uploads each file to BigQuery
3. Creates tables automatically
4. Shows row counts for each upload
5. Final summary report

## 🚀 Recommended Workflow

### First Time Setup:
```powershell
python main.py
```

**Step-by-step:**
1. Press **2** - Normalizes all files (clears old, creates new)
2. Press **3** - Uploads everything to BigQuery
3. Press **4** - Start querying with AI

### Subsequent Runs:
If you add new files to `downloads/multi_agent_workflow/`:
1. Press **2** - Re-normalizes everything (auto-clears old files)
2. Press **3** - Re-uploads everything to BigQuery

### Full Automated Pipeline:
Press **5** - Runs both normalize + upload automatically

## 📊 Current Configuration

From your `.env` file:
```env
BQ_PROJECT_ID=ccibt-hack25ww7-713
BQ_DATASET_ID=multi_agent_workflow
GOOGLE_CLOUD_PROJECT=ccibt-hack25ww7-713
GOOGLE_CLOUD_LOCATION=us-central1
```

All uploads go to: `ccibt-hack25ww7-713.multi_agent_workflow`

## 🎯 Example Session

```
1. Start program: python main.py
2. Press 2 → Normalizes 6 files automatically
   - Clears old normalized/
   - Processes all files
   - Shows: "✅ Successful: 6, ❌ Failed: 0"

3. Press 3 → Uploads ~17 tables to BigQuery
   - All CSV files uploaded automatically
   - Shows: "✅ Successful: 17, ❌ Failed: 0"

4. Press 4 → Query your data
   - Ask: "What are the top 10 states by flood policies?"
   - Get instant AI-powered answers
```

## 🔄 Key Improvements

1. **No repetitive prompts** - everything is automatic
2. **Smart file management** - clears old, prevents duplicate downloads
3. **Progress visibility** - see each file being processed
4. **Error handling** - continues even if one file fails
5. **Detailed summaries** - know exactly what succeeded/failed

## 💡 Tips

- **Re-normalizing**: Just press 2 again - old files auto-deleted
- **Re-uploading**: Press 3 again - tables will be overwritten
- **Check files**: Press 6 to see what's in downloads/ and normalized/
- **AI Queries**: Press 4 anytime to query your BigQuery data

All operations are now streamlined for maximum efficiency! 🚀
