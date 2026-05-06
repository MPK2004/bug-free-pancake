import json
import re
from llm.summarizer import summarize_history

class ConversationHistory:
    """
    Manages the persistent state of the conversation.
    Handles selective context injection, persistence via SQLite, and recursive compaction.
    """
    def __init__(self, thread_id=None, db_manager=None, max_turns=10):
        self.thread_id = thread_id
        self.db_manager = db_manager
        self.max_turns = max_turns
        
        self.messages = []
        self.snapshot = None # Stores compressed narrative + data ledger
        self.step_index = 0

        if self.thread_id and self.db_manager:
            self._load_from_db()

    def _load_from_db(self):
        """
        Hydrates the history from the SQLite database.
        """
        # Load messages
        db_messages = self.db_manager.get_thread_messages(self.thread_id)
        self.messages = []
        for msg in db_messages:
            self.messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "meta_data": json.loads(msg["meta_data"]) if msg["meta_data"] else {}
            })
            if msg["step_index"] >= self.step_index:
                self.step_index = msg["step_index"] + 1
        
        # Load latest snapshot
        db_snapshot = self.db_manager.get_latest_snapshot(self.thread_id)
        if db_snapshot:
            # Note: snapshot in DB stores narrative and data_ledger separately or as JSON
            # We normalize it here
            self.snapshot = {
                "narrative": db_snapshot["narrative"],
                "data_ledger": json.loads(db_snapshot["data_ledger"]) if db_snapshot["data_ledger"] else {}
            }
            if db_snapshot["step_index"] >= self.step_index:
                self.step_index = db_snapshot["step_index"] + 1

    def append(self, role, content, entities=None, intent=None, meta_data=None):
        """
        Appends a message to history and persists it to the database.
        Merges intent and entities into meta_data for consistent serialization.
        """
        # Prepare meta_data (merging passed meta_data with entities and intent)
        final_meta = meta_data.copy() if meta_data else {}
        if entities:
            final_meta["entities"] = list(set(entities))
        if intent:
            final_meta["intent"] = intent
            
        msg = {
            "role": role, 
            "content": content,
            "meta_data": final_meta
        }
        self.messages.append(msg)
        
        # Persist to database
        if self.thread_id and self.db_manager:
            self.db_manager.save_message(
                self.thread_id, 
                role, 
                content, 
                self.step_index, 
                final_meta
            )
        
        self.step_index += 1

    def get_full(self):
        """
        Returns the full conversation history for Analyst Agents.
        Prepends the session snapshot to maintain long-term memory.
        """
        full_history = []
        if self.snapshot:
            # Standardize snapshot format for the LLM
            snapshot_content = f"### SESSION SNAPSHOT ###\nNarrative: {self.snapshot.get('narrative', '')}\n\nData Ledger: {json.dumps(self.snapshot.get('data_ledger', {}), indent=2)}"
            full_history.append({"role": "system", "content": snapshot_content})
        
        full_history.extend([dict(m) for m in self.messages])
        return full_history

    def get_clean_history(self, limit=5):
        """
        Returns history for the SQL Generator where assistant messages are 
        replaced by synthetic Data Context messages for pronoun resolution.
        """
        clean_msgs = []
        for msg in self.messages[-limit:]:
            if msg["role"] == "user":
                clean_msgs.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                meta = msg.get("meta_data", {})
                entities = meta.get("entities", [])
                if entities:
                    content = f"Data Context: [Entities: {', '.join(entities)}]"
                else:
                    content = "Assistant provided a general explanation."
                clean_msgs.append({"role": "assistant", "content": content})
        return clean_msgs

    def get_router_history(self, limit=3):
        """
        Returns an Intent-Aware Hybrid Context for the Router:
        - User: Head-slice.
        - Assistant (Analytical): Targeted Conclusion block (fuzzy matching).
        - Assistant (General): Head-slice (captures core message, avoids signatures).
        """
        router_msgs = []
        for msg in self.messages[-limit:]:
            role = msg["role"]
            raw_content = msg["content"]
            meta = msg.get("meta_data", {})
            intent = meta.get("intent")
            
            if role == "user":
                content = raw_content[:300]
            else: # assistant
                entities = meta.get("entities", [])
                entity_prefix = f"Data Context: [Entities: {', '.join(entities)}] " if entities else ""
                
                # Intent-Aware Extraction Logic
                if intent in ["DATA_ANALYSIS", "FINANCIAL_ANALYSIS"]:
                    # Robust Conclusion Detection
                    gist = raw_content
                    patterns = [
                        r'(?i)\*\*(CONCLUSION|FINAL ANSWER|RESULT):\*\*',
                        r'(?i)### (CONCLUSION|FINAL ANSWER|RESULT)',
                        r'(?i)^(CONCLUSION|FINAL ANSWER|RESULT):'
                    ]
                    for pattern in patterns:
                        match = re.split(pattern, raw_content)
                        if len(match) > 1:
                            gist = match[-1].strip()
                            break
                    
                    if len(gist) > 300:
                        gist = "..." + gist[-300:]
                else:
                    # For GENERAL intents: avoid signatures
                    gist = raw_content[:400]
                
                content = f"{entity_prefix}{gist}"
                
            router_msgs.append({"role": role, "content": content})
        return router_msgs

    def compact(self, model=None):
        """
        Triggered when messages exceed max_turns.
        Moves the oldest messages into the recursive snapshot and persists to DB.
        """
        if len(self.messages) <= self.max_turns:
            return False

        print(f"[memory] History limit reached ({len(self.messages)} turns). Compacting...")
        
        # Take the oldest messages to compress (keeping the last 5 for immediate context)
        to_compact = self.messages[:-5]
        self.messages = self.messages[-5:]
        
        # summarize_history handles integrating new info into existing snapshot
        self.snapshot = summarize_history(to_compact, current_snapshot=self.snapshot, model=model)
        
        if self.thread_id and self.db_manager:
            self.db_manager.save_snapshot(
                self.thread_id,
                self.step_index,
                self.snapshot.get("narrative", ""),
                self.snapshot.get("data_ledger", {})
            )
        
        print("[memory] Compaction complete.")
        return True

    def __repr__(self):
        return f"ConversationHistory(turns={len(self.messages)}, has_snapshot={self.snapshot is not None})"
