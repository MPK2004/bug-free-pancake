import json

class ConversationHistory:
    """
    Manages the persistent state of the conversation.
    Handles selective context injection for different pipeline nodes.
    """
    def __init__(self):
        self.messages = []
        # Store metadata per turn to enable deterministic context injection
        self.turn_metadata = []

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
        """
        # Return a copy to prevent accidental mutation
        return [dict(m) for m in self.messages]

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

    def __repr__(self):
        return f"ConversationHistory(turns={len(self.messages)})"
