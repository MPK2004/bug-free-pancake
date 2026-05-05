import sys
import uuid
from orchestrator.pipeline import run_pipeline
from orchestrator.memory import ConversationHistory
from db.schema import DOMAIN_CONFIG

def main():
    if not DOMAIN_CONFIG:
        print("CRITICAL ERROR: domain_config.json not found or invalid. System cannot start.")
        sys.exit(1)
    
    print(f"\n=== {DOMAIN_CONFIG.get('domain_name', 'System')} AI Agent (Interactive Mode) ===")
    print("Type 'exit' or 'quit' to stop. Type 'clear' to reset memory.\n")
    
    history = ConversationHistory()
    
    while True:
        try:
            user_query = input('Question > ').strip()
            
            if not user_query:
                continue
                
            if user_query.lower() in ['exit', 'quit']:
                print('Goodbye!')
                break
                
            if user_query.lower() == 'clear':
                history = ConversationHistory()
                print("Memory cleared.")
                continue

            request_id = str(uuid.uuid4())
            
            # Iterate through the generator events for real-time UX feedback
            for event in run_pipeline(user_query, request_id=request_id, history=history):
                etype = event.get("event")
                
                if etype == "planning":
                    print(f"[*] {event['status']}")
                
                elif etype == "plan_ready":
                    tasks = event['tasks']
                    print(f"[PLAN] Identified {len(tasks)} tasks:")
                    for i, t in enumerate(tasks):
                        print(f"  {i+1}. [{t['intent']}] {t['sub_query']}")
                
                elif etype == "step_start":
                    idx = event['index']
                    task = event['task']
                    print(f"\n[RUNNING] Step {idx}: {task['sub_query']}...")
                
                elif etype == "step_complete":
                    print(f"[DONE] Step {event['index']} complete.")
                    # We can print partial results here if we want more verbosity
                
                elif etype == "pipeline_complete":
                    print("\n" + "="*20 + " FINAL ANALYSIS " + "="*20)
                    for result in event['results']:
                        print(result)
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print('\nExiting...')
            break
        except Exception as e:
            print(f'An error occurred: {e}')

if __name__ == '__main__':
    main()