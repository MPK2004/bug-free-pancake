import os
import json
import uuid
import time
from llm.client import call_llm

NAME = "Prediction Simulator"

def extract_scenario_variables(query: str, history_context: str, model: str) -> dict:
    """
    Uses the LLM to parse the query and extract the target mall, scenario type, and numerical change.
    """
    system_prompt = """You are the Scenario Parser for the MiroFish Simulation Engine.
Extract the target mall name, the proposed action/scenario type, and the numerical value/percentage from the query.

SCENARIO TYPES:
1. RENT_INCREASE: A proposed percentage change in base rent.
2. TENANT_DEPARTURE: A scenario where a specific tenant leaves a mall.
3. CATEGORY_BOOM: A positive shift in category-level demand.

Ensure the mall matches one of our known malls: "Kanyon", "Mall of Istanbul", "Metrocity", "Metropol AVM", "Istinye Park", "Zorlu Center", "Cevahir AVM", "Viaport Outlet", "Emaar Square Mall", "Forum Istanbul", "South China Mall", "Dongguan Central Plaza". If no mall matches, default to "Kanyon".

Return ONLY a JSON object:
{
  "target_mall_name": "Mall Name",
  "action_type": "RENT_INCREASE / TENANT_DEPARTURE / CATEGORY_BOOM",
  "value": 15.0, 
  "target_tenant": "Zara (or null if none)",
  "description": "Brief scenario description"
}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"History: {history_context}\nQuery: {query}"}
    ]
    try:
        response = call_llm(messages, model=model)
        import re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[simulator] Scenario parsing failed: {e}")
    
    # Fallback default
    return {
        "target_mall_name": "Kanyon",
        "action_type": "RENT_INCREASE",
        "value": 15.0,
        "target_tenant": None,
        "description": "Base rent raised by 15% next quarter"
    }

def analyze(context: dict):
    """
    Prediction Simulator Agent:
    Loads the compiled Knowledge Graph, filters for target mall/allies/enemies,
    spawns an OASIS multi-agent swarm communicating via a Structured State Protocol,
    compacts state into the DATA_LEDGER, and renders a professional predictive report.
    """
    start_time = time.monotonic()
    query = context.get('query')
    request_id = context.get('request_id') or str(uuid.uuid4())
    model = context.get('model')
    history = context.get('history', [])

    # Format history context for the scenario parser
    history_str = ""
    for msg in history[-3:]:
        history_str += f"{msg['role'].upper()}: {msg['content'][:200]}\n"

    # 1. Parse Scenario Variables
    scenario = extract_scenario_variables(query, history_str, model)
    target_mall = scenario["target_mall_name"]
    action_type = scenario["action_type"]
    action_value = scenario["value"]
    target_tenant_name = scenario["target_tenant"]

    # 2. Load and Traverse Knowledge Graph
    graph_path = "/home/mahesh/bug-free-pancake/knowledge_graph.json"
    if not os.path.exists(graph_path):
        return {
            'status': 'error',
            'message': "Knowledge Graph not compiled. Please run the ontology builder first by requesting to 'Initialize the MiroFish ontology graph'.",
            'code': 'ONTOLOGY_MISSING',
            'meta': {'request_id': request_id}
        }

    with open(graph_path, "r") as f:
        graph = json.load(f)

    # Find Target Mall Node
    mall_node = next((n for n in graph["nodes"] if n["label"] == "MALL" and n["properties"]["name"].lower() == target_mall.lower()), None)
    if not mall_node:
        # Fallback to Kanyon
        target_mall = "Kanyon"
        mall_node = next((n for n in graph["nodes"] if n["label"] == "MALL" and n["properties"]["name"] == "Kanyon"), None)

    mall_id = mall_node["id"]

    # Find connected nodes (Active tenants, proposals, anchors)
    operating_tenant_ids = []
    proposed_tenant_ids = []
    anchored_tenant_ids = []
    competitor_mall_ids = []

    for e in graph["edges"]:
        if e["target"] == mall_id:
            if e["type"] == "OPERATES_IN":
                operating_tenant_ids.append(e["source"])
            elif e["type"] == "PROPOSED_AT":
                # Find the proposals and get their tenant
                prop_node = next((n for n in graph["nodes"] if n["id"] == e["source"]), None)
                if prop_node:
                    # Find T -> P proposals edge
                    t_prop_edge = next((edge for edge in graph["edges"] if edge["target"] == e["source"] and edge["type"] == "PROPOSES"), None)
                    if t_prop_edge:
                        proposed_tenant_ids.append(t_prop_edge["source"])
            elif e["type"] == "ANCHORS":
                anchored_tenant_ids.append(e["source"])
        elif e["source"] == mall_id:
            if e["type"] == "COMPETES_WITH" and e["target"].startswith("M-"):
                competitor_mall_ids.append(e["target"])

    # Resolve names of key actors
    operating_tenants = [n for n in graph["nodes"] if n["id"] in operating_tenant_ids]
    proposed_tenants = [n for n in graph["nodes"] if n["id"] in proposed_tenant_ids]
    anchored_tenants = [n for n in graph["nodes"] if n["id"] in anchored_tenant_ids]
    competitor_malls = [n for n in graph["nodes"] if n["id"] in competitor_mall_ids]

    # Select Primary Target Tenant for the simulation
    if target_tenant_name:
        primary_tenant_node = next((n for n in graph["nodes"] if n["label"] == "TENANT" and n["properties"]["name"].lower() == target_tenant_name.lower()), None)
    else:
        primary_tenant_node = anchored_tenants[0] if anchored_tenants else (operating_tenants[0] if operating_tenants else None)

    if not primary_tenant_node:
        primary_tenant_node = {"id": "T-Unknown", "properties": {"name": "Anchor Tenant", "category": "Retail"}}

    primary_tenant_id = primary_tenant_node["id"]
    primary_tenant_name = primary_tenant_node["properties"]["name"]

    # Select Competitor Tenant (preferably same category)
    comp_tenant_node = next((t for t in operating_tenants + proposed_tenants if t["id"] != primary_tenant_id and t["properties"]["category"] == primary_tenant_node["properties"]["category"]), None)
    if not comp_tenant_node:
        comp_tenant_node = next((t for t in operating_tenants + proposed_tenants if t["id"] != primary_tenant_id), None)
    if not comp_tenant_node:
        comp_tenant_node = {"id": "T-Comp", "properties": {"name": "Competitor Retailer", "category": primary_tenant_node["properties"]["category"]}}

    # Select Competitor Mall
    comp_mall_node = competitor_malls[0] if competitor_malls else next((n for n in graph["nodes"] if n["label"] == "MALL" and n["id"] != mall_id), None)
    if not comp_mall_node:
        comp_mall_node = {"id": "M-Comp", "properties": {"name": "Competing Central Mall"}}

    # Build Sandbox Context Payload
    sandbox_context = {
        "target_mall": target_mall,
        "action_type": action_type,
        "action_value": action_value,
        "primary_tenant": {
            "id": primary_tenant_id,
            "name": primary_tenant_name,
            "category": primary_tenant_node["properties"]["category"],
            "is_anchor": primary_tenant_id in anchored_tenant_ids
        },
        "competitor_tenant": {
            "id": comp_tenant_node["id"],
            "name": comp_tenant_node["properties"]["name"],
            "category": comp_tenant_node["properties"]["category"]
        },
        "competitor_mall": {
            "id": comp_mall_node["id"],
            "name": comp_mall_node["properties"]["name"]
        }
    }

    # --- Structured State Protocol Simulation Rounds ---
    rounds_log = []

    # Round 1: Operator Proposes and Tenants React
    # Agent 1: Operator
    op_round1_prompt = f"""You are the Mall Operator of {target_mall}.
