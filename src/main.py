import sys
import os

# Add the parent directory to sys.path to allow imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.graph import create_graph

# Load environment variables
load_dotenv()

def main():
    """
    Main entry point for the Investment Research Assistant.
    """
    # Check for API Keys based on provider
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "google":
        if not os.getenv("GOOGLE_API_KEY"):
            print("Error: GOOGLE_API_KEY not found in environment variables.")
            print("Please create a .env file with your GOOGLE_API_KEY.")
            return
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please create a .env file with your OPENAI_API_KEY.")
            return
    else:
        # Fallback or warning for unknown provider
        print(f"Warning: Unknown LLM_PROVIDER '{provider}'. Checking for OPENAI_API_KEY by default.")
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found.")
            return


    print("----------------------------------------------------------------")
    print("   Multi-Agent Investment Research Assistant (LangGraph)   ")
    print("----------------------------------------------------------------")
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your research query (e.g., 'Analyze AAPL and MSFT'): ")

    print(f"\nProcessing query: '{query}'\n")
    print("Initializing agents...", end="", flush=True)
    
    graph = create_graph()
    print(" Done.")
    
    print("Running research workflow (this may take a minute)...")
    
    initial_state = {"query": query}
    
    # Run the graph
    # We can stream events to show progress if desired, but for now let's just invoke
    try:
        final_state = graph.invoke(initial_state)
        
        print("\n" + "="*60)
        print("FINAL REPORT")
        print("="*60 + "\n")
        
        print(final_state["final_report"])
        
        print("\n" + "="*60)
        print("Research Complete.")
        
    except Exception as e:
        print(f"\nError running graph: {e}")

if __name__ == "__main__":
    main()
