import os
import json
import uuid
import time
from db.connection import get_db_connection
from llm.client import call_llm

NAME = "Ontology Builder"

# Static mapping for Istanbul/Dongguan malls
MALL_TO_CITY = {
    "Mall of Istanbul": "Istanbul",
    "Kanyon": "Istanbul",
    "Metrocity": "Istanbul",
    "Metropol AVM": "Istanbul",
    "Istinye Park": "Istanbul",
    "Zorlu Center": "Istanbul",
    "Cevahir AVM": "Istanbul",
    "Viaport Outlet": "Istanbul",
    "Emaar Square Mall": "Istanbul",
    "Forum Istanbul": "Istanbul",
    "South China Mall": "Dongguan",
    "Dongguan Central Plaza": "Dongguan"
}

def get_city_for_mall(mall_name: str) -> str:
    if mall_name in MALL_TO_CITY:
        return MALL_TO_CITY[mall_name]
    if "dongguan" in mall_name.lower():
        return "Dongguan"
    return "Istanbul" # Default fallback

def analyze(context: dict):
    """
    Ontology Builder Agent:
    Compiles database records into an immutable, cognitive Knowledge Graph.
    Outputs the result to /home/mahesh/bug-free-pancake/knowledge_graph.json.
    """
    start_time = time.monotonic()
    query = context.get('query')
    request_id = context.get('request_id') or str(uuid.uuid4())
    model = context.get('model')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # --- Step 1: Deterministic Node & Edge Fetching ---
        # 1. Fetch Malls
        cur.execute("SELECT id, name FROM malls;")
        malls_rows = cur.fetchall()
        malls = [{"id": r[0], "name": r[1]} for r in malls_rows]

        # 2. Fetch Tenants
        cur.execute("SELECT id, name, category, brand_type FROM tenants;")
        tenants_rows = cur.fetchall()
        tenants = [{"id": r[0], "name": r[1], "category": r[2], "brand_type": r[3]} for r in tenants_rows]

        # 3. Fetch Active Agreements
        cur.execute("""
            SELECT ra.id, ra.tenant_id, ra.mall_id, ra.base_rent, ra.revenue_share_percentage, t.name, m.name, t.category
            FROM rental_agreements ra
            JOIN tenants t ON ra.tenant_id = t.id
            JOIN malls m ON ra.mall_id = m.id
            WHERE ra.status = 'Active';
        """)
        agreements_rows = cur.fetchall()
        agreements = [{
            "id": r[0], "tenant_id": r[1], "mall_id": r[2], "base_rent": r[3],
            "revenue_share": r[4], "tenant_name": r[5], "mall_name": r[6], "category": r[7]
        } for r in agreements_rows]

        # 4. Fetch Proposals
        cur.execute("""
            SELECT p.id, p.tenant_id, p.mall_id, p.proposed_rent, p.expected_sales, p.expected_yield, t.name, m.name, t.category
            FROM proposals p
            JOIN tenants t ON p.tenant_id = t.id
            JOIN malls m ON p.mall_id = m.id;
        """)
        proposals_rows = cur.fetchall()
        proposals = [{
            "id": r[0], "tenant_id": r[1], "mall_id": r[2], "proposed_rent": r[3],
            "expected_sales": r[4], "expected_yield": r[5], "tenant_name": r[6], "mall_name": r[7], "category": r[8]
        } for r in proposals_rows]

        # 5. Fetch Transaction Aggregates by Mall and Category
        cur.execute("""
            SELECT shopping_mall, category, SUM(total_sales) as total_sales, COUNT(*) as txn_count
            FROM transactions
            GROUP BY shopping_mall, category;
        """)
        txn_rows = cur.fetchall()
        txn_aggregates = {}
        for r in txn_rows:
            mall_name = r[0]
            cat = r[1]
            sales = float(r[2] or 0)
            txn_aggregates.setdefault(mall_name, {})[cat] = sales

        # --- Scaffold Graph Structure ---
        nodes = []
        edges = []
        added_nodes = set()

        # Add Mall and City Nodes and LOCATED_IN edges
        for m in malls:
            mall_id_str = f"M-{m['id']}"
            city_name = get_city_for_mall(m['name'])
            city_id_str = f"C-{city_name}"

            if mall_id_str not in added_nodes:
                nodes.append({
                    "id": mall_id_str,
                    "label": "MALL",
                    "properties": {"name": m['name']}
                })
                added_nodes.add(mall_id_str)

            if city_id_str not in added_nodes:
                nodes.append({
                    "id": city_id_str,
                    "label": "CITY",
                    "properties": {"name": city_name}
                })
                added_nodes.add(city_id_str)

            edges.append({
                "source": mall_id_str,
                "target": city_id_str,
                "type": "LOCATED_IN"
            })

        # Add Tenant and Category Nodes and BELONGS_TO edges
        for t in tenants:
            tenant_id_str = f"T-{t['id']}"
            cat_id_str = f"CT-{t['category']}"

            if tenant_id_str not in added_nodes:
                nodes.append({
                    "id": tenant_id_str,
                    "label": "TENANT",
                    "properties": {
                        "name": t['name'],
                        "brand_type": t['brand_type'],
                        "category": t['category']
                    }
                })
                added_nodes.add(tenant_id_str)

            if cat_id_str not in added_nodes:
                nodes.append({
                    "id": cat_id_str,
                    "label": "CATEGORY",
                    "properties": {"name": t['category']}
                })
                added_nodes.add(cat_id_str)

            edges.append({
                "source": tenant_id_str,
                "target": cat_id_str,
                "type": "BELONGS_TO"
            })

        # Add Rental Agreements as Edges (OPERATES_IN)
        for ra in agreements:
            edges.append({
                "source": f"T-{ra['tenant_id']}",
                "target": f"M-{ra['mall_id']}",
                "type": "OPERATES_IN",
                "properties": {
                    "base_rent": ra['base_rent'],
                    "revenue_share_percentage": ra['revenue_share']
                }
            })

        # Add Proposals as Nodes and connect them
        for p in proposals:
            prop_id_str = f"P-{p['id']}"
            nodes.append({
                "id": prop_id_str,
                "label": "PROPOSAL",
                "properties": {
                    "proposed_rent": p['proposed_rent'],
                    "expected_sales": p['expected_sales'],
                    "expected_yield": p['expected_yield']
                }
            })
            edges.append({
                "source": f"T-{p['tenant_id']}",
                "target": prop_id_str,
                "type": "PROPOSES"
            })
            edges.append({
                "source": prop_id_str,
                "target": f"M-{p['mall_id']}",
                "type": "PROPOSED_AT"
            })

        # Add Geographic Mall COMPETES_WITH Edges
        # If two malls share the same city, they compete
        for i in range(len(malls)):
            for j in range(i + 1, len(malls)):
                m1 = malls[i]
                m2 = malls[j]
                city1 = get_city_for_mall(m1['name'])
                city2 = get_city_for_mall(m2['name'])
                if city1 == city2:
                    edges.append({
                        "source": f"M-{m1['id']}",
                        "target": f"M-{m2['id']}",
                        "type": "COMPETES_WITH",
                        "properties": {"reason": "Shared geographic city catchment area"}
                    })

        # --- Step 2: Local Pareto Culling within Each Mall's Ecosystem ---
        mall_payloads = []
        for m in malls:
            mall_id = m['id']
            mall_name = m['name']

            # Find all active tenants in this mall
            local_agreements = [ra for ra in agreements if ra['mall_id'] == mall_id]
            # Find all proposed tenants in this mall
            local_proposals = [p for p in proposals if p['mall_id'] == mall_id]

            # Merge to get unique list of tenants operating or proposed in this mall
            local_tenant_dict = {}
            for ra in local_agreements:
                local_tenant_dict[ra['tenant_id']] = {
                    "id": ra['tenant_id'],
                    "name": ra['tenant_name'],
                    "category": ra['category'],
                    "status": "Active"
                }
            for p in local_proposals:
                if p['tenant_id'] not in local_tenant_dict:
                    local_tenant_dict[p['tenant_id']] = {
                        "id": p['tenant_id'],
                        "name": p['tenant_name'],
                        "category": p['category'],
                        "status": "Proposed"
                    }

            if not local_tenant_dict:
                continue

            # Calculate estimated volume per category in this mall
            # We split the category's total sales equally among the tenants in that category in this mall
            cat_tenant_counts = {}
            for t_info in local_tenant_dict.values():
                cat_tenant_counts[t_info['category']] = cat_tenant_counts.get(t_info['category'], 0) + 1

            local_tenants_with_volume = []
            mall_sales_data = txn_aggregates.get(mall_name, {})
            
            for t_info in local_tenant_dict.values():
                cat_sales = mall_sales_data.get(t_info['category'], 0.0)
                # Split equally among active/proposed tenants in this category
                count = cat_tenant_counts.get(t_info['category'], 1)
                allocated_volume = cat_sales / count
                
                # Fetch proposal expected yield if applicable
                ey = 0.0
                if t_info['status'] == "Proposed":
                    match_p = next((p for p in local_proposals if p['tenant_id'] == t_info['id']), None)
                    if match_p:
                        ey = match_p['expected_yield']

                local_tenants_with_volume.append({
                    "id": t_info['id'],
                    "name": t_info['name'],
                    "category": t_info['category'],
                    "status": t_info['status'],
                    "volume": allocated_volume,
                    "expected_yield": ey
                })

            # Sort descending by volume
            local_tenants_with_volume.sort(key=lambda x: x['volume'], reverse=True)
            local_total_volume = sum(x['volume'] for x in local_tenants_with_volume)

            # Local Pareto Cutoff (cumulative sum <= 80%)
            top_candidates = []
            culled_tenants = []
            running_sum = 0.0

            for t_vol in local_tenants_with_volume:
                percentage = (t_vol['volume'] / local_total_volume * 100) if local_total_volume > 0 else 0.0
                if local_total_volume == 0 or running_sum < (local_total_volume * 0.8):
                    top_candidates.append({
                        "tenant_id": f"T-{t_vol['id']}",
                        "tenant_name": t_vol['name'],
                        "category": t_vol['category'],
                        "status": t_vol['status'],
                        "volume": t_vol['volume'],
                        "percentage": percentage,
                        "expected_yield": t_vol['expected_yield']
                    })
                    running_sum += t_vol['volume']
                else:
                    culled_tenants.append({
                        "tenant_id": f"T-{t_vol['id']}",
                        "tenant_name": t_vol['name'],
                        "category": t_vol['category'],
                        "volume": t_vol['volume'],
                        "percentage": percentage
                    })

            sum_culled_volume = sum(x['volume'] for x in culled_tenants)
            sum_culled_percentage = sum(x['percentage'] for x in culled_tenants)

            mall_payloads.append({
                "mall_name": mall_name,
                "mall_id": f"M-{mall_id}",
                "total_tenants": len(local_tenants_with_volume),
                "top_candidates": top_candidates,
                "aggregated_noise": {
                    "tenant_count": len(culled_tenants),
                    "cumulative_volume": sum_culled_volume,
                    "cumulative_percentage": sum_culled_percentage
                }
            })

        # --- Step 3: LLM Cognitive Pass for Anchor & Behavioral Edges ---
        system_prompt = """You are the MiroFish Ontology Builder. 
Your job is to analyze the local statistics payload of shopping malls and identify high-value cognitive/behavioral edges:

EDGE TYPES TO DEDUCE:
1. (TENANT) -[ANCHORS]-> (MALL): Triggered when a tenant has dominant market power in the mall (e.g. represents > 20% of the mall's volume, is a premium/luxury anchor, or has high expected yield).
2. (TENANT) -[COMPETES_WITH]-> (TENANT): Triggered when two top-tier candidates in the same category operate or are proposed in the same mall, indicating intense brand-level competition.

RULES:
- Ground your analysis STRICTLY in the provided local candidate lists.
- Do NOT output prose. Output ONLY a strict JSON array of objects representing these edges.
- Each edge object in the array must follow this exact format:
  {"source": "T-TenantID", "target": "M-MallID or T-TenantID", "type": "ANCHORS or COMPETES_WITH", "properties": {"reason": "Detailed explanation of why this edge exists based on market share / category metrics."}}
"""

        user_prompt = f"Here is the local Pareto culling statistics payload per mall:\n{json.dumps(mall_payloads, indent=2)}\n\nDeduce the ANCHORS and COMPETES_WITH edges now. Return ONLY JSON."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        cognitive_edges = []
        try:
            response = call_llm(messages, model=model)
            # Extract JSON array
            import re
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                parsed_edges = json.loads(match.group())
                for e in parsed_edges:
                    if isinstance(e, dict) and "source" in e and "target" in e and "type" in e:
                        cognitive_edges.append({
                            "source": e["source"],
                            "target": e["target"],
                            "type": e["type"],
                            "properties": e.get("properties", {"reason": "Cognitive inference"})
                        })
        except Exception as e_llm:
            print(f"[ontology] Cognitive pass failed or returned invalid JSON: {e_llm}. Proceeding with deterministic scaffold.")

        # Append cognitive edges to final list
        edges.extend(cognitive_edges)

        # --- Step 4: Write Graph to Disk ---
        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "compiled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "anchor_relationships": len([e for e in edges if e["type"] == "ANCHORS"]),
                "competitor_relationships": len([e for e in edges if e["type"] == "COMPETES_WITH"])
            }
        }

        output_path = "/home/mahesh/bug-free-pancake/knowledge_graph.json"
        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)

        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        insights = [
            "### MiroFish Knowledge Graph Compiled successfully!",
            f"- **Storage Location**: [knowledge_graph.json](file://{output_path})",
            f"- **Total Nodes**: {len(nodes)} (Malls, Tenants, Categories, Cities, Proposals)",
            f"- **Total Edges**: {len(edges)} (LOCATED_IN, BELONGS_TO, OPERATES_IN, COMPETES_WITH, PROPOSES, PROPOSED_AT)",
            f"- **MiroFish Triggers Deduced**:",
            f"  - **Anchor Relationships (`ANCHORS`)**: {graph_data['metadata']['anchor_relationships']}",
            f"  - **Dynamic Competitor Edges (`COMPETES_WITH`)**: {graph_data['metadata']['competitor_relationships']}",
            "",
            "#### Compiled Anchors & Insights Deduces by Swarm Engine:",
        ]

        for e in cognitive_edges:
            if e["type"] == "ANCHORS":
                source_name = next((n["properties"]["name"] for n in nodes if n["id"] == e["source"]), e["source"])
                target_name = next((n["properties"]["name"] for n in nodes if n["id"] == e["target"]), e["target"])
                insights.append(f"- **Anchor**: **{source_name}** acts as anchor for **{target_name}**. Reason: *{e['properties'].get('reason', '')}*")
            elif e["type"] == "COMPETES_WITH" and e["source"].startswith("T-") and e["target"].startswith("T-"):
                source_name = next((n["properties"]["name"] for n in nodes if n["id"] == e["source"]), e["source"])
                target_name = next((n["properties"]["name"] for n in nodes if n["id"] == e["target"]), e["target"])
                insights.append(f"- **Competition**: direct Category combat between **{source_name}** and **{target_name}** detected. *{e['properties'].get('reason', '')}*")

        meta = {
            'request_id': request_id,
            'duration_ms': duration_ms,
            'model': model,
            'nodes_count': len(nodes),
            'edges_count': len(edges)
        }

        return {'status': 'success', 'insights': insights, 'meta': meta}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f"Ontology Builder failed: {str(e)}",
            'code': 'AGENT_ERROR',
            'meta': {'request_id': request_id, 'details': str(e)}
        }
    finally:
        cur.close()
        conn.close()
