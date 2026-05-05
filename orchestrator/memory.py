import json

class ConversationHistory:
    """
    Manages the persistent state of the conversation.
    Handles selective context injection for different pipeline nodes.
    """
    def __init__(self, max_turns=20):
        self.messages = []
        # The session snapshot stores the compressed Narrative + Data Ledger
        self.snapshot = None
        self.max_turns = max_turns

    def append(self, role, content, entities=None):
        """
        Appends a message to the history.
        If role is 'assistant', entities (extracted from data context) can be provided.
        """
        msg = {"role": role, "content": content}
        if entities:
            msg["entities"] = list(set(entities))
        self.messages.append(msg)

    def get_full(self):
        """
        Returns the full conversation history for Analyst Agents.
        Prepends the session snapshot (if it exists) to maintain long-term memory.
        """
        full_history = []
        if self.snapshot:
            full_history.append({"role": "system", "content": f"SESSION SNAPSHOT (Historical Context):\n{self.snapshot}"})
        
        full_history.extend([dict(m) for m in self.messages])
        return full_history

    def get_truncated(self, limit=3):
        """
        Returns the last N messages for the Router to maintain low latency.
        """
        return [dict(m) for m in self.messages[-limit:]] if limit > 0 else []

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
                entities = msg.get("entities", [])
                if entities:
                    # Synthetic context that anchors pronouns to real data entities
                    content = f"Data Context: [Entities: {', '.join(entities)}]"
                else:
                    # Fallback for general responses
                    content = "Assistant provided a general explanation."
                clean_msgs.append({"role": "assistant", "content": content})
        return clean_msgs

    def compact(self, model=None):
        """
        Triggered when messages exceed max_turns.
        Moves the oldest 10 messages into the recursive snapshot.
        """
        if len(self.messages) <= self.max_turns:
            return

        print(f"[memory] History limit reached ({len(self.messages)} turns). Compacting...")
        
        # Take the oldest 10 messages to compress
        to_compact = self.messages[:10]
        self.messages = self.messages[10:]
        
        from llm.summarizer import summarize_history
        self.snapshot = summarize_history(to_compact, current_snapshot=self.snapshot, model=model)
        print("[memory] Compaction complete.")

    def __repr__(self):
        return f"ConversationHistory(turns={len(self.messages)}, has_snapshot={self.snapshot is not None})"