You are initiating a MiroFish multi-agent negotiation.
The proposed scenario: {action_type} of {action_value}%.
Your goal is to maximize the mall's revenue and occupancy.

You MUST communicate via this strict JSON format (NO PROSE):
{{
  "agent_id": "OP-Operator",
  "stance": "COOPERATIVE / NEUTRAL / HOSTILE / RESIGNED",
  "action_taken": "PROPOSE / COUNTER / THREATEN_DEPARTURE / ACCEPT / REJECT",
  "counter_offer_percentage": {action_value},
  "internal_monologue": "State your internal strategic reasoning here."
}}
"""
    op_r1_response = call_llm([{"role": "user", "content": op_round1_prompt}], model=model)
    op_r1_state = parse_agent_json(op_r1_response, "OP-Operator")
    rounds_log.append(op_r1_state)

    # Agent 2: Primary Tenant (Anchor) reacts
    tenant_r1_prompt = f"""You are the Tenant Manager of {primary_tenant_name} (ID: {primary_tenant_id}) at {target_mall}.
Your category is {primary_tenant_node['properties']['category']}.
Is Anchor Tenant: {sandbox_context['primary_tenant']['is_anchor']}.

The Mall Operator has proposed the following negotiation state:
{json.dumps(op_r1_state, indent=2)}

