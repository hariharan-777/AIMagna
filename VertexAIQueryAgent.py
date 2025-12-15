# filename: VertexAIQueryAgent.py

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import bigquery
from adk import Agent, AgentInput, AgentOutput
import json
import os
from dotenv import load_dotenv

class VertexAIQueryAgent(Agent):
    """
    Agent that uses Vertex AI Gemini to query BigQuery tables
    and provide natural language responses.
    """
    
    def __init__(self, project_id: str, dataset_id: str, location: str = "us-central1", 
                 service_account_json=None):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Use a stable Gemini model
        self.model = GenerativeModel("gemini-2.5-flash")
        
        # Initialize BigQuery client
        if service_account_json:
            self.bq_client = bigquery.Client.from_service_account_json(
                service_account_json, 
                project=project_id
            )
        else:
            self.bq_client = bigquery.Client(project=project_id)
        
        # Get table schemas
        self.table_schemas = self._get_table_schemas()
    
    def _get_table_schemas(self):
        schemas = {}
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        try:
            tables = list(self.bq_client.list_tables(dataset_ref))
            for table in tables:
                table_id = f"{dataset_ref}.{table.table_id}"
                table_obj = self.bq_client.get_table(table_id)
                schemas[table.table_id] = {
                    "columns": [(field.name, field.field_type) for field in table_obj.schema],
                    "num_rows": table_obj.num_rows,
                    "description": table_obj.description or "No description"
                }
        except Exception as e:
            print(f"Warning: Could not load table schemas: {e}")
        return schemas
    
    def run(self, agent_input: AgentInput) -> AgentOutput:
        user_query = agent_input.inputs.get("query")
        mode = agent_input.inputs.get("mode", "data")
        
        if not user_query:
            return AgentOutput(output={"error": "Please provide a 'query' in inputs."})
        
        print(f"\n{'='*60}\nPROCESSING QUERY WITH VERTEX AI GEMINI\n{'='*60}")
        print(f"Question: {user_query}\n")
        
        sql_query = self._generate_sql(user_query)
        if not sql_query:
            return AgentOutput(output={"error": "Failed to generate SQL query", "query": user_query})
        
        print(f"Generated SQL:\n{sql_query}\n")
        
        if mode == "sql":
            return AgentOutput(output={"success": True, "query": user_query, "sql": sql_query})
        
        # Execute query
        try:
            query_job = self.bq_client.query(sql_query)
            results = query_job.result()
            rows = [dict(row) for row in results]
            print(f"✓ Retrieved {len(rows)} rows\n")
            
            response = self._generate_response(user_query, sql_query, rows)
            return AgentOutput(output={
                "success": True,
                "query": user_query,
                "sql": sql_query,
                "row_count": len(rows),
                "data": rows[:100],
                "response": response
            })
        except Exception as e:
            print(f"✗ Query execution failed: {e}\n")
            return AgentOutput(output={"error": f"Query execution failed: {e}", "query": user_query, "sql": sql_query})
    
    def _generate_sql(self, user_query: str) -> str:
        schema_context = "Available BigQuery tables:\n\n"
        for table_name, schema in self.table_schemas.items():
            schema_context += f"Table: {self.project_id}.{self.dataset_id}.{table_name}\n"
            schema_context += f"  Rows: {schema['num_rows']:,}\n  Columns:\n"
            for col_name, col_type in schema['columns'][:10]:
                schema_context += f"    - {col_name} ({col_type})\n"
            if len(schema['columns']) > 10:
                schema_context += f"    ... and {len(schema['columns']) - 10} more columns\n"
            schema_context += "\n"
        
        prompt = f"""You are a SQL expert. Generate a BigQuery SQL query to answer the following question.

{schema_context}

Question: {user_query}

Requirements:
- Use standard BigQuery SQL syntax
- Include fully qualified table names (project.dataset.table)
- Limit results to 1000 rows unless otherwise specified
- Use SAFE_CAST for numeric conversions
- Return ONLY the SQL query, no explanations

SQL Query:"""
        
        try:
            response = self.model.generate_content(prompt)
            # Access text safely
            sql_query = response.candidates[0].content.parts[0].text.strip()
            # Cleanup
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip().rstrip(";")
            return sql_query
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return None
    
    def _generate_response(self, user_query: str, sql_query: str, data: list) -> str:
        if len(data) == 0:
            data_summary = "No results found."
        elif len(data) <= 5:
            data_summary = json.dumps(data, indent=2, default=str)
        else:
            data_summary = f"First 5 rows:\n{json.dumps(data[:5], indent=2, default=str)}\n\nTotal rows: {len(data)}"
        
        prompt = f"""You are a data analyst. Provide a clear, concise answer to the user's question based on the query results.

User Question: {user_query}
SQL Query Used: {sql_query}
Query Results:
{data_summary}

Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            return f"Generated {len(data)} results. Unable to generate natural language response: {e}"


if __name__ == "__main__":
    import sys
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Configuration - Read from .env file
    PROJECT_ID = os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    DATASET_ID = os.getenv("BQ_DATASET_ID")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Optional: Path to service account JSON key file
    # If not provided, will use GOOGLE_APPLICATION_CREDENTIALS environment variable
    SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Validate required configuration
    if not PROJECT_ID or not DATASET_ID:
        print("Error: Please set BQ_PROJECT_ID and BQ_DATASET_ID in your .env file")
        sys.exit(1)
    
    # Initialize agent
    print("Initializing Vertex AI Query Agent...")
    agent = VertexAIQueryAgent(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        location=LOCATION,
        service_account_json=SERVICE_ACCOUNT_JSON
    )
    
    # Example query - modify as needed
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Show me the first 10 rows from the table"
    
    # Run query
    result = agent.run(AgentInput(inputs={
        "query": query,
        "mode": "data"  # Use "sql" to only generate SQL without executing
    }))
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    if "error" in result.output:
        print(f"Error: {result.output['error']}")
    else:
        print(f"Response: {result.output.get('response', 'No response generated')}")
        print(f"\nRows returned: {result.output.get('row_count', 0)}")
        if result.output.get('sql'):
            print(f"\nSQL Used:\n{result.output['sql']}")
