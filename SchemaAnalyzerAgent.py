# filename: SchemaAnalyzerAgent.py

from google.cloud import bigquery
from pathlib import Path
from adk import Agent, AgentInput, AgentOutput

class SchemaAnalyzerAgent(Agent):
    """
    Agent to analyze BigQuery tables and create relationships/foreign keys if possible.
    """
    
    def __init__(self, project_id: str, dataset_id: str, service_account_json=None):
        """
        Initialize Schema Analyzer Agent.
        
        Args:
            project_id: Your GCP project ID
            dataset_id: BigQuery dataset name
            service_account_json: Path to service account key (optional)
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
    
    def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        Analyze tables in the dataset and suggest relationships.
        
        Expected inputs:
            - analyze_only: (optional) If True, only analyze without creating views
        """
        analyze_only = agent_input.inputs.get("analyze_only", False)
        
        # Get all tables in the dataset
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        tables = list(self.client.list_tables(dataset_ref))
        
        if not tables:
            return AgentOutput(output={
                "error": f"No tables found in dataset {dataset_ref}"
            })
        
        print(f"\n{'='*60}")
        print(f"ANALYZING {len(tables)} TABLES IN {dataset_ref}")
        print(f"{'='*60}\n")
        
        table_schemas = {}
        
        # Get schema for each table
        for table in tables:
            table_id = f"{dataset_ref}.{table.table_id}"
            table_obj = self.client.get_table(table_id)
            
            columns = [(field.name, field.field_type) for field in table_obj.schema]
            table_schemas[table.table_id] = {
                "columns": columns,
                "num_rows": table_obj.num_rows,
                "table_id": table_id
            }
            
            print(f"Table: {table.table_id}")
            print(f"  Rows: {table_obj.num_rows:,}")
            print(f"  Columns: {len(columns)}")
            print(f"  Schema: {', '.join([f'{name} ({dtype})' for name, dtype in columns[:5]])}...")
            print()
        
        # Analyze potential relationships
        relationships = self._find_relationships(table_schemas)
        
        if relationships:
            print(f"\n{'='*60}")
            print(f"POTENTIAL RELATIONSHIPS FOUND: {len(relationships)}")
            print(f"{'='*60}\n")
            
            for rel in relationships:
                print(f"• {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
                print(f"  Confidence: {rel['confidence']}")
                print(f"  Reason: {rel['reason']}\n")
        else:
            print(f"\n{'='*60}")
            print("NO OBVIOUS RELATIONSHIPS FOUND")
            print(f"{'='*60}\n")
            print("Tables appear to be independent datasets.")
        
        # Create joined views if not analyze_only
        if not analyze_only and relationships:
            self._create_relationship_views(relationships, table_schemas)
        
        return AgentOutput(output={
            "success": True,
            "tables": len(tables),
            "relationships": relationships,
            "table_schemas": {k: {"columns": v["columns"], "rows": v["num_rows"]} 
                            for k, v in table_schemas.items()}
        })
    
    def _find_relationships(self, table_schemas):
        """
        Analyze table schemas to find potential relationships.
        """
        relationships = []
        table_names = list(table_schemas.keys())
        
        for i, table1 in enumerate(table_names):
            cols1 = {name.lower(): dtype for name, dtype in table_schemas[table1]["columns"]}
            
            for table2 in table_names[i+1:]:
                cols2 = {name.lower(): dtype for name, dtype in table_schemas[table2]["columns"]}
                
                # Find common column names
                common_cols = set(cols1.keys()) & set(cols2.keys())
                
                for col in common_cols:
                    # Skip generic columns
                    if col in ['id', 'unknown', 'date', 'time', 'timestamp']:
                        continue
                    
                    # Check if data types match
                    if cols1[col] == cols2[col]:
                        relationships.append({
                            "from_table": table1,
                            "from_column": col,
                            "to_table": table2,
                            "to_column": col,
                            "confidence": "HIGH" if col in ['property_id', 'listing_id', 'address'] else "MEDIUM",
                            "reason": f"Common column '{col}' with matching type {cols1[col]}"
                        })
        
        # Check for location-based relationships (address, city, state, zip)
        location_cols = ['address', 'city', 'state', 'zip', 'zipcode', 'postal_code']
        
        for table1 in table_names:
            cols1 = {name.lower(): dtype for name, dtype in table_schemas[table1]["columns"]}
            
            for table2 in table_names:
                if table1 == table2:
                    continue
                
                cols2 = {name.lower(): dtype for name, dtype in table_schemas[table2]["columns"]}
                
                # Check if both tables have location columns
                loc_cols_1 = [col for col in location_cols if col in cols1]
                loc_cols_2 = [col for col in location_cols if col in cols2]
                
                if loc_cols_1 and loc_cols_2:
                    # Check if not already in relationships
                    already_related = any(
                        r['from_table'] == table1 and r['to_table'] == table2 
                        for r in relationships
                    )
                    
                    if not already_related:
                        relationships.append({
                            "from_table": table1,
                            "from_column": ', '.join(loc_cols_1),
                            "to_table": table2,
                            "to_column": ', '.join(loc_cols_2),
                            "confidence": "MEDIUM",
                            "reason": f"Both tables have location fields - potential geographic join"
                        })
        
        return relationships
    
    def _create_relationship_views(self, relationships, table_schemas):
        """
        Create SQL views that demonstrate the relationships.
        """
        print(f"\n{'='*60}")
        print("CREATING RELATIONSHIP VIEWS")
        print(f"{'='*60}\n")
        
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        created_count = 0
        skipped_count = 0
        
        for i, rel in enumerate(relationships, 1):
            # Skip multi-column relationships (contain commas)
            if ',' in rel['from_column'] or ',' in rel['to_column']:
                print(f"⊘ Skipped: {rel['from_table']} ↔ {rel['to_table']} (multi-column join not supported in views)")
                skipped_count += 1
                continue
            
            # Skip if confidence is too low
            if rel['confidence'] not in ['HIGH', 'MEDIUM']:
                skipped_count += 1
                continue
            
            view_name = f"view_{rel['from_table']}_join_{rel['to_table']}"
            
            # Get all columns from both tables to build proper SELECT
            t1_cols = [name for name, _ in table_schemas[rel['from_table']]['columns']]
            t2_cols = [name for name, _ in table_schemas[rel['to_table']]['columns']]
            
            # Exclude the join column from t2 to avoid duplicates
            t2_cols_filtered = [f"t2.{col}" for col in t2_cols if col.lower() != rel['to_column'].lower()]
            
            # Build SELECT clause
            t1_select = ", ".join([f"t1.{col}" for col in t1_cols])
            t2_select = ", ".join(t2_cols_filtered) if t2_cols_filtered else ""
            
            if t2_select:
                select_clause = f"{t1_select}, {t2_select}"
            else:
                select_clause = t1_select
            
            # Create a simple JOIN view
            query = f"""
            CREATE OR REPLACE VIEW `{dataset_ref}.{view_name}` AS
            SELECT 
                {select_clause}
            FROM `{table_schemas[rel['from_table']]['table_id']}` t1
            LEFT JOIN `{table_schemas[rel['to_table']]['table_id']}` t2
            ON t1.{rel['from_column']} = t2.{rel['to_column']}
            LIMIT 1000
            """
            
            try:
                self.client.query(query).result()
                print(f"✓ Created view: {view_name}")
                print(f"  Joins {rel['from_table']} ↔ {rel['to_table']} on '{rel['from_column']}'")
                created_count += 1
            except Exception as e:
                print(f"✗ Failed to create view {view_name}: {e}")
        
        print(f"\n{'='*60}")
        print(f"VIEW CREATION COMPLETE: {created_count} created, {skipped_count} skipped")
        print(f"{'='*60}\n")