Your goal is to keep base rent as low as possible and preserve your profit margins. If you are an ANCHOR, leverage your 30%+ local market share to threaten departure to the competing mall {comp_mall_node['properties']['name']}.

You MUST communicate via this strict JSON format (NO PROSE):
{{
  "agent_id": "{primary_tenant_id}",
  "stance": "COOPERATIVE / NEUTRAL / HOSTILE / RESIGNED",
  "action_taken": "PROPOSE / COUNTER / THREATEN_DEPARTURE / ACCEPT / REJECT",
  "counter_offer_percentage": 5.0, 
  "internal_monologue": "State your internal strategic reasoning here."
}}
"""
    t_r1_response = call_llm([{"role": "user", "content": tenant_r1_prompt}], model=model)
    t_r1_state = parse_agent_json(t_r1_response, primary_tenant_id)
    rounds_log.append(t_r1_state)

    # Round 2: Competitor Brand Reacts & Competitor Mall Operator Poaches
    # Agent 3: Competitor Brand (e.g. H&M)
    comp_brand_prompt = f"""You are the Brand Manager of {comp_tenant_node['properties']['name']} (ID: {comp_tenant_node['id']}) at {target_mall}.
You compete directly with {primary_tenant_name} in the {comp_tenant_node['properties']['category']} category.

Here is the Round 1 negotiation log between the Operator and {primary_tenant_name}:
{json.dumps(rounds_log, indent=2)}

If the Anchor tenant ({primary_tenant_name}) threatens departure, this is a massive opportunity for you to demand their premium retail location, or negotiate a lower rent rate.

You MUST communicate via this strict JSON format (NO PROSE):
{{
  "agent_id": "{comp_tenant_node['id']}",
  "stance": "COOPERATIVE / NEUTRAL / HOSTILE / RESIGNED",
  "action_taken": "PROPOSE / COUNTER / THREATEN_DEPARTURE / ACCEPT / REJECT",
  "counter_offer_percentage": 7.0,
  "internal_monologue": "State your internal strategic reasoning here."
}}
"""
    comp_brand_response = call_llm([{"role": "user", "content": comp_brand_prompt}], model=model)
    comp_brand_state = parse_agent_json(comp_brand_response, comp_tenant_node['id'])
    rounds_log.append(comp_brand_state)

    # Agent 4: Competitor Mall Operator (Poacher)
    comp_mall_prompt = f"""You are the Leasing Director of {comp_mall_node['properties']['name']} (ID: {comp_mall_node['id']}), the primary competitor of {target_mall}.
