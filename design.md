# AIMagna: System Design Document

## 1. Introduction & Overview

**AIMagna** is an end-to-end data engineering and analytics pipeline designed to streamline the process of ingesting, normalizing, storing, and querying large datasets. It leverages a multi-agent architecture built on Python and Google Cloud Platform (GCP) services.

The system's primary goal is to take raw, semi-structured data files (like CSVs and Excel spreadsheets) from a source, automatically clean and transform them into a queryable format, load them into a data warehouse (Google BigQuery), and provide a natural language interface for data analysis using Vertex AI's Gemini models.

This document details the architecture, core components, and operational flow of the AIMagna workspace.

## 2. System Architecture

The system is designed as a modular, agent-based pipeline. Each major function (fetching, normalizing, uploading, querying) is encapsulated within a dedicated "Agent" class. A central command-line interface (CLI) orchestrates these agents to execute user-defined tasks.

**High-Level Architectural Diagram:**

```
[User] -> [main.py CLI] -> Orchestrates Agents -> [GCP Services]
   ^                                                    |
   |                                                    |
   +--------------------[AI Response]--------------------+
```

**Component Interaction Flow:**

1.  **Data Ingestion:** `GoogleCloudStorageAgent` downloads raw files from a GCS bucket into a local `downloads/` directory.
2.  **Data Normalization:** `LocalNormalizerAgent` reads files from `downloads/`, performs extensive cleaning and transformation, and saves BigQuery-ready CSVs to the `normalized/` directory.
3.  **Data Loading:** `BigQueryAgent` picks up the normalized CSVs from `normalized/` and uploads them into corresponding tables within a specified BigQuery dataset.
4.  **Schema Analysis:** `SchemaAnalyzerAgent` can inspect the BigQuery dataset to identify potential relationships between tables and automatically create `VIEW`s to represent these joins.
5.  **AI-Powered Querying:** `VertexAIQueryAgent` accepts a natural language question from the user, generates a BigQuery SQL query using Vertex AI Gemini, executes it, and then uses Gemini again to synthesize a human-readable answer from the query results.

## 3. Core Components

### 3.1. Agent Interaction Model: Orchestration

A key design principle of AIMagna is its use of an **orchestrated multi-agent workflow**. This is distinct from conversational or autonomous agent systems where agents might communicate and make decisions collaboratively.

*   **Central Orchestrator**: The `main.py` script acts as a central orchestrator or "conductor". It is responsible for invoking the correct agent based on user input and managing the overall sequence of operations. For example, the "Run Full Pipeline" option explicitly calls the normalization agent first, and then the upload agent.

*   **Indirect Communication**: Agents do not talk directly to each other. Instead, they communicate indirectly through shared resources, following an assembly-line pattern:
    *   **File System**: The `GoogleCloudStorageAgent` writes files to the `downloads/` directory. The `LocalNormalizerAgent` reads from `downloads/` and writes its output to the `normalized/` directory.
    *   **Data Warehouse**: The `BigQueryAgent` reads from `normalized/` and loads data into Google BigQuery. The `VertexAIQueryAgent` then reads from BigQuery to answer user questions.

*   **No Direct Agent-to-Agent Calls**: An agent never decides which agent to call next. This logic is centralized in the orchestrator (`main.py`), making the overall data flow predictable, debuggable, and easy to manage.

---

The system is built around a set of specialized Python classes (Agents) that follow a simple, common interface defined in `adk.py`.

#### 3.2. Agent Development Kit (`adk.py`)

This simple module provides the foundational building blocks for all agents, ensuring a consistent interface.
*   `AgentInput`: A wrapper for data passed *to* an agent.
*   `AgentOutput`: A wrapper for data returned *from* an agent.
*   `Agent`: An abstract base class with a single `run` method that all concrete agents must implement.

#### 3.3. Data Ingestion (`fetch_data.py`)

*   **`GoogleCloudStorageAgent`**:
    *   **Purpose**: To connect to Google Cloud Storage and download data.
    *   **Functionality**:
        *   Authenticates with GCP using application default credentials.
        *   Downloads a single file (`fetch_dataset`).
        *   Downloads all files within a specified GCS folder/prefix (`download_folder`).
        *   Lists available files in a bucket.
    *   **Interaction**: It is triggered by the user via the main menu to populate the local `downloads/multi_agent_workflow/` directory.

#### 3.4. Data Normalization (`LocalNormalizerAgent.py`)

*   **`LocalNormalizerAgent`**:
    *   **Purpose**: To be the "brains" of the ETL process, transforming raw, messy data into clean, structured CSVs suitable for BigQuery.
    *   **Key Functionality**:
        *   **File Handling**: Reads both CSV and Excel (`.xls`, `.xlsx`) files.
        *   **Excel Sheet Processing**: Can process a single sheet or iterate through *all* sheets in an Excel workbook, saving each as a separate normalized CSV.
        *   **Column Name Normalization**: Cleans column headers by stripping whitespace, removing special characters, and replacing spaces with underscores. It intelligently infers names for unnamed columns.
        *   **Data Type Conversion**: Converts columns to BigQuery-compatible types (e.g., `datetime` to ISO strings).
        *   **Text Cleaning**: Removes null bytes, newlines, and other problematic characters from text fields to prevent CSV parsing errors.
        *   **Relationship Detection (for Excel)**: When processing all sheets of an Excel file, it attempts to identify potential foreign key relationships between the sheets based on common column names.

