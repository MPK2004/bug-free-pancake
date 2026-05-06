import os
import json
import re
from llm.client import call_llm

def summarize_history(messages, current_snapshot=None, model=None):
    """
    Recursive Hybrid Summarization: Compresses conversation into Narrative + Data Ledger.
    Maintains zero-loss for critical metrics and IDs.
    """
    if not messages:
        return current_snapshot

    # Use FAST_MODEL for summarization
    model = model or os.getenv('FAST_LLM_MODEL', "openai/gpt-3.5-turbo")
    
    previous_snapshot_str = json.dumps(current_snapshot, indent=2) if current_snapshot else "None"

    prompt = f"""
You are the Memory Compaction Engine for a Mall Leasing AI. 
Your goal is to compress the provided conversation history into a hybrid "Session Snapshot" while maintaining zero-loss for critical data.

STRICT RULES:
1.  **SESSION_NARRATIVE**: A concise, 1-2 paragraph prose summary of the conversation's progress, user intent, and key reasoning.
2.  **DATA_LEDGER**: A lossless, structured dictionary of EVERY exact entity (Malls, Brands, KPIs, Dates, IDs) mentioned. 
3.  **LOSSLESSNESS IS NON-NEGOTIABLE**:
    - You MUST NOT round, omit, abbreviate, or approximate ANY numerical value.
    - If the original value is 22947417.68, write 22947417.68.
    - If a proposal ID is P-9921, it must remain exactly as-is.
4.  **UPSERT LOGIC**: If a metric for a specific ID exists in the previous snapshot and the new messages, keep the most recent one.

### PREVIOUS SNAPSHOT:
{previous_snapshot_str}

### NEW MESSAGES TO COMPACT:
{json.dumps(messages, indent=2)}

### OUTPUT FORMAT:
You MUST respond in raw JSON format with two keys:
{{
  "narrative": "...",
  "data_ledger": {{ "EntityName": {{ "id": "...", "metric": "...", "value": ... }}, ... }}
}}
"""

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
        print(f"[summarizer] Failed to parse JSON: {e}")
        # Fallback
        return {
            "narrative": response_text[:500],
            "data_ledger": current_snapshot.get("data_ledger", {}) if current_snapshot else {}
        }
