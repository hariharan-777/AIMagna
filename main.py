#!/usr/bin/env python3
"""
Main Entry Point for Real Estate Data Pipeline
Orchestrates: Data Fetching → Normalization → BigQuery Upload → AI Querying
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_menu():
    """Display the main menu."""
    print_header("REAL ESTATE DATA PIPELINE - MAIN MENU")
    print("1. 📥 Fetch Data from Google Cloud Storage")
    print("2. 🔄 Normalize Local Files (CSV/Excel → BigQuery-ready CSV)")
    print("3. ⬆️  Upload Normalized Files to BigQuery")
    print("4. 🤖 Query BigQuery with Vertex AI (Natural Language)")
    print("5. 🚀 Run Full Pipeline (Normalize All + Upload)")
    print("6. 📊 List Available Files")
    print("7. ❌ Exit")
    print()

def fetch_data_menu():
    """Handle data fetching from GCS."""
    print_header("FETCH DATA FROM GCS")
    
    from fetch_data import GoogleCloudStorageAgent
    
    # Check if downloads folder has files
    downloads_dir = Path("downloads/multi_agent_workflow")
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    existing_files = list(downloads_dir.glob("*"))
    if existing_files:
        print(f"⚠️  Found {len(existing_files)} existing file(s) in downloads folder:\n")
        for f in existing_files[:10]:  # Show first 10
            if f.is_file():
                print(f"  • {f.name}")
        if len(existing_files) > 10:
            print(f"  ... and {len(existing_files) - 10} more")
        
        print(f"\n❌ Files already exist. Download skipped.")
        print("\ud83d\udca1 Delete files in downloads/multi_agent_workflow/ to re-download")
        return
    
    # Default configuration
    DEFAULT_BUCKET = os.getenv("GCS_BUCKET_NAME", "datasets-ccibt-hack25ww7-713")
    DEFAULT_FOLDER = os.getenv("GCS_FOLDER", "datasets/uc2-multi-agent-workflow-for-intelligent-data-integration/Sample-DataSet-CommercialLending/Source-Schema-DataSets")
    
    # Get configuration
    bucket_name = input(f"Enter GCS bucket name (default: {DEFAULT_BUCKET}): ").strip()
    if not bucket_name:
        bucket_name = DEFAULT_BUCKET
    
    source_path = input(f"Enter source path - file or folder (default: folder download): ").strip()
    
    # Initialize agent
    agent = GoogleCloudStorageAgent()
    
    # If no path provided, download entire default folder
    if not source_path:
        print(f"\n📁 Downloading folder: gs://{bucket_name}/{DEFAULT_FOLDER}")
        print(f"📂 To: {downloads_dir}")
        
        success = agent.download_folder(bucket_name, DEFAULT_FOLDER, str(downloads_dir))
        
        if success:
            downloaded_files = list(downloads_dir.glob("*"))
            print(f"\n✅ Successfully downloaded {len(downloaded_files)} file(s)")
        else:
            print("\n❌ Download failed")
    else:
        # Single file download
        dest_file = f"{downloads_dir}/{Path(source_path).name}"
        
        print(f"\n📄 Downloading file: gs://{bucket_name}/{source_path}")
        print(f"📂 To: {dest_file}")
        
        success = agent.fetch_dataset(bucket_name, source_path, dest_file)
        
        if success:
            print(f"\n✅ Successfully downloaded to {dest_file}")
        else:
            print("\n❌ Download failed")

def normalize_files_menu():
    """Handle file normalization."""
    print_header("NORMALIZE FILES")
    
    # Check downloads folder for files
    downloads_dir = Path("downloads/multi_agent_workflow")
    
    if not downloads_dir.exists():
        print(f"\u274c Directory not found: {downloads_dir}")
        print("\ud83d\udca1 Run option 1 to fetch data first, or manually add files to downloads/multi_agent_workflow/")
        return
    
    files = list(downloads_dir.glob("*.csv")) + list(downloads_dir.glob("*.xlsx")) + list(downloads_dir.glob("*.xls"))
    
    if not files:
        print(f"❌ No CSV or Excel files found in {downloads_dir}")
        print("\ud83d\udca1 Add files to downloads/multi_agent_workflow/ folder")
        return
    
    # Always process all files - simplified workflow
    print(f"📁 Found {len(files)} file(s) to process:\n")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    
    print("\n🔄 Processing all files...")
    
    # Clear old normalized files first
    normalized_dir = Path("normalized")
    if normalized_dir.exists():
        print(f"\n🗑️  Cleaning old normalized files...")
        import shutil
        shutil.rmtree(normalized_dir)
        print(f"✅ Cleared normalized directory")
    
    normalized_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all files
    normalize_all_files(files)
    
def normalize_all_files(files=None):
    """Normalize all files in downloads directory."""
    from LocalNormalizerAgent import LocalNormalizerAgent
    from adk import AgentInput
    
    if files is None:
        downloads_dir = Path("downloads/multi_agent_workflow")
        
        if not downloads_dir.exists():
            print(f"❌ Directory not found: {downloads_dir}")
            return
        
        files = list(downloads_dir.glob("*.csv")) + list(downloads_dir.glob("*.xlsx")) + list(downloads_dir.glob("*.xls"))
        
        if not files:
            print(f"❌ No CSV or Excel files found in {downloads_dir}")
            return
    
    agent = LocalNormalizerAgent()
    output_dir = "normalized"
    
    successful = 0
    failed = 0
    
    for file_path in files:
        print(f"\n{'='*70}")
        print(f"🔄 Processing: {file_path.name}")
        print(f"{'='*70}")
        is_excel = str(file_path).lower().endswith(('.xlsx', '.xls'))
        
        try:
            result = agent.run(AgentInput(inputs={
                "file_path": str(file_path),
                "output_dir": output_dir,
                "process_all_sheets": is_excel
            }))
            print(f"✅ Success: {file_path.name}")
            successful += 1
        except Exception as e:
            print(f"❌ Failed: {file_path.name} - {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"NORMALIZATION COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output: {output_dir}/")
    print(f"{'='*70}")

def upload_to_bigquery_menu():
    """Handle BigQuery uploads."""
    print_header("UPLOAD TO BIGQUERY")
    
    from BigQueryAgent import BigQueryAgent
    from adk import AgentInput
    
    # Get configuration from .env
    project_id = os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    if not project_id or not dataset_id:
        print("❌ Please set BQ_PROJECT_ID and BQ_DATASET_ID in .env file")
        return
    
    print(f"Project: {project_id}")
    print(f"Dataset: {dataset_id}\n")
    
    normalized_dir = Path("normalized")
    
    if not normalized_dir.exists():
        print(f"❌ Normalized directory not found. Run option 2 to normalize files first.")
        return
    
    csv_files = list(normalized_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {normalized_dir}")
        print("💡 Run option 2 to normalize files first")
        return
    
    print(f"📁 Found {len(csv_files)} CSV file(s):\n")
    for i, f in enumerate(csv_files[:15], 1):  # Show first 15
        print(f"  {i}. {f.name}")
    if len(csv_files) > 15:
        print(f"  ... and {len(csv_files) - 15} more")
    
    # Always upload all files - simplified workflow
    print(f"\n⬆️  Uploading all {len(csv_files)} file(s) to BigQuery...")
    
    agent = BigQueryAgent(project_id=project_id, dataset_id=dataset_id)
    
    successful = 0
    failed = 0
    
    for csv_file in csv_files:
        table_name = csv_file.stem.lower().replace('-', '_').replace(' ', '_').replace('.', '_')
        print(f"\n⬆️  {csv_file.name} → {dataset_id}.{table_name}")
        
        try:
            result = agent.run(AgentInput(inputs={
                "file_path": str(csv_file),
                "table_name": table_name
            }))
            output = result.output
            if isinstance(output, dict) and output.get("success"):
                rows = output.get('rows_loaded', '?')
                print(f"   ✅ Uploaded {rows} rows")
                successful += 1
            else:
                print(f"   ❌ {output}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"UPLOAD COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"🗄️  Dataset: {project_id}.{dataset_id}")
    print(f"{'='*70}")

def query_with_ai_menu():
    """Handle AI queries."""
    print_header("QUERY WITH VERTEX AI")
    
    from VertexAIQueryAgent import VertexAIQueryAgent
    from adk import AgentInput
    
    # Get configuration
    project_id = os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BQ_DATASET_ID")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    if not project_id or not dataset_id:
        print("❌ Please set BQ_PROJECT_ID and BQ_DATASET_ID in .env file")
        return
    
    print(f"Connected to: {project_id}.{dataset_id}\n")
    
    # Initialize agent
    print("Initializing Vertex AI Query Agent...")
    agent = VertexAIQueryAgent(
        project_id=project_id,
        dataset_id=dataset_id,
        location=location
    )
    
    print("\n💡 Enter your questions in natural language (or 'back' to return)")
    print("Examples:")
    print("  - What are the top 5 states by flood zone policies?")
    print("  - Show me average property prices by state")
    print("  - Which ZIP codes have the highest SAFMR rates?\n")
    
    while True:
        query = input("Your question: ").strip()
        
        if query.lower() in ['back', 'exit', 'quit']:
            break
        
        if not query:
            continue
        
        print("\n🤖 Processing your query...")
        result = agent.run(AgentInput(inputs={
            "query": query,
            "mode": "data"
        }))
        
        output = result.output
        
        if "error" in output:
            print(f"\n❌ Error: {output['error']}")
        else:
            print(f"\n📊 Response:\n{output.get('response', 'No response')}")
            print(f"\nRows returned: {output.get('row_count', 0)}")

def list_files_menu():
    """List available files."""
    print_header("AVAILABLE FILES")
    
    downloads_dir = Path("downloads/multi_agent_workflow")
    normalized_dir = Path("normalized")
    
    print("\ud83d\udcc2 Source Files (downloads/multi_agent_workflow):")
    if downloads_dir.exists():
        files = list(downloads_dir.glob("*"))
        if files:
            for f in files:
                if f.is_file():
                    size = f.stat().st_size / (1024*1024)  # MB
                    print(f"  • {f.name} ({size:.2f} MB)")
        else:
            print("  (empty)")
    else:
        print("  (directory not found)")
    
    print("\n📂 Normalized Files (normalized):")
    if normalized_dir.exists():
        files = list(normalized_dir.glob("*.csv"))
        if files:
            for f in files:
                size = f.stat().st_size / (1024*1024)  # MB
                print(f"  • {f.name} ({size:.2f} MB)")
        else:
            print("  (empty)")
    else:
        print("  (directory not found)")

def run_full_pipeline():
    """Run complete pipeline: normalize all + upload all."""
    print_header("FULL PIPELINE EXECUTION")
    
    # Check if files exist
    downloads_dir = Path("downloads/multi_agent_workflow")
    if not downloads_dir.exists() or not list(downloads_dir.glob("*")):
        print("\u274c No files found in downloads/multi_agent_workflow/")
        print("\ud83d\udca1 Run option 1 to fetch data first, or manually add files")
        return
    
    print("This will:")
    print("1. Clear old normalized files")
    print("2. Normalize all files in downloads/multi_agent_workflow")
    print("3. Upload all normalized files to BigQuery")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        return
    
    # Clear old normalized files
    normalized_dir = Path("normalized")
    if normalized_dir.exists():
        print(f"\n🗑️  Cleaning old normalized files...")
        import shutil
        shutil.rmtree(normalized_dir)
        print(f"✅ Cleared normalized directory")
    
    normalized_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Normalize
    print("\n" + "="*70)
    print("STEP 1: NORMALIZING FILES")
    print("="*70)
    
    files = list(downloads_dir.glob("*.csv")) + list(downloads_dir.glob("*.xlsx")) + list(downloads_dir.glob("*.xls"))
    normalize_all_files(files)
    
    # Step 2: Upload
    print("\n" + "="*70)
    print("STEP 2: UPLOADING TO BIGQUERY")
    print("="*70)
    
    from BigQueryAgent import BigQueryAgent
    from adk import AgentInput
    
    project_id = os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    if not project_id or not dataset_id:
        print("❌ Please set BQ_PROJECT_ID and BQ_DATASET_ID in .env file")
        return
    
    csv_files = list(normalized_dir.glob("*.csv"))
    
    if not csv_files:
        print("❌ No normalized CSV files found")
        return
    
    agent = BigQueryAgent(project_id=project_id, dataset_id=dataset_id)
    
    successful = 0
    failed = 0
    
    for csv_file in csv_files:
        table_name = csv_file.stem.lower().replace('-', '_').replace(' ', '_').replace('.', '_')
        print(f"\n⬆️  {csv_file.name} → {table_name}")
        
        try:
            result = agent.run(AgentInput(inputs={
                "file_path": str(csv_file),
                "table_name": table_name
            }))
            output = result.output
            if isinstance(output, dict) and output.get("success"):
                rows = output.get('rows_loaded', '?')
                print(f"   ✅ {rows} rows")
                successful += 1
            else:
                print(f"   ❌ {output}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Uploaded: {successful} tables")
    print(f"❌ Failed: {failed}")
    print(f"🗄️  Dataset: {project_id}.{dataset_id}")
    print(f"{'='*70}")

def main():
    """Main entry point."""
    
    # Check .env file
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found. Some features may not work.")
        print("Please create a .env file with your configuration.\n")
    
    while True:
        print_menu()
        choice = input("Enter your choice (1-7): ").strip()
        
        try:
            if choice == "1":
                fetch_data_menu()
            elif choice == "2":
                normalize_files_menu()
            elif choice == "3":
                upload_to_bigquery_menu()
            elif choice == "4":
                query_with_ai_menu()
            elif choice == "5":
                run_full_pipeline()
            elif choice == "6":
                list_files_menu()
            elif choice == "7":
                print("\n👋 Goodbye!")
                sys.exit(0)
            else:
                print("\n❌ Invalid choice. Please enter 1-7.")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
