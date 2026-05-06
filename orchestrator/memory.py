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

    def append(self, role, content, entities=None, intent=None):
        """
        Appends a message to the history.
        Packs auxiliary data into 'meta_data' to match SQLite JSON column schema.
        """
        meta_data = {}
        if entities:
            meta_data["entities"] = list(set(entities))
        if intent:
            meta_data["intent"] = intent
            
        msg = {
            "role": role, 
            "content": content,
            "meta_data": meta_data
        }
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
        import re
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
                    # Robust Conclusion Detection (handles Markdown variations and common keywords)
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
                    
                    # Tail-slice fallback for long analytical outputs
                    if len(gist) > 300:
                        gist = "..." + gist[-300:]
                else:
                    # For GENERAL/GENERAL_RESPONDER intents (emails, greetings):
                    # Use Head-slice to capture the core body and avoid boilerplate signatures at the tail.
                    gist = raw_content[:400]
                
                content = f"{entity_prefix}{gist}"
                
            router_msgs.append({"role": role, "content": content})
        return router_msgs

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
