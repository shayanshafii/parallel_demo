import os
import json
import time
from parallel import Parallel

# SET YOUR API KEY HERE OR USE ENVIRONMENT VARIABLE
API_KEY = "AlYHEY9m8ctfemrhwJD50u3TjYOwcnsF3l_dqt3k"
client = Parallel(api_key=API_KEY)


def search_mode():
    try:
        objective = input("Enter search objective: ").strip()
        if not objective:
            print("ERROR: Objective is required")
            return
        
        search_queries_input = input("Enter search queries (comma-separated, optional): ").strip()
        search_queries = None
        if search_queries_input:
            search_queries = [q.strip() for q in search_queries_input.split(",")]
        
        print("\nExecuting search...")
        search = client.beta.search(
            objective=objective,
            search_queries=search_queries,
            max_results=10,
            max_chars_per_result=10000,
        )
        
        # DISPLAY RESULTS
        print("\n" + "=" * 80)
        print("SEARCH RESULTS")
        print("=" * 80)
        print(f"Search ID: {search.search_id}")
        print(f"\nFound {len(search.results)} result(s):")
        print("-" * 80)
        
        for i, result in enumerate(search.results, 1):
            print(f"\nResult {i}:")
            print(f"  URL: {result.url}")
            print(f"  Title: {result.title or 'N/A'}")
            print(f"  Publish Date: {result.publish_date or 'N/A'}")
            if result.excerpts:
                print(f"  Excerpts: {len(result.excerpts)} excerpt(s)")
                if result.excerpts[0]:
                    excerpt_preview = result.excerpts[0][:300]
                    print(f"  Preview: {excerpt_preview}...")
            else:
                print("  Excerpts: None")
        
        # PRINT USAGE INFO IF AVAILABLE
        if hasattr(search, 'usage') and search.usage:
            print("\n" + "-" * 80)
            print("Usage:")
            for usage_item in search.usage:
                print(f"  {usage_item.name}: {usage_item.count}")
        
    except Exception as e:
        print(f"ERROR: Search failed - {str(e)}")


def extract_mode():
    try:
        urls_input = input("Enter URLs to extract (comma-separated): ").strip()
        if not urls_input:
            print("ERROR: At least one URL is required")
            return
        
        urls = [url.strip() for url in urls_input.split(",")]
        
        objective = input("Enter extraction objective (optional): ").strip()
        objective = objective if objective else None
        
        print("\nExtracting content...")
        extract = client.beta.extract(
            urls=urls,
            objective=objective,
            excerpts=True,
            full_content=True,
        )
        
        # DISPLAY RESULTS
        print("\n" + "=" * 80)
        print("EXTRACTED CONTENT")
        print("=" * 80)
        print(f"Extracted {len(extract.results)} URL(s):")
        print("-" * 80)
        
        for i, result in enumerate(extract.results, 1):
            print(f"\nResult {i}:")
            print(f"  URL: {result.url}")
            print(f"  Title: {result.title or 'N/A'}")
            print(f"  Publish Date: {result.publish_date or 'N/A'}")
            
            if hasattr(result, 'excerpts') and result.excerpts:
                print(f"  Excerpts: {len(result.excerpts)} excerpt(s)")
                if result.excerpts[0]:
                    excerpt_preview = result.excerpts[0][:300]
                    print(f"  Preview: {excerpt_preview}...")
            
            if hasattr(result, 'full_content') and result.full_content:
                content_preview = result.full_content[:500]
                print(f"  Full Content Preview: {content_preview}...")
        
        # PRINT USAGE INFO IF AVAILABLE
        if hasattr(extract, 'usage') and extract.usage:
            print("\n" + "-" * 80)
            print("Usage:")
            for usage_item in extract.usage:
                print(f"  {usage_item.name}: {usage_item.count}")
        
    except Exception as e:
        print(f"ERROR: Extract failed - {str(e)}")


def poll_findall_status(findall_id, max_wait_time=300):
    start_time = time.time()
    while True:
        try:
            status_response = client.beta.findall.retrieve(findall_id)
            status = status_response.status.status
            
            if status == "completed":
                return status_response
            elif status in ["failed", "cancelled"]:
                print(f"\nFindAll run {status}")
                return status_response
            
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                print(f"\nTimeout after {max_wait_time} seconds")
                return status_response
            
            print(".", end="", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"\nERROR: Failed to poll status - {str(e)}")
            return None


