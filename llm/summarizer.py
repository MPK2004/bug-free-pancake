import os
import json
from llm.client import call_llm

SUMMARIZER_PROMPT = """
You are a memory compaction engine for an AI agent. Your goal is to compress a conversation history while maintaining zero-loss for critical data.

### COMPACTION RULES:
1.  **SESSION_NARRATIVE**: A concise, 2-3 paragraph summary of the conversation's progress, user intent, and key discoveries.
2.  **DATA_LEDGER**: A structured list of every exact entity (Malls, Brands, KPIs, Dates, IDs) mentioned. If a specific dollar amount or metric was calculated, it MUST be preserved exactly.

### CURRENT STATE:
Previous Snapshot: {previous_snapshot}

### NEW MESSAGES TO COMPACT:
{new_messages}

### OUTPUT FORMAT:
You MUST respond in raw JSON format with two keys:
{{
  "narrative": "...",
  "data_ledger": {{ ... }}
}}
"""

def summarize_history(messages, current_snapshot=None, model=None):
    """
    Recursive Hybrid Summarization: Compresses conversation into Narrative + Data Ledger.
    """
    if not model:
        model = os.getenv('FAST_LLM_MODEL', "openai/gpt-3.5-turbo") # Default fast model

    prompt = SUMMARIZER_PROMPT.format(
        previous_snapshot=json.dumps(current_snapshot) if current_snapshot else "None",
        new_messages=json.dumps(messages, indent=2)
    )

    system_msg = {"role": "system", "content": "You are a precise data summarizer. Output ONLY raw JSON."}
    user_msg = {"role": "user", "content": prompt}

    response_text = call_llm([system_msg, user_msg], model=model)

    try:
        # Strip potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except Exception as e:
        print(f"[ERROR] Failed to parse summarizer response: {e}")
        # Fallback: return a basic narrative if JSON fails
        return {
            "narrative": response_text[:500],
            "data_ledger": current_snapshot.get("data_ledger", {}) if current_snapshot else {}
        }
