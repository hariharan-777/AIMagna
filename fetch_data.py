import os
import shutil
from google.cloud import storage
from typing import Optional
from LocalNormalizerAgent import LocalNormalizerAgent
from BigQueryAgent import BigQueryAgent
from SchemaAnalyzerAgent import SchemaAnalyzerAgent
from adk import AgentInput
from pathlib import Path

class GoogleCloudStorageAgent:
    """
    A simple agent/wrapper to interact with Google Cloud Storage.
    """
    def __init__(self, service_account_json: Optional[str] = None):
        """
        Initialize the GCS client.
        
        Args:
            service_account_json (str, optional): Path to the service account JSON file.
                                                  If None, uses default environment credentials.
        """
        if service_account_json:
            self.client = storage.Client.from_service_account_json(service_account_json)
        else:
            # Relies on GOOGLE_APPLICATION_CREDENTIALS environment variable
            # or gcloud auth application-default login
            self.client = storage.Client()

    def fetch_dataset(self, bucket_name: str, source_blob_name: str, destination_file_name: str):
        """
        Downloads a dataset (blob) from the bucket.

        Args:
            bucket_name (str): The ID of your GCS bucket.
            source_blob_name (str): The path to the file in the bucket.
            destination_file_name (str): The local path where the file should be saved.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            
            print(f"Starting download of gs://{bucket_name}/{source_blob_name}...")
            blob.download_to_filename(destination_file_name)
            
            print(f"Success! Downloaded to {destination_file_name}")
            return True
        except Exception as e:
            print(f"Error fetching dataset: {e}")
            return False

    def download_folder(self, bucket_name: str, gcs_folder: str, local_folder: str):
        """
        Downloads all files from a GCS folder (prefix) to a local directory.

        Args:
            bucket_name (str): The ID of your GCS bucket.
            gcs_folder (str): The folder path in the bucket (prefix).
            local_folder (str): The local directory to save files to.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            # Ensure prefix ends with / to correctly match folder structure
            prefix = gcs_folder if gcs_folder.endswith('/') else gcs_folder + '/'
            blobs = list(bucket.list_blobs(prefix=prefix))
            
            if not blobs:
                print(f"No files found with prefix: {prefix}")
                return False

            print(f"Found {len(blobs)} files in {prefix}. Starting download...")

            for blob in blobs:
                if blob.name.endswith('/'):
                    continue # Skip "directory" markers

                # Calculate relative path to maintain structure inside the local folder
                if blob.name.startswith(prefix):
                    relative_path = blob.name[len(prefix):]
                else:
                    relative_path = blob.name

                local_path = os.path.join(local_folder, relative_path)
                
                # Create local directory if it doesn't exist
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                print(f"Downloading {blob.name} to {local_path}...")
                blob.download_to_filename(local_path)
            
            print("Folder download complete.")
            return True
        except Exception as e:
            print(f"Error downloading folder: {e}")
            return False

    def list_datasets(self, bucket_name: str, prefix: str = None):
        """
        Lists all the blobs in the bucket that begin with the prefix.
        """
        try:
            blobs = self.client.list_blobs(bucket_name, prefix=prefix)
            print(f"Datasets in bucket {bucket_name}:")
            for blob in blobs:
                print(f" - {blob.name}")
        except Exception as e:
            print(f"Error listing datasets: {e}")

    def list_files(self, bucket_name: str, gcs_folder: str, allowed_ext: Optional[set[str]] = None):
        """List blob names under a prefix, optionally filtering by extension."""
        prefix = gcs_folder if gcs_folder.endswith('/') else gcs_folder + '/'
        blobs = self.client.list_blobs(bucket_name, prefix=prefix)
        for blob in blobs:
            name = blob.name
            if name.endswith('/'):
                continue
            if allowed_ext is not None:
                ext = os.path.splitext(name)[1].lower()
                if ext not in allowed_ext:
                    continue
            yield name