You see that the Anchor Tenant {primary_tenant_name} is hostile towards {target_mall}'s rent proposals:
{json.dumps(t_r1_state, indent=2)}

You want to POACH {primary_tenant_name}. Pitch them an offer to move to your mall by offering a highly attractive rent structure (e.g. a discount on rent or better revenue shares).

You MUST communicate via this strict JSON format (NO PROSE):
{{
  "agent_id": "{comp_mall_node['id']}",
  "stance": "COOPERATIVE / NEUTRAL / HOSTILE / RESIGNED",
  "action_taken": "PROPOSE / COUNTER / THREATEN_DEPARTURE / ACCEPT / REJECT",
  "counter_offer_percentage": -5.0, 
  "internal_monologue": "State your internal strategic reasoning here."
}}
"""
    comp_mall_response = call_llm([{"role": "user", "content": comp_mall_prompt}], model=model)
    comp_mall_state = parse_agent_json(comp_mall_response, comp_mall_node['id'])
    rounds_log.append(comp_mall_state)

    # Round 3: Final Resolution & Convergence
    # Mall Operator reacts to poaching and tenant rebellion
    op_r3_prompt = f"""You are the Mall Operator of {target_mall}.
The round negotiation logs show that {primary_tenant_name} has reacted strongly, and your primary competitor {comp_mall_node['properties']['name']} is trying to poach them with this offer:
{json.dumps(comp_mall_state, indent=2)}

If your anchor tenant ({primary_tenant_name}) leaves, it will trigger a cascade failure (other tenants will demand rent reductions, footfall will drop). You must make a final counter-proposal to retain them, or stand your ground and risk loss.

You MUST communicate via this strict JSON format (NO PROSE):
{{
  "agent_id": "OP-Operator",
  "stance": "COOPERATIVE / NEUTRAL / HOSTILE / RESIGNED",
  "action_taken": "PROPOSE / COUNTER / THREATEN_DEPARTURE / ACCEPT / REJECT",
  "counter_offer_percentage": 6.5,
  "internal_monologue": "State your final compromise or hard stance reasoning."
}}
"""
    op_r3_response = call_llm([{"role": "user", "content": op_r3_prompt}], model=model)
    op_r3_state = parse_agent_json(op_r3_response, "OP-Operator")
    rounds_log.append(op_r3_state)

    # Tenant makes final decision
    tenant_r3_prompt = f"""You are the Tenant Manager of {primary_tenant_name} (ID: {primary_tenant_id}).
Here is the final round of poaching and operator compromise offers:
Operator's Final Proposal: {json.dumps(op_r3_state, indent=2)}
Poaching Offer: {json.dumps(comp_mall_state, indent=2)}

Make your final stance decision (ACCEPT operator rent increase, reject it and DEPART to competitor mall, or agree to a middle ground).

