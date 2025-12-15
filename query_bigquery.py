# filename: query_bigquery.py
"""
Demo script to query BigQuery tables using Vertex AI Gemini 2.5-Flash.
Uses natural language to generate SQL and analyze results.
"""

from VertexAIQueryAgent import VertexAIQueryAgent
from adk import AgentInput

def main():
    # Configuration
    PROJECT_ID = "ccibt-hack25ww7-713"
    DATASET_ID = "multi_agent_workflow"
    LOCATION = "us-central1"
    SERVICE_ACCOUNT_KEY = None  # Use gcloud auth
    
    # Initialize the Vertex AI Query Agent
    print("Initializing Vertex AI Query Agent...")
    agent = VertexAIQueryAgent(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        location=LOCATION,
        service_account_json=SERVICE_ACCOUNT_KEY
    )
    
    print(f"\n✓ Agent initialized with {len(agent.table_schemas)} tables")
    print(f"Available tables: {', '.join(agent.table_schemas.keys())}\n")
    
    # Example queries
    example_queries = [
        "What are the top 5 most expensive properties in the commercial real estate table?",
        "How many properties are there in each state in the realtor data?",
        "What is the average price of properties with 3 bedrooms?",
        "Show me properties in California with more than 2 bathrooms",
    ]
    
    print("="*60)
    print("EXAMPLE QUERIES")
    print("="*60)
    for i, q in enumerate(example_queries, 1):
        print(f"{i}. {q}")
    print()
    
    # Interactive query loop
    while True:
        print("\n" + "="*60)
        user_query = input("\nEnter your question (or 'quit' to exit): ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if not user_query:
            continue
        
        # Run the query
        input_data = AgentInput(inputs={"query": user_query, "mode": "data"})
        result = agent.run(input_data)
        
        # Display results
        if isinstance(result.output, dict):
            if result.output.get("success"):
                print("\n" + "="*60)
                print("ANSWER")
                print("="*60)
                print(result.output.get("response"))
                
                print(f"\n(Retrieved {result.output.get('row_count', 0)} rows)")
                
                # Ask if user wants to see the data
                show_data = input("\nShow raw data? (y/n): ").strip().lower()
                if show_data == 'y':
                    data = result.output.get("data", [])
                    if data:
                        print(f"\nShowing first {min(len(data), 10)} rows:\n")
                        for i, row in enumerate(data[:10], 1):
                            print(f"Row {i}:")
                            for key, value in row.items():
                                print(f"  {key}: {value}")
                            print()
                    else:
                        print("\nNo data to display.")
            else:
                print(f"\n✗ Error: {result.output.get('error')}")
        else:
            print(f"\nUnexpected output: {result.output}")

if __name__ == "__main__":
    main()
