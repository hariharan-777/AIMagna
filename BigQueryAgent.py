# filename: BigQueryAgent.py

from google.cloud import bigquery
from pathlib import Path
from adk import Agent, AgentInput, AgentOutput

class BigQueryAgent(Agent):
    """
    Agent to upload normalized CSV files to Google BigQuery tables.
    """
    
    def __init__(self, project_id: str, dataset_id: str, service_account_json=None):
        """
        Initialize BigQuery Agent.
        
        Args:
            project_id: Your GCP project ID
            dataset_id: BigQuery dataset name (will be created if doesn't exist)
            service_account_json: Path to service account key (optional, uses gcloud auth if None)
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        if service_account_json:
            self.client = bigquery.Client.from_service_account_json(
                service_account_json, 
                project=project_id
            )
        else:
            self.client = bigquery.Client(project=project_id)
        
        # Ensure dataset exists
        self._ensure_dataset()
    
    def _ensure_dataset(self):
        """Create dataset if it doesn't exist."""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        try:
            self.client.get_dataset(dataset_ref)
            print(f"✓ Dataset {dataset_ref} exists.")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # Change to your preferred location
            self.client.create_dataset(dataset)
            print(f"✓ Created dataset {dataset_ref}")
    
    def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        Upload CSV file(s) to BigQuery.
        
        Expected inputs:
            - file_path: Single CSV file path to upload
            OR
            - folder_path: Folder containing CSV files to upload
            
            - table_name: (optional) Custom table name for single file upload
            - write_disposition: (optional) "WRITE_TRUNCATE" (default), "WRITE_APPEND", or "WRITE_EMPTY"
        """
        file_path = agent_input.inputs.get("file_path")
        folder_path = agent_input.inputs.get("folder_path")
        table_name = agent_input.inputs.get("table_name")
        write_disposition = agent_input.inputs.get("write_disposition", "WRITE_TRUNCATE")
        
        # Single file upload
        if file_path:
            result = self._upload_single_file(file_path, table_name, write_disposition)
            return AgentOutput(output=result)
        
        # Folder upload
        elif folder_path:
            result = self._upload_folder(folder_path, write_disposition)
            return AgentOutput(output=result)
        
        else:
            return AgentOutput(output={
                "error": "Provide either 'file_path' or 'folder_path' in inputs."
            })
    
    def _upload_single_file(self, csv_path: str, table_name: str = None, 
                           write_disposition: str = "WRITE_TRUNCATE") -> dict:
        """Upload a single CSV file to BigQuery."""
        try:
            csv_file = Path(csv_path)
            if not csv_file.exists():
                return {
                    "success": False,
                    "error": f"File not found: {csv_path}"
                }
            
            # Generate table name from filename if not provided
            if not table_name:
                table_name = csv_file.stem.replace("-", "_").replace(" ", "_").replace(".", "_")
            
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            # Configure load job
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                autodetect=True,  # Auto-detect schema from CSV
                write_disposition=write_disposition,
            )
            
            print(f"  Uploading {csv_file.name} → {table_id}")
            
            with open(csv_path, "rb") as source_file:
                job = self.client.load_table_from_file(
                    source_file, 
                    table_id, 
                    job_config=job_config
                )
            
            job.result()  # Wait for job completion
            
            table = self.client.get_table(table_id)
            message = f"✓ Loaded {table.num_rows} rows into {table_id}"
            print(f"  {message}")
            
            return {
                "success": True,
                "table_id": table_id,
                "rows": table.num_rows,
                "file": csv_file.name
            }
            
        except Exception as e:
            error_msg = f"✗ Failed to upload {csv_path}: {e}"
            print(f"  {error_msg}")
            return {
                "success": False,
                "error": str(e),
                "file": csv_path
            }
    
    def _upload_folder(self, folder_path: str, 
                      write_disposition: str = "WRITE_TRUNCATE") -> dict:
        """Upload all CSV files in a folder to BigQuery."""
        folder = Path(folder_path)
        if not folder.exists():
            return {
                "success": False,
                "error": f"Folder not found: {folder_path}"
            }
        
        csv_files = list(folder.glob("*.csv"))
        if not csv_files:
            return {
                "success": False,
                "error": f"No CSV files found in {folder_path}"
            }
        
        print(f"\n{'='*60}")
        print(f"UPLOADING {len(csv_files)} FILES TO BIGQUERY")
        print(f"{'='*60}")
        
        results = []
        success_count = 0
        failed_count = 0
        
        for csv_file in csv_files:
            result = self._upload_single_file(str(csv_file), write_disposition=write_disposition)
            results.append(result)
            
            if result.get("success"):
                success_count += 1
            else:
                failed_count += 1
        
        summary = {
            "success": True,
            "total_files": len(csv_files),
            "succeeded": success_count,
            "failed": failed_count,
            "results": results
        }
        
        print(f"\n{'='*60}")
        print(f"✓ Upload Summary: {success_count} succeeded, {failed_count} failed")
        print(f"{'='*60}\n")
        
        return summary
