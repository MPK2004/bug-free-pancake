import os
import uuid
import json
import chainlit as cl
from chainlit.data import BaseDataLayer
from chainlit.types import ThreadDict, ThreadFilter
from typing import List, Optional, Dict

from orchestrator.pipeline import run_pipeline
from orchestrator.memory import ConversationHistory
from db.db_manager import DBManager
from db.schema import DOMAIN_CONFIG

# Initialize Global DB Manager
db_manager = DBManager()
DEFAULT_USER_ID = "default_user"

@cl.data_layer
class SQLiteDataLayer(BaseDataLayer):
    """
    Bridges Chainlit UI with our custom SQLite persistence layer.
    """
    async def get_user(self, identifier: str):
        # We ensure the user exists in our DB and return a cl.User
        db_manager.ensure_user(DEFAULT_USER_ID)
        return cl.User(identifier=DEFAULT_USER_ID, metadata={"role": "admin"})

    async def list_threads(self, pagination, filter: ThreadFilter) -> List[ThreadDict]:
        # Fetch historical chats for the default user
        threads = db_manager.get_user_threads(DEFAULT_USER_ID)
        return [
            {
                "id": t["id"],
                "createdAt": t["created_at"],
                "userIdentifier": DEFAULT_USER_ID,
                "name": t["title"] or "New Chat"
            }
            for t in threads
        ]

    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        # Fetch thread details for rehydration
        messages = db_manager.get_thread_messages(thread_id)
        if not messages:
            return None
        
        # Map our messages to Chainlit's message format
        cl_messages = []
        for msg in messages:
            cl_messages.append({
                "id": str(uuid.uuid4()), # Chainlit needs unique IDs for UI elements
                "threadId": thread_id,
                "author": "Assistant" if msg["role"] == "assistant" else "User",
                "content": msg["content"],
                "createdAt": msg.get("created_at"),
                "type": "assistant_message" if msg["role"] == "assistant" else "user_message"
            })
        
        # Find thread title
        threads = db_manager.get_user_threads(DEFAULT_USER_ID)
        thread_info = next((t for t in threads if t["id"] == thread_id), None)
        
        return {
            "id": thread_id,
            "createdAt": thread_info["created_at"] if thread_info else None,
            "userIdentifier": DEFAULT_USER_ID,
            "name": thread_info["title"] if thread_info else "Chat",
            "steps": cl_messages
        }

    async def delete_thread(self, thread_id: str):
        db_manager.delete_thread(thread_id)

    async def create_thread(self, thread_id: str, user_id: str, name: str = None, metadata: Dict = None):
        db_manager.create_thread(thread_id, DEFAULT_USER_ID, title=name)

    # --- Missing Abstract Methods (Minimal Implementation) ---
    async def build_debug_url(self): return None
    async def create_element(self, element): pass
    async def get_element(self, thread_id, element_id): return None
    async def delete_element(self, element_id): pass
    async def create_step(self, step_dict): pass
    async def update_step(self, step_dict): pass
    async def delete_step(self, step_id): pass
    async def create_user(self, user): return None
    async def upsert_feedback(self, feedback): pass
    async def delete_feedback(self, feedback_id): pass
    async def get_thread_author(self, thread_id): return DEFAULT_USER_ID
    async def update_thread(self, thread_id, name=None, user_id=None, metadata=None, tags=None): pass

# --- Chainlit Lifecycle Handlers ---

@cl.on_chat_start
async def on_chat_start():
    """
    Initializes a new session.
    """
    thread_id = cl.context.session.thread_id
    # Create thread in DB if it doesn't exist
    db_manager.create_thread(thread_id, DEFAULT_USER_ID, title="New Chat")
    
    # Instantiate memory with the fresh thread_id
    history = ConversationHistory(thread_id=thread_id, db_manager=db_manager)
    cl.user_session.set("history", history)
    
    domain_name = DOMAIN_CONFIG.get("domain_name", "System")
    await cl.Message(content=f"Welcome to the **{domain_name}** AI Agent. How can I help you today?").send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """
    Proactively hydrates the history when a user resumes an old chat from the sidebar.
    """
    thread_id = thread["id"]
    # Instant time-travel: Load history from SQLite
    history = ConversationHistory(thread_id=thread_id, db_manager=db_manager)
    cl.user_session.set("history", history)
    print(f"[UI] Resumed thread {thread_id} - History hydrated.")

@cl.on_message
async def on_message(message: cl.Message):
    """
    The main execution loop with the Fail-Safe Consumer.
    """
    history = cl.user_session.get("history")
    if not history:
        # Fallback if session was lost but thread_id persists
        history = ConversationHistory(thread_id=cl.context.session.thread_id, db_manager=db_manager)
        cl.user_session.set("history", history)

    current_step = None
    final_answer = cl.Message(content="")
    
    try:
        # Consume the backend generator
        # Note: run_pipeline is a sync generator. In Chainlit, we can iterate directly 
        # as it runs within a thread pool for each session.
        for event in run_pipeline(message.content, history=history):
            etype = event.get("event")
            
            if etype == "planning":
                current_step = cl.Step(name="Cognitive Planning")
                await current_step.send()
                current_step.output = event.get("status", "Analyzing request...")
                await current_step.update()
            
            elif etype == "plan_ready":
                if current_step:
                    tasks = event.get("tasks", [])
                    roadmap = "\n".join([f"{i+1}. [{t['intent']}] {t['sub_query']}" for i, t in enumerate(tasks)])
                    current_step.output = f"Execution Roadmap:\n{roadmap}"
                    await current_step.update()
                    current_step = None # Close planning step
            
            elif etype == "step_start":
                idx = event.get("index")
                task = event.get("task")
                current_step = cl.Step(name=f"Step {idx}: {task['sub_query']}")
                await current_step.send()
                current_step.output = f"Running {task['intent']} analysis..."
                await current_step.update()
            
            elif etype == "step_complete":
                if current_step:
                    current_step.output = event.get("insights", "Analysis complete.")
                    await current_step.update()
                    current_step = None
            
            elif etype == "pipeline_complete":
                # Final synthesis
                results = event.get("results", [])
                final_content = "\n\n---\n\n".join(results)
                final_answer.content = final_content
                await final_answer.send()

    except Exception as e:
        # --- The Fail-Safe Closure ---
        error_msg = f"Critical Failure: {str(e)}"
        print(f"[UI ERROR] {error_msg}")
        
        if current_step:
            current_step.output = f"⚠️ Step Failed: {str(e)}"
            await current_step.update()
        
        await cl.ErrorMessage(content=f"I encountered an error while processing your request: {str(e)}").send()
    
    finally:
        current_step = None