def findall_mode():
    try:
        objective = input("Enter findall objective: ").strip()
        if not objective:
            print("ERROR: Objective is required")
            return
        
        entity_type = input("Enter entity type (e.g., 'companies', 'people'): ").strip()
        if not entity_type:
            print("ERROR: Entity type is required")
            return
        
        print("\nEnter match conditions:")
        print("  Format: JSON array of objects with 'name' and 'description' (BOTH REQUIRED)")
        print("  Example: [{\"name\": \"location\", \"description\": \"San Francisco\"}]")
        match_conditions_input = input("Match conditions (JSON or press Enter for empty): ").strip()
        
        match_conditions = []
        if match_conditions_input:
            try:
                match_conditions = json.loads(match_conditions_input)
            except json.JSONDecodeError:
                print("ERROR: Invalid JSON format for match conditions")
                return
        
        print("\nCreating FindAll run...")
        findall_run = client.beta.findall.create(
            objective=objective,
            entity_type=entity_type,
            match_conditions=match_conditions,
            generator="base",
            match_limit=10,
        )
        
        findall_id = findall_run.findall_id
        print(f"FindAll Run ID: {findall_id}")
        print("Waiting for completion", end="", flush=True)
        
        # POLL FOR COMPLETION
        status_response = poll_findall_status(findall_id)
        
        if not status_response:
            return
        
        if status_response.status.status == "completed":
            print("\n\n" + "=" * 80)
            print("FINDALL RESULTS")
            print("=" * 80)
            
            # RETRIEVE RESULTS
            try:
                results = client.beta.findall.result(findall_id)
                
                if hasattr(results, 'candidates') and results.candidates:
                    print(f"\nFound {len(results.candidates)} candidate(s):")
                    print("-" * 80)
                    
                    for i, candidate in enumerate(results.candidates, 1):
                        print(f"\nCandidate {i}:")
                        if hasattr(candidate, 'name'):
                            print(f"  Name: {candidate.name}")
                        if hasattr(candidate, 'url'):
                            print(f"  URL: {candidate.url}")
                        if hasattr(candidate, 'description'):
                            print(f"  Description: {candidate.description}")
                else:
                    print("\nNo candidates found")
                
                # PRINT USAGE INFO IF AVAILABLE
                if hasattr(results, 'usage') and results.usage:
                    print("\n" + "-" * 80)
                    print("Usage:")
                    for usage_item in results.usage:
                        print(f"  {usage_item.name}: {usage_item.count}")
                        
            except Exception as e:
                print(f"\nERROR: Failed to retrieve results - {str(e)}")
        else:
            print(f"\nFindAll run did not complete successfully. Status: {status_response.status.status}")
        
    except Exception as e:
        print(f"ERROR: FindAll failed - {str(e)}")


def poll_task_run_status(run_id, max_wait_time=300):
    start_time = time.time()
    while True:
        try:
            status_response = client.task_run.retrieve(run_id)
            status = status_response.status
            
            if status == "completed":
                return status_response
            elif status in ["failed", "cancelled"]:
                print(f"\nTask run {status}")
                return status_response
            
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                print(f"\nTimeout after {max_wait_time} seconds")
                return status_response
            
            print(".", end="", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"\nERROR: Failed to poll status - {str(e)}")
            return None


def task_run_mode():
    try:
        input_text = input("Enter task input: ").strip()
        if not input_text:
            print("ERROR: Task input is required")
            return
        
        processor = input("Enter processor type (default: 'base'): ").strip()
        processor = processor if processor else "base"
        
        print("\nCreating task run...")
        task_run = client.task_run.create(
            input=input_text,
            processor=processor
        )
        
        run_id = task_run.run_id
        print(f"Task Run ID: {run_id}")
        print("Waiting for completion", end="", flush=True)
        
        # POLL FOR COMPLETION
        status_response = poll_task_run_status(run_id)
        
        if not status_response:
            return
        
        if status_response.status == "completed":
            print("\n\n" + "=" * 80)
            print("TASK RUN RESULTS")
            print("=" * 80)
            
            # RETRIEVE RESULTS
            try:
                result = client.task_run.result(run_id)
                
                print("\nResult:")
                print("-" * 80)
                if hasattr(result, 'output') and hasattr(result.output, 'content'):
                    print(result.output.content)
                
                # PRINT USAGE INFO IF AVAILABLE
                if hasattr(result, 'usage') and result.usage:
                    print("\n" + "-" * 80)
                    print("Usage:")
                    for usage_item in result.usage:
                        print(f"  {usage_item.name}: {usage_item.count}")
                        
            except Exception as e:
                print(f"\nERROR: Failed to retrieve results - {str(e)}")
        else:
            print(f"\nTask run did not complete successfully. Status: {status_response.status}")
        
    except Exception as e:
        print(f"ERROR: Task run failed - {str(e)}")


def display_menu():
    print("\n" + "=" * 80)
    print("PARALLEL API DEMO - SELECT A MODE")
    print("=" * 80)
    print("1. Search")
    print("2. Extract")
    print("3. FindAll")
    print("4. Task Run")
    print("5. Exit")
    print("=" * 80)


def main():
    while True:
        display_menu()
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            search_mode()
        elif choice == "2":
            extract_mode()
        elif choice == "3":
            findall_mode()
        elif choice == "4":
            task_run_mode()
        elif choice == "5":
            print("\nExiting. Goodbye!")
            break
        else:
            print("\nERROR: Invalid choice. Please enter a number between 1 and 5.")
            continue
        
        # ASK IF USER WANTS TO CONTINUE
        while True:
            continue_choice = input("\nContinue? (y/n): ").strip().lower()
            if continue_choice in ["y", "yes"]:
                break
            elif continue_choice in ["n", "no"]:
                print("\nExiting. Goodbye!")
                return
            else:
                print("Please enter 'y' or 'n'")


if __name__ == "__main__":
    main()