You MUST communicate via this strict JSON format (NO PROSE):
{{
  "agent_id": "{primary_tenant_id}",
  "stance": "COOPERATIVE / NEUTRAL / HOSTILE / RESIGNED",
  "action_taken": "ACCEPT / THREATEN_DEPARTURE / REJECT",
  "counter_offer_percentage": 5.0, 
  "internal_monologue": "State your final convergence reasoning."
}}
"""
    t_r3_response = call_llm([{"role": "user", "content": tenant_r3_prompt}], model=model)
    t_r3_state = parse_agent_json(t_r3_response, primary_tenant_id)
    rounds_log.append(t_r3_state)

    # --- Step 5: State Compaction & DATA_LEDGER Writeback ---
    # Parse final numeric values
    final_rent_percentage = t_r3_state.get("counter_offer_percentage", action_value)
    
    # Calculate simple deterministic outcome based on stances
    if t_r3_state["action_taken"] == "ACCEPT":
        retention_prob = 100.0
        final_negotiated_rent = final_rent_percentage
        occupancy_impact = 0.0
    elif t_r3_state["action_taken"] == "REJECT" or t_r3_state["stance"] == "HOSTILE":
        # Anchor left!
        retention_prob = 15.0
        final_negotiated_rent = 0.0
        occupancy_impact = -30.0 # Anchor vacancy triggers major loss
    else:
        # Compromise reached
        retention_prob = 75.0
        final_negotiated_rent = (final_rent_percentage + op_r3_state.get("counter_offer_percentage", action_value)) / 2.0
        occupancy_impact = 0.0

    # Write to memory's DATA_LEDGER
    # In pipeline, the history object has thread_id and db_manager, but history is not directly passed to agent.analyze.
    # Wait, history is in context["history"], which is a snapshot!
    # To update the actual ConversationHistory in memory, we can return the ledger state updates in the return dict's meta!
    # In execute_step or pipeline, we can check if the agent returned a 'data_ledger' and merge it!
    # Let's check: our history object has db_manager and thread_id, so let's verify if we can write to DB or if we can return it.
    # In `memory.py`, conversation history is compacted and loaded.
    # We can write directly to chat_history.db's thread metadata if we want, or just return the new metrics!
    # Let's return the `data_ledger` update in the return dictionary so the pipeline can safely integrate it.
    data_ledger_updates = {
        "active_scenario": {
            "mall": target_mall,
            "action": action_type,
            "original_proposed_rent_change": action_value,
            "negotiated_rent_change": final_negotiated_rent,
            "anchor_retention_probability": retention_prob,
            "occupancy_rate_impact": occupancy_impact,
            "poach_risk": "HIGH" if retention_prob < 50 else "LOW"
        }
    }

    # --- Step 6: ReportAgent Renders Predictive Report ---
    report_prompt = f"""You are the MiroFish ReportAgent.
Compile the following structured multi-agent negotiation logs into a premium predictive forecast report:

SCENARIO CONTEXT:
{json.dumps(sandbox_context, indent=2)}

SIMULATION ROUND LOGS:
{json.dumps(rounds_log, indent=2)}

CONVERGED FORECAST METRICS:
- Negotiated Rent Adjustment: {final_negotiated_rent:.2f}% (Originally: {action_value:.2f}%)
- Anchor Tenant Retention Probability: {retention_prob:.1f}%
- Occupancy Footfall Impact: {occupancy_impact:.1f}%
- Poach Risk Stance: {"HIGH RISK - Direct poaching attempt by " + comp_mall_node['properties']['name'] if retention_prob < 50 else "STABLE COMPROMISE"}

Generate a highly professional strategic report. Use elegant formatting, a premium layout, clear sections, bullet points, and strategic takeaways. Limit any conversational filler. Highlight the exact negotiation positions, internal monologues, and actions.
"""
    final_report = call_llm([{"role": "user", "content": report_prompt}], model=model)

    insights = [final_report]
    
    meta = {
        'request_id': request_id,
        'duration_ms': int((time.monotonic() - start_time) * 1000),
        'model': model,
        'data_ledger': data_ledger_updates
    }

    return {'status': 'success', 'insights': insights, 'meta': meta}

def parse_agent_json(response: str, agent_id: str) -> dict:
    try:
        import re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            state = json.loads(match.group())
            # Enforce keys
            return {
                "agent_id": agent_id,
                "stance": state.get("stance", "NEUTRAL").upper(),
                "action_taken": state.get("action_taken", "PROPOSE").upper(),
                "counter_offer_percentage": float(state.get("counter_offer_percentage", 0.0)),
                "internal_monologue": state.get("internal_monologue", "Negotiating baseline metrics.")
            }
    except Exception as e:
        print(f"[simulator] Parser error for agent {agent_id}: {e}")
    
    return {
        "agent_id": agent_id,
        "stance": "NEUTRAL",
        "action_taken": "COUNTER",
        "counter_offer_percentage": 0.0,
        "internal_monologue": "Baseline protocol fallback."
    }
