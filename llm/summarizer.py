import os
import json
from llm.client import call_llm

def summarize_history(messages, current_snapshot=None, model=None):
    """
    Recursive Hybrid Summarization: Compresses conversation into Narrative + Data Ledger.
    Ensures precise IDs and metrics are preserved in a structured format.
    """
    if not messages:
        return current_snapshot

    # Use FAST_MODEL for summarization to keep costs and latency low
    model = model or os.getenv("FAST_LLM_MODEL")
    
    snapshot_context = ""
    if current_snapshot:
        snapshot_context = f"\nEXISTING SESSION SNAPSHOT (to be updated):\n{current_snapshot}\n"

    prompt = f"""
You are the Memory Compaction Engine for a Mall Leasing AI. 
Your task is to compress the provided conversation history into a hybrid "Session Snapshot".

STRICT RULES:
1. <SESSION_NARRATIVE>: Write a concise (1-2 paragraph) prose summary of the conversation's intent, reasoning, and any strategic decisions made.
2. <DATA_LEDGER>: Create a lossless, structured markdown table of ALL specific entities, primary keys (IDs), and numerical metrics (demand, yield, adjusted values, etc.) mentioned in the data results.
3. LOSSLESSNESS IS NON-NEGOTIABLE:
   - You MUST NOT round, omit, abbreviate, or approximate ANY numerical value.
   - If the original value is 22947417.68, write 22947417.68. NOT "22.95M", NOT "~23M", NOT "22,947,418".
   - If a proposal ID is P-9921 or 12345, it must remain exactly as-is.
   - If you are unsure of the exact value, write "UNKNOWN" rather than approximating.
4. UPSERT LOGIC: If an EXISTING SNAPSHOT is provided, integrate the new information into it. If a metric for a specific ID exists in both, keep the most recent one.

{snapshot_context}

NEW MESSAGES TO COMPRESS:
{json.dumps(messages, indent=2)}

OUTPUT FORMAT:
<SESSION_NARRATIVE>
...prose...
</SESSION_NARRATIVE>

<DATA_LEDGER>
| Entity | ID | Metric | Value |
| :--- | :--- | :--- | :--- |
...table...
</DATA_LEDGER>
"""

    response = call_llm([{"role": "user", "content": prompt}], model=model)
    return response.strip()