#### 3.5. Data Loading (`BigQueryAgent.py`)

*   **`BigQueryAgent`**:
    *   **Purpose**: To manage the loading of data into Google BigQuery.
    *   **Functionality**:
        *   Ensures the target BigQuery dataset exists, creating it if necessary.
        *   Uploads a single CSV file or all CSV files from a specified folder.
        *   Automatically generates a valid BigQuery table name from the source filename.
        *   Uses BigQuery's `autodetect` feature to infer the table schema.
        *   Sets the `write_disposition` to `WRITE_TRUNCATE` by default, meaning it overwrites the table on each run.

#### 3.6. Schema Analysis (`SchemaAnalyzerAgent.py`)

*   **`SchemaAnalyzerAgent`**:
    *   **Purpose**: To analyze the schemas of tables within a BigQuery dataset and discover potential relationships.
    *   **Functionality**:
        *   Fetches the schema for all tables in the dataset.
        *   Identifies potential relationships by looking for common column names with matching data types.
        *   Can automatically generate and create SQL `VIEW`s in BigQuery that perform a `LEFT JOIN` on the discovered relationships, simplifying future queries.

#### 3.7. AI-Powered Querying (`VertexAIQueryAgent.py`)

*   **`VertexAIQueryAgent`**:
    *   **Purpose**: To provide a natural language interface for querying the data in BigQuery.
    *   **Two-Step AI Process**:
        1.  **SQL Generation**: It first constructs a detailed prompt for the Gemini model. This prompt includes the user's question and the complete schema of all available tables in the BigQuery dataset. It then asks the model to return only a valid BigQuery SQL query.
        2.  **Response Generation**: After executing the generated SQL and retrieving the results, it constructs a second prompt. This prompt includes the original question, the SQL query used, and a summary of the data returned. It then asks the model to provide a conversational, analytical answer based on the results.
    *   **Result**: The user receives a direct answer to their question without needing to write any SQL.

## 4. Data Flow & Workspace Structure

The project follows a clear, sequential data flow, reflected in the directory structure.

1.  **Configuration (`.env`)**: GCP project details (`BQ_PROJECT_ID`, `BQ_DATASET_ID`) are stored here.
2.  **Raw Data (`downloads/multi_agent_workflow/`)**: This is the landing zone for raw data fetched from GCS. The pipeline starts here.
3.  **Normalized Data (`normalized/`)**: This is the staging area. `LocalNormalizerAgent` writes its clean, BigQuery-ready CSV output here. This directory is typically cleared and recreated on each run to ensure freshness.
4.  **Data Warehouse (Google BigQuery)**: The final destination for the data, where it is stored in structured tables, ready for analysis by the `VertexAIQueryAgent`.

## 5. User Interface (`main.py`)

The `main.py` script serves as the central orchestrator, providing a simple, menu-driven CLI for the user to interact with the pipeline.

*   **Menu Options**:
    1.  **Fetch Data**: Triggers the `GoogleCloudStorageAgent`.
    2.  **Normalize Files**: Triggers the `LocalNormalizerAgent` on all files in the `downloads` directory.
    3.  **Upload to BigQuery**: Triggers the `BigQueryAgent` on all files in the `normalized` directory.
    4.  **Query with Vertex AI**: Initiates an interactive session with the `VertexAIQueryAgent`.
    5.  **Run Full Pipeline**: Executes steps 2 and 3 in sequence for a complete "normalize and upload" workflow.
    6.  **Exit**: Terminates the application.

The interface includes robust error handling and user-friendly prompts to guide the user.

## 6. Setup & Validation

The workspace includes scripts to ensure a smooth setup and development experience.

*   **`build.py`**: An automated setup script that:
    *   Installs dependencies from `requirements.txt`.
    *   Compiles Python files.
    *   Runs validation checks.
    *   Creates necessary directories (`downloads`, `normalized`).
    *   Checks for the `.env` file.
*   **`validate_workspace.py`**: A dedicated script to check for syntax errors, import issues, and correct environment setup. This is crucial for maintaining code health.
*   **`quick_check.py`**: A faster, lightweight version of the validation script for quick checks during development.

## 7. Standalone Scripts

In addition to the main application, several scripts can be run independently for specific tasks.

*   **`fetch_data.py`**: Can be run directly to download, normalize, and upload all data in a single, non-interactive execution.
*   **`query_bigquery.py`**: Provides a dedicated, interactive CLI for querying the BigQuery dataset with natural language, separate from the main menu.
*   **`LocalNormalizerAgent.py`**: Can be executed with a file path as an argument to normalize a single file and see detailed output and BigQuery `bq load` command suggestions.