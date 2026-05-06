import sys
import uuid
import os
from orchestrator.pipeline import run_pipeline
from orchestrator.memory import ConversationHistory
from db.db_manager import DBManager
from db.schema import DOMAIN_CONFIG

def print_help():
    print("\n--- Commands ---")
    print("/new  - Start a new conversation thread")
    print("/list - List your historical chats")
    print("/load <thread_id> - Load a specific thread")
    print("/help - Show this help message")
    print("/exit - Exit the application")
    print("----------------\n")

def main():
    if not DOMAIN_CONFIG:
        print("CRITICAL ERROR: domain_config.json not found or invalid. System cannot start.")
        sys.exit(1)
    
    db_manager = DBManager()
    user_id = "default_user" # In a real app, this would be the logged-in user
    
    # Initialize session
    thread_id = str(uuid.uuid4())
    db_manager.create_thread(thread_id, user_id, title="New Chat")
    history = ConversationHistory(thread_id=thread_id, db_manager=db_manager)
    
    print(f"\n=== {DOMAIN_CONFIG.get('domain_name', 'System')} AI Agent (Interactive Mode) ===")
    print(f"Active Thread: {thread_id}")
    print_help()

    while True:
        try:
            user_query = input('\nQuestion > ').strip()
            if not user_query:
                continue
            
            # Handle Commands
            if user_query.startswith("/"):
                cmd = user_query.split()[0].lower()
                if cmd == "/exit":
                    break
                elif cmd == "/new":
                    thread_id = str(uuid.uuid4())
                    db_manager.create_thread(thread_id, user_id, title="New Chat")
                    history = ConversationHistory(thread_id=thread_id, db_manager=db_manager)
                    print(f"Started new thread: {thread_id}")
                    continue
                elif cmd == "/list":
                    threads = db_manager.get_user_threads(user_id)
                    print("\n--- Your Chats ---")
                    for t in threads:
                        print(f"[{t['id'][:8]}] {t['title']} ({t['created_at']})")
                    continue
                elif cmd == "/load":
                    parts = user_query.split()
                    if len(parts) < 2:
                        print("Usage: /load <thread_id_prefix>")
                        continue
                    prefix = parts[1]
                    threads = db_manager.get_user_threads(user_id)
                    match = [t for t in threads if t['id'].startswith(prefix)]
                    if not match:
                        print("Thread not found.")
                    else:
                        thread_id = match[0]['id']
                        history = ConversationHistory(thread_id=thread_id, db_manager=db_manager)
                        print(f"Loaded thread: {thread_id}")
                        # Print last few messages
                        for m in history.get_clean_history(5):
                            print(f"{m['role'].upper()}: {m['content'][:100]}...")
                    continue
                elif cmd == "/help":
                    print_help()
                    continue
                else:
                    print("Unknown command. Type /help for assistance.")
                    continue

            request_id = str(uuid.uuid4())
            
            # Run Pipeline using the generator for real-time feedback
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
                
                elif etype == "pipeline_complete":
                    print("\n" + "="*20 + " FINAL ANALYSIS " + "="*20)
                    for result in event['results']:
                        print(result)
            
            print("-" * 50)
            
        except (KeyboardInterrupt, EOFError):
            print('\nExiting...')
            break
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'An error occurred: {e}')
            continue

if __name__ == '__main__':
    main()