if __name__ == "__main__":
    # Configuration
    BUCKET_NAME = "datasets-ccibt-hack25ww7-713"
    GCS_FOLDER = "datasets/uc2-multi-agent-workflow-for-intelligent-data-integration/Sample-DataSet-CommercialLending/Source-Schema-DataSets"
    LOCAL_FOLDER = "downloads/multi_agent_workflow"
    NORMALIZED_FOLDER = "normalized"
    
    # BigQuery Configuration
    UPLOAD_TO_BIGQUERY = True  # Set to False to skip BigQuery upload
    BQ_PROJECT_ID = "ccibt-hack25ww7-713"  # CHANGE THIS to your GCP project ID
    BQ_DATASET_ID = "multi_agent_workflow"     # BigQuery dataset name
    
    # Path to your service account key file (optional if using env vars)
    # SERVICE_ACCOUNT_KEY = "path/to/service-account-key.json"
    SERVICE_ACCOUNT_KEY = None 

    # Initialize agents
    agent = GoogleCloudStorageAgent(service_account_json=SERVICE_ACCOUNT_KEY)
    normalizer = LocalNormalizerAgent()
    
    if UPLOAD_TO_BIGQUERY:
        bq_agent = BigQueryAgent(
            project_id=BQ_PROJECT_ID,
            dataset_id=BQ_DATASET_ID,
            service_account_json=SERVICE_ACCOUNT_KEY
        )
    
    allowed_ext = {".csv", ".xlsx"}

    download_root = Path(LOCAL_FOLDER)
    normalized_root = Path(NORMALIZED_FOLDER)
    
    # Delete old normalized folder if it exists
    if normalized_root.exists():
        print(f"Deleting old normalized folder: {normalized_root.resolve()}")
        shutil.rmtree(normalized_root)
    
    # Create fresh normalized folder
    normalized_root.mkdir(parents=True, exist_ok=True)

    # Check if files already exist in download folder
    existing_files = sorted(
        [p for p in download_root.rglob("*") if p.is_file() and p.suffix.lower() in allowed_ext],
        key=lambda p: p.name.lower(),
    ) if download_root.exists() else []

    if existing_files:
        print(f"Found {len(existing_files)} existing files in {download_root.resolve()}")
        print("Skipping download. Starting normalization from local files...")
    else:
        print(f"No existing files found. Downloading from Bucket: {BUCKET_NAME}, Folder: {GCS_FOLDER}")
        agent.download_folder(BUCKET_NAME, GCS_FOLDER, LOCAL_FOLDER)
        
        # Re-scan for files after download
        existing_files = sorted(
            [p for p in download_root.rglob("*") if p.is_file() and p.suffix.lower() in allowed_ext],
            key=lambda p: p.name.lower(),
        )

    if not existing_files:
        print(f"No CSV/XLSX files found under: {download_root.resolve()}")
    else:
        print(f"\nNormalizing {len(existing_files)} files...")
        normalized_count = 0
        
        for candidate in existing_files:
            file_path = str(candidate.resolve())
            print(f"Normalizing: {candidate.name}")
            
            input_data = AgentInput(inputs={"file_path": file_path, "output_dir": str(normalized_root.resolve())})
            result = normalizer.run(input_data)
            
            if isinstance(result.output, str):
                print(result.output)
                if result.output.startswith("Normalization complete"):
                    normalized_count += 1
            else:
                print(f"Unexpected output type: {type(result.output)}")

        print(f"\nCompleted: {normalized_count}/{len(existing_files)} files normalized successfully.")
        
        # Upload to BigQuery
        if UPLOAD_TO_BIGQUERY and normalized_count > 0:
            bq_input = AgentInput(inputs={
                "folder_path": str(normalized_root.resolve())
            })
            bq_result = bq_agent.run(bq_input)
            
            if isinstance(bq_result.output, dict):
                if bq_result.output.get("success"):
                    print(f"BigQuery upload completed successfully!")
                    
                    # Analyze table relationships
                    schema_agent = SchemaAnalyzerAgent(
                        project_id=BQ_PROJECT_ID,
                        dataset_id=BQ_DATASET_ID,
                        service_account_json=SERVICE_ACCOUNT_KEY
                    )
                    
                    schema_input = AgentInput(inputs={"analyze_only": False})
                    schema_result = schema_agent.run(schema_input)
                    
                else:
                    print(f"BigQuery upload failed: {bq_result.output.get('error')}")
            else:
                print(bq_result.output)

