import json
from llm.summarizer import summarize_history

class ConversationHistory:
    """
    Manages the persistent state of the conversation.
    Handles selective context injection and recursive compaction.
    """
    def __init__(self, thread_id=None, db_manager=None, max_turns=10):
        self.thread_id = thread_id
        self.db_manager = db_manager
        self.max_turns = max_turns
        
        self.messages = []
        self.snapshot = None # { "narrative": ..., "data_ledger": ... }
        self.step_index = 0

        if self.thread_id and self.db_manager:
            self._load_from_db()

    def _load_from_db(self):
        # Load messages
        db_messages = self.db_manager.get_thread_messages(self.thread_id)
        self.messages = []
        for msg in db_messages:
            self.messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "meta_data": json.loads(msg["meta_data"]) if msg["meta_data"] else None
            })
            if msg["step_index"] >= self.step_index:
                self.step_index = msg["step_index"] + 1
        
        # Load latest snapshot
        db_snapshot = self.db_manager.get_latest_snapshot(self.thread_id)
        if db_snapshot:
            self.snapshot = {
                "narrative": db_snapshot["narrative"],
                "data_ledger": json.loads(db_snapshot["data_ledger"]) if db_snapshot["data_ledger"] else {}
            }
            # Ensure step_index is at least after the snapshot
            if db_snapshot["step_index"] >= self.step_index:
                self.step_index = db_snapshot["step_index"] + 1

    def append(self, role, content, meta_data=None):
        """
        Appends a message and persists it if DB is connected.
        """
        msg = {"role": role, "content": content, "meta_data": meta_data}
        self.messages.append(msg)
        
        if self.thread_id and self.db_manager:
            self.db_manager.save_message(
                self.thread_id, 
                role, 
                content, 
                self.step_index, 
                meta_data
            )
        
        self.step_index += 1

    def get_full(self):
        """
        Returns full history with snapshot prepended as a system message.
        Used by Analyst Agents.
        """
        history = []
        if self.snapshot:
            snapshot_msg = {
                "role": "system",
                "content": f"### SESSION SNAPSHOT ###\nNarrative: {self.snapshot['narrative']}\n\nData Ledger: {json.dumps(self.snapshot['data_ledger'], indent=2)}"
            }
            history.append(snapshot_msg)
        
        history.extend(self.messages)
        return history

    def get_clean_history(self, last_n=3):
        """
        Returns last N turns only. Used by Router.
        """
        return self.messages[-last_n:] if self.messages else []

    def get_truncated(self):
        """
        Returns history for SQL Generator (pronoun resolution).
        Focuses on user queries and extracted entities.
        """
        truncated = []
        for msg in self.messages:
            if msg["role"] == "user":
                truncated.append(msg)
            elif msg["role"] == "assistant":
                # Use 'or {}' to handle cases where meta_data is explicitly None (common after DB load)
                content = (msg.get("meta_data") or {}).get("entities", [])
                if not content:
                    content = msg["content"][:200] + "..."
                truncated.append({"role": "assistant", "content": str(content)})
        return truncated

    def compact(self, model=None):
        """
        Triggers compaction if history exceeds max_turns.
        """
        if len(self.messages) <= self.max_turns:
            return False

        print(f"[MEMORY] Compacting history (turns: {len(self.messages)})...")
        
        # We compact the oldest half of messages
        to_compact = self.messages[:-5]
        remaining = self.messages[-5:]

        new_snapshot = summarize_history(to_compact, self.snapshot, model=model)
        self.snapshot = new_snapshot
        self.messages = remaining

        if self.thread_id and self.db_manager:
            self.db_manager.save_snapshot(
                self.thread_id,
                self.step_index,
                self.snapshot["narrative"],
                self.snapshot["data_ledger"]
            )
        
        return True
