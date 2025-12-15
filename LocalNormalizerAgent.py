# filename: local_normalizer_agent.py

import pandas as pd
import os
import csv
import io
from adk import Agent, AgentInput, AgentOutput

class LocalNormalizerAgent(Agent):
    def run(self, agent_input: AgentInput) -> AgentOutput:
        file_path = agent_input.inputs.get("file_path")
        file_bytes = agent_input.inputs.get("file_bytes")
        file_name = agent_input.inputs.get("file_name")
        output_dir = agent_input.inputs.get("output_dir")
        sheet_name = agent_input.inputs.get("sheet_name", 0)  # Default to first sheet
        process_all_sheets = agent_input.inputs.get("process_all_sheets", False)  # Process all sheets in Excel

        in_memory = file_bytes is not None
        if in_memory:
            if not file_name or not isinstance(file_name, str):
                return AgentOutput(output="When using file_bytes, provide file_name.")
            if not isinstance(file_bytes, (bytes, bytearray)):
                return AgentOutput(output="file_bytes must be bytes.")
        else:
            if not file_path or not os.path.exists(file_path):
                return AgentOutput(output="File not found. Provide a valid local path.")

        # Some datasets contain extremely large fields; increase CSV field size limit.
        try:
            csv.field_size_limit(2**31 - 1)
        except Exception:
            pass

        # Read CSV or Excel
        source_name = file_name if in_memory else file_path
        if source_name.lower().endswith(".csv"):
            try:
                # Use the Python engine to avoid C-engine buffer overflows on very large fields.
                df = pd.read_csv(
                    io.BytesIO(file_bytes) if in_memory else file_path,
                    engine="python",
                    on_bad_lines="skip",
                    encoding_errors="replace",
                )
            except Exception as e:
                return AgentOutput(output=f"Failed to parse CSV: {e}")
        elif source_name.lower().endswith(".xlsx") or source_name.lower().endswith(".xls"):
            # Handle Excel files - process all sheets or just one
            if process_all_sheets:
                return self._process_all_excel_sheets(file_path, file_bytes, file_name, output_dir, in_memory)
            else:
                try:
                    # Read Excel with proper handling
                    df = pd.read_excel(
                        io.BytesIO(file_bytes) if in_memory else file_path,
                        sheet_name=sheet_name,
                        engine='openpyxl' if source_name.lower().endswith(".xlsx") else None
                    )
                    print(f"Read Excel file: {df.shape[0]} rows, {df.shape[1]} columns")
                    
                    # Remove completely empty rows and columns (common in Excel)
                    df = df.dropna(how='all', axis=0)  # Remove rows with all NaN
                    df = df.dropna(how='all', axis=1)  # Remove columns with all NaN
                    print(f"After removing empty rows/cols: {df.shape[0]} rows, {df.shape[1]} columns")
                    
                except Exception as e:
                    return AgentOutput(output=f"Failed to read Excel: {e}")
        else:
            return AgentOutput(output="Unsupported file type. Use CSV or Excel.")

        # --- Normalization operations ---
        # 1. Normalize column names - ONLY infer names for unnamed columns, preserve existing names
        new_columns = []
        for i, col in enumerate(df.columns):
            col_str = str(col).strip()
            # Clean newlines and other problematic characters from column names
            col_str = col_str.replace('\n', '_').replace('\r', '_').replace('\t', '_')
            col_str = ' '.join(col_str.split())  # Replace multiple spaces with single space
            
            # Only handle unnamed or auto-generated columns - keep existing names as-is
            if (col_str.lower().startswith('unnamed:') or 
                col_str.lower().startswith('column_') or 
                not col_str or 
                col_str == 'nan'):
                # Infer meaningful name from data values
                inferred_name = self._infer_column_name(df[col], i)
                new_col = inferred_name
            else:
                # Keep existing column name, just clean it up (spaces to underscores)
                new_col = col_str.replace(" ", "_").replace("-", "_").replace(".", "_")
            new_columns.append(new_col)
        df.columns = new_columns

        # 2. Normalize data types for BigQuery compatibility
        for col in df.columns:
            # Convert datetime objects to ISO format strings
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                df[col] = df[col].str.replace(" 00:00:00", "")  # Remove time if midnight
            # Try to detect date columns by name or content
            elif "date" in col.lower() or "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            # Convert boolean to string for BigQuery
            elif df[col].dtype == 'bool':
                df[col] = df[col].astype(str)
            # Handle numeric columns - ensure proper type
            elif pd.api.types.is_numeric_dtype(df[col]):
                # Check if column has decimal values
                if df[col].dropna().apply(lambda x: x != int(x) if isinstance(x, (int, float)) else False).any():
                    df[col] = df[col].astype('float64')
                else:
                    # Try to convert to integer if no decimals
                    try:
                        df[col] = df[col].fillna(0).astype('int64')
                    except:
                        df[col] = df[col].astype('float64')

        # 3. Clean text for BigQuery compatibility (preserve original casing and content)
        for col in df.select_dtypes(include="object").columns:
            # Remove all newlines and problematic characters that break CSV parsing
            # Use fillna first to handle NaN values
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str)  # Ensure all values are strings
            df[col] = df[col].str.replace('\x00', '', regex=False)  # Remove null bytes
            df[col] = df[col].str.replace('\r\n', ' ', regex=False)  # Replace CRLF with space
            df[col] = df[col].str.replace('\n', ' ', regex=False)    # Replace LF with space
            df[col] = df[col].str.replace('\r', ' ', regex=False)    # Replace CR with space
            df[col] = df[col].str.replace('\t', ' ', regex=False)    # Replace tabs with space
            # Replace empty strings back to NaN
            df[col] = df[col].replace('', None)

        # 4. Handle missing values:
        # - String columns: Already handled above (NaN/None)
        # - Numeric columns: Fill with 0
        for col in df.select_dtypes(include="number").columns:
            df[col] = df[col].fillna(0)

        # Final validation - ensure no problematic data
        # Replace any remaining NaN with None for proper CSV output
        df = df.where(pd.notnull(df), None)
        
        # CSV output configuration for BigQuery compatibility
        csv_config = {
            'index': False,
            'quoting': csv.QUOTE_NONNUMERIC,  # Quote non-numeric values
            'doublequote': True,
            'lineterminator': '\n',
            'encoding': 'utf-8',
            'na_rep': ''  # Represent None/NaN as empty string
        }
        
        if in_memory:
            normalized_csv_bytes = df.to_csv(**csv_config).encode("utf-8")
            return AgentOutput(
                output={
                    "message": f"Normalization complete (in-memory) for {file_name}",
                    "rows": int(df.shape[0]),
                    "cols": int(df.shape[1]),
                    "columns": list(df.columns),
                    "normalized_csv_bytes": normalized_csv_bytes,
                }
            )

        # Save normalized file (disk mode)
        if output_dir:
            from pathlib import Path
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            # Convert to CSV extension (all normalized files are CSV format)
            base_name = Path(file_path).stem + ".csv"
            normalized_path = str(output_dir_path / base_name)
        else:
            # Handle all Excel extensions
            normalized_path = file_path
            for ext in [".csv", ".xlsx", ".xls"]:
                normalized_path = normalized_path.replace(ext, "")
            normalized_path += "_normalized.csv"
        
        df.to_csv(normalized_path, **csv_config)
        print(f"Saved normalized CSV: {normalized_path}")
        print(f"Final dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"Columns: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
        
        return AgentOutput(
            output={
                "message": f"Normalization complete. File saved at {normalized_path}",
                "path": normalized_path,
                "rows": int(df.shape[0]),
                "cols": int(df.shape[1]),
                "columns": list(df.columns)
            }
        )
    
    def _infer_column_name(self, series, index):
        """Infer a meaningful column name based on data values."""
        # Get sample non-null values
        sample_values = series.dropna().head(10).astype(str)
        
        if len(sample_values) == 0:
            return f"column_{index+1}"
        
        sample_str = ' '.join(sample_values.values).lower()
        
        # Check for common patterns
        if any(word in sample_str for word in ['street', 'avenue', 'road', 'drive', 'lane', 'boulevard']):
            return f"address_{index+1}"
        elif any(word in sample_str for word in ['zip', 'postal']):
            return f"zipcode_{index+1}"
        elif any(word in sample_str for word in ['city', 'town']):
            return f"city_{index+1}"
        elif any(word in sample_str for word in ['state', 'province']):
            return f"state_{index+1}"
        elif any(word in sample_str for word in ['phone', 'tel', 'mobile']):
            return f"phone_{index+1}"
        elif any(word in sample_str for word in ['email', '@']):
            return f"email_{index+1}"
        elif any(word in sample_str for word in ['http', 'www', '.com', '.org']):
            return f"url_{index+1}"
        elif series.dtype in ['int64', 'float64']:
            # Check if numeric values look like prices
            if series.dropna().median() > 1000:
                return f"amount_{index+1}"
            else:
                return f"value_{index+1}"
        elif any(word in sample_str for word in ['description', 'detail', 'note', 'comment']):
            return f"description_{index+1}"
        elif any(word in sample_str for word in ['name', 'title']):
            return f"name_{index+1}"
        elif any(word in sample_str for word in ['id', 'identifier', 'code']):
            return f"id_{index+1}"
        elif any(word in sample_str for word in ['date', '/', '-']) and len(sample_values.iloc[0]) <= 12:
            return f"date_{index+1}"
        else:
            # Default to field_N
            return f"field_{index+1}"
    
    def _process_all_excel_sheets(self, file_path, file_bytes, file_name, output_dir, in_memory):
        """Process all sheets in an Excel file and create relationships between them."""
        from pathlib import Path
        
        # Read all sheets
        source = io.BytesIO(file_bytes) if in_memory else file_path
        source_name = file_name if in_memory else file_path
        engine = 'openpyxl' if source_name.lower().endswith(".xlsx") else None
        
        try:
            # Get all sheet names
            excel_file = pd.ExcelFile(source, engine=engine)
            sheet_names = excel_file.sheet_names
            print(f"\nFound {len(sheet_names)} sheets: {', '.join(sheet_names)}")
            
            if output_dir:
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
            else:
                output_dir_path = Path(file_path).parent / "normalized"
                output_dir_path.mkdir(parents=True, exist_ok=True)
            
            processed_sheets = {}
            all_columns = {}  # Store column info for relationship detection
            
            # Process each sheet
            for sheet_name in sheet_names:
                print(f"\n{'='*60}")
                print(f"Processing sheet: {sheet_name}")
                print(f"{'='*60}")
                
                # Read sheet
                df = pd.read_excel(source, sheet_name=sheet_name, engine=engine)
                print(f"Initial size: {df.shape[0]} rows, {df.shape[1]} columns")
                
                # Skip empty sheets
                if df.empty or df.shape[0] == 0:
                    print(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                # Remove empty rows and columns
                df = df.dropna(how='all', axis=0)
                df = df.dropna(how='all', axis=1)
                
                if df.empty:
                    print(f"Skipping sheet with no data after cleanup: {sheet_name}")
                    continue
                
                print(f"After cleanup: {df.shape[0]} rows, {df.shape[1]} columns")
                
                # Normalize the sheet
                df_normalized = self._normalize_dataframe(df, sheet_name)
                
                # Store column information
                all_columns[sheet_name] = {
                    'columns': list(df_normalized.columns),
                    'row_count': len(df_normalized)
                }
                
                # Save to CSV
                base_name = Path(file_path).stem if not in_memory else Path(file_name).stem
                csv_filename = f"{base_name}_{sheet_name.replace(' ', '_').replace('/', '_')}.csv"
                csv_path = str(output_dir_path / csv_filename)
                
                csv_config = {
                    'index': False,
                    'quoting': csv.QUOTE_NONNUMERIC,
                    'doublequote': True,
                    'lineterminator': '\n',
                    'encoding': 'utf-8',
                    'na_rep': ''
                }
                
                df_normalized.to_csv(csv_path, **csv_config)
                print(f"✓ Saved: {csv_path}")
                print(f"  Dimensions: {df_normalized.shape[0]} rows × {df_normalized.shape[1]} columns")
                print(f"  Columns: {', '.join(df_normalized.columns[:5])}{'...' if len(df_normalized.columns) > 5 else ''}")
                
                processed_sheets[sheet_name] = {
                    'path': csv_path,
                    'rows': int(df_normalized.shape[0]),
                    'cols': int(df_normalized.shape[1]),
                    'columns': list(df_normalized.columns)
                }
            
            # Detect relationships between sheets
            relationships = self._detect_relationships(all_columns)
            
            # Save relationship metadata
            if relationships:
                import json
                relationship_file = str(output_dir_path / f"{Path(file_path).stem if not in_memory else Path(file_name).stem}_relationships.json")
                with open(relationship_file, 'w') as f:
                    json.dump({
                        'sheets': processed_sheets,
                        'relationships': relationships
                    }, f, indent=2)
                print(f"\n✓ Saved relationship metadata: {relationship_file}")
                print(f"\nDetected {len(relationships)} potential relationships:")
                for rel in relationships:
                    print(f"  • {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
            
            return AgentOutput(
                output={
                    "message": f"Processed {len(processed_sheets)} sheets from Excel file",
                    "sheets": processed_sheets,
                    "relationships": relationships,
                    "output_dir": str(output_dir_path)
                }
            )
            
        except Exception as e:
            return AgentOutput(output=f"Failed to process Excel sheets: {e}")
    
    def _normalize_dataframe(self, df, sheet_name=None):
        """Normalize a single dataframe."""
        # 1. Normalize column names
        new_columns = []
        for i, col in enumerate(df.columns):
            col_str = str(col).strip()
            col_str = col_str.replace('\n', '_').replace('\r', '_').replace('\t', '_')
            col_str = ' '.join(col_str.split())
            
            if (col_str.lower().startswith('unnamed:') or 
                col_str.lower().startswith('column_') or 
                not col_str or 
                col_str == 'nan'):
                inferred_name = self._infer_column_name(df[col], i)
                new_col = inferred_name
            else:
                new_col = col_str.replace(" ", "_").replace("-", "_").replace(".", "_")
            new_columns.append(new_col)
        df.columns = new_columns
        
        # 2. Normalize data types for BigQuery
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                df[col] = df[col].str.replace(" 00:00:00", "")
            elif "date" in col.lower() or "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            elif df[col].dtype == 'bool':
                df[col] = df[col].astype(str)
            elif pd.api.types.is_numeric_dtype(df[col]):
                if df[col].dropna().apply(lambda x: x != int(x) if isinstance(x, (int, float)) else False).any():
                    df[col] = df[col].astype('float64')
                else:
                    try:
                        df[col] = df[col].fillna(0).astype('int64')
                    except:
                        df[col] = df[col].astype('float64')
        
        # 3. Clean text
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace('\x00', '', regex=False)
            df[col] = df[col].str.replace('\r\n', ' ', regex=False)
            df[col] = df[col].str.replace('\n', ' ', regex=False)
            df[col] = df[col].str.replace('\r', ' ', regex=False)
            df[col] = df[col].str.replace('\t', ' ', regex=False)
            df[col] = df[col].replace('', None)
        
        # 4. Handle missing numeric values
        for col in df.select_dtypes(include="number").columns:
            df[col] = df[col].fillna(0)
        
        # Final cleanup
        df = df.where(pd.notnull(df), None)
        
        return df
    
    def _detect_relationships(self, all_columns):
        """Detect potential foreign key relationships between sheets based on column names."""
        relationships = []
        sheet_names = list(all_columns.keys())
        
        # Common patterns for ID columns
        id_patterns = ['id', '_id', 'key', '_key', 'code', '_code', 'num', 'number']
        
        for i, sheet1 in enumerate(sheet_names):
            for sheet2 in sheet_names[i+1:]:
                # Find common columns
                cols1 = set(all_columns[sheet1]['columns'])
                cols2 = set(all_columns[sheet2]['columns'])
                common_cols = cols1.intersection(cols2)
                
                for col in common_cols:
                    col_lower = col.lower()
                    # Check if it looks like an ID/key column
                    if any(pattern in col_lower for pattern in id_patterns):
                        relationships.append({
                            'from_table': sheet1,
                            'from_column': col,
                            'to_table': sheet2,
                            'to_column': col,
                            'relationship_type': 'potential_foreign_key',
                            'confidence': 'high' if col_lower.endswith('_id') or col_lower.endswith('id') else 'medium'
                        })
        
        return relationships


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python LocalNormalizerAgent.py <excel_file_path> [output_dir]")
        print("\nExample:")
        print("  python LocalNormalizerAgent.py data/myfile.xlsx normalized/")
        print("  python LocalNormalizerAgent.py data/myfile.csv normalized/")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "normalized"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"FILE NORMALIZER FOR BIGQUERY")
    print(f"{'='*60}")
    print(f"Input file: {file_path}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")
    
    # Initialize agent
    agent = LocalNormalizerAgent()
    
    # Determine if it's an Excel file
    is_excel = file_path.lower().endswith(('.xlsx', '.xls'))
    
    # Process file
    result = agent.run(AgentInput(inputs={
        "file_path": file_path,
        "output_dir": output_dir,
        "process_all_sheets": is_excel  # Auto-process all sheets for Excel files
    }))
    
    # Display results
    output = result.output
    
    if isinstance(output, dict):
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"{output.get('message', 'Processing complete')}")
        
        if 'sheets' in output:
            print(f"\nProcessed Sheets:")
            for sheet_name, info in output['sheets'].items():
                print(f"\n  📊 {sheet_name}")
                print(f"     File: {info['path']}")
                print(f"     Rows: {info['rows']:,}")
                print(f"     Columns: {info['cols']}")
                print(f"     Schema: {', '.join(info['columns'][:5])}{'...' if len(info['columns']) > 5 else ''}")
        
        if 'relationships' in output and output['relationships']:
            print(f"\n  🔗 Relationships Detected:")
            for rel in output['relationships']:
                confidence_emoji = "🟢" if rel['confidence'] == 'high' else "🟡"
                print(f"     {confidence_emoji} {rel['from_table']}.{rel['from_column']} ↔ {rel['to_table']}.{rel['to_column']}")
        
        print(f"\n✅ All files saved to: {output.get('output_dir', output_dir)}")
        
        # BigQuery import instructions
        if 'sheets' in output:
            print(f"\n{'='*60}")
            print("BIGQUERY IMPORT COMMANDS")
            print(f"{'='*60}")
            for sheet_name, info in output['sheets'].items():
                table_name = sheet_name.lower().replace(' ', '_').replace('-', '_')
                print(f"\n# Load {sheet_name}")
                print(f"bq load --source_format=CSV \\")
                print(f"  --autodetect \\")
                print(f"  --skip_leading_rows=1 \\")
                print(f"  your-dataset.{table_name} \\")
                print(f"  {info['path']}")
        elif 'path' in output:
            # Single file output
            print(f"\n{'='*60}")
            print("BIGQUERY IMPORT COMMAND")
            print(f"{'='*60}")
            table_name = os.path.splitext(os.path.basename(file_path))[0].lower().replace(' ', '_').replace('-', '_')
            print(f"\nbq load --source_format=CSV \\")
            print(f"  --autodetect \\")
            print(f"  --skip_leading_rows=1 \\")
            print(f"  your-dataset.{table_name} \\")
            print(f"  {output['path']}")
    else:
        print(f"\nResult: {output}")
