import os
import re
import sys
import uuid
import time
from llm.client import call_llm

NAME = "Decision Engine"

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

def redact(s: str) -> str:
    """Masks API keys, Auth headers, cookies, and strips PII/Credentialed URLs."""
    if not isinstance(s, str):
        return s
    s = re.sub('(sk-[A-Za-z0-9]{20,})', '****', s)
    s = re.sub('(Authorization:?\\s*Bearer\\s+)[A-Za-z0-9\\-\\._~+/]+=*', '\\1****', s, flags=re.IGNORECASE)
    s = re.sub('(Cookie:?\\s*)[^(\\s|;)]+', '\\1****', s, flags=re.IGNORECASE)
    s = re.sub('(https?://\\S+?)\\?.*?(?=\\s|$)', '\\1', s)
    return s

def analyze(context: dict):
    """
    Strategic Decision Engine: Deterministic scoring + LLM explanation.
    """
    start_time = time.monotonic()
    query = context.get('query')
    raw_data = context.get('data', [])
    request_id = context.get('request_id') or str(uuid.uuid4())

    if not raw_data:
        return {'status': 'success', 'insights': ['No data available for strategic analysis.'], 'meta': {'rows_used': 0}}

    entity_scores = []
    PRIORITY_MAP = {'high': 1.0, 'medium': 0.6, 'low': 0.3}

    def get_priority_value(raw_p):
        if isinstance(raw_p, (int, float)):
            return float(raw_p)
        p_str = str(raw_p).lower()
        return PRIORITY_MAP.get(p_str, 0.6)

    try:
        # Extract metrics needed for scoring
        yields = [float(d.get('expected_yield') or 0) for d in raw_data]
        demands = [float(d.get('total_sales') or d.get('demand') or d.get('total_demand') or 0) for d in raw_data]
        raw_priorities = [d.get('priority') for d in raw_data]
        priorities = [get_priority_value(p) for p in raw_priorities]

        def robust_normalize(values):
            if not values: return []
            if len(values) == 1: return [0.5]
            min_v, max_v = min(values), max(values)
            if max_v == min_v: return [0.5] * len(values)
            return [(v - min_v) / (max_v - min_v + 1e-6) for v in values]

        norm_yields = robust_normalize(yields)
        norm_demands = robust_normalize(demands)
        norm_priorities = robust_normalize(priorities)
        
        for i, row in enumerate(raw_data):
            ny, nd, np = norm_yields[i], norm_demands[i], norm_priorities[i]
            
            # Formula: Score = (0.5 * normalized_yield) + (0.3 * normalized_demand) + (0.2 * category_strength)
            cat_strength = (0.5 * np) + (0.5 * nd)
            score = (0.5 * ny) + (0.3 * nd) + (0.2 * cat_strength)
            
            # Risk Mitigation: Penalty for low demand
            penalty_factor = min(1.0, nd / 0.1) if nd > 0 else 0.5
            score *= penalty_factor
            
            label = "Optimal Strategic Fit" if score > 0.8 else "Strong Contender" if score > 0.5 else "Defensive Match" if score > 0.2 else "High Risk"
            
            # Explicit Penalty for 0 yield
            if yields[i] == 0:
                score *= 0.5
                label = "High Risk (No Yield Data)"
            
            # Robust name extraction
            name = None
            # Check common keys in order of priority
            for key in ['mall', 'tenant', 'name', 'tenant_name', 'category', 'recommended_tenant', 'location']:
                if row.get(key):
                    name = row.get(key)
                    break
            
            # Fallback: find any string value that isn't a known metric key
            if not name:
                for k, v in row.items():
                    if isinstance(v, str) and k not in ['priority', 'label', 'status']:
                        name = v
                        break
            
            if not name:
                name = f"Entity {i}"
            entity_scores.append({
                "name": name,
                "score": round(score, 4),
                "label": label,
                "raw_metrics": {"yield": yields[i], "demand": demands[i], "priority": priorities[i]}
            })
        
        entity_scores.sort(key=lambda x: x['score'], reverse=True)
        
    except Exception as e:
        print(f"Scoring Engine Error: {e}", file=sys.stderr)

    decision_summary = "\n".join([
        f"- Candidate: {ent['name']} | Score: {ent['score']} | Label: {ent['label']} | Yield: {ent['raw_metrics']['yield']:.2f} | Demand: {ent['raw_metrics']['demand']:,.2f}"
        for ent in entity_scores[:5]
    ])

    analysis_prompt = f"""
Provide a strategic business recommendation based on the following deterministic scores.

User Question: {query}

COMPUTED DECISIONS (Highest Score = Best Strategic Fit):
{decision_summary}

STRICT RULES:
1. REFER TO CANDIDATES BY THEIR ACTUAL NAMES.
2. Your RECOMMENDATION must align with the Rank #1 candidate ({entity_scores[0]['name'] if entity_scores else 'None'}).
3. Explain the TRADE-OFFS (Yield vs. Demand vs. Category Priority) that led to these scores.
4. Formatting: Use the headers below EXACTLY. Do NOT add your own numbering like "1. 1." or "1.".
5. DO NOT override the mathematical ranking.
6. COMPARE NUMBERS CAREFULLY: Verify which demand/yield is actually higher before writing.

OUTPUT FORMAT:
OBSERVATION:
(Highlight the real numbers here)

TRADE-OFF ANALYSIS:
(Explain the balance between metrics)

RECOMMENDATION:
(The final strategic advice)
"""
    return _execute_llm_analysis(analysis_prompt, entity_scores, start_time, request_id, len(raw_data))

def _execute_llm_analysis(prompt, entity_scores, start_time, request_id, rows_count):
    if DEBUG:
        print(f'--- Executing Decision Engine ---', file=sys.stderr)
        print(redact(prompt), file=sys.stderr)

    try:
        response = call_llm([{'role': 'user', 'content': prompt}], timeout=20)
        insights = [line.strip() for line in response.split('\n') if line.strip()]
        
        meta = {
            'request_id': request_id,
            'rows_used': rows_count,
            'duration_ms': int((time.monotonic() - start_time) * 1000),
            'entity_scores': entity_scores
        }

        return {'status': 'success', 'insights': insights, 'meta': meta}
    except Exception as e:
        print(f"Decision Engine LLM Error: {e}", file=sys.stderr)
        return {'status': 'error', 'message': 'Strategic analysis failed.', 'meta': {'request_id': request_id}}
