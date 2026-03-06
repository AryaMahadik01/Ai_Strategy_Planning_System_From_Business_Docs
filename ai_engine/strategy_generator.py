import json
from google import genai
from config import Config
import re

# Use the new Client setup
client = genai.Client(api_key=Config.GEMINI_API_KEY)

def generate_full_strategy_profile(raw_text):
    """
    Uses Gemini to analyze the document and return structured JSON for all frameworks.
    """
    text_snippet = raw_text[:30000] 

    prompt = f"""
    You are an expert McKinsey-level corporate strategy consultant. 
    Analyze the following business document and extract key strategic frameworks.
    
    Return ONLY a raw, valid JSON object with the exact following structure. Do not include markdown formatting like ```json.
    {{
        "intents": ["Top 2 business intents (e.g., market_expansion, cost_reduction, digital_transformation, risk_management)"],
        "swot": {{
            "strengths": ["3 key strengths"],
            "weaknesses": ["3 key weaknesses"],
            "opportunities": ["3 key opportunities"],
            "threats": ["3 key threats"]
        }},
        "pestle": {{
            "Political": "1 sentence analysis",
            "Economic": "1 sentence analysis",
            "Social": "1 sentence analysis",
            "Technological": "1 sentence analysis",
            "Legal": "1 sentence analysis",
            "Environmental": "1 sentence analysis"
        }},
        "porters": {{
            "Competitive Rivalry": "High/Medium/Low - short reason",
            "Supplier Power": "High/Medium/Low - short reason",
            "Buyer Power": "High/Medium/Low - short reason",
            "Threat of Substitutes": "High/Medium/Low - short reason",
            "Threat of New Entrants": "High/Medium/Low - short reason"
        }}
    }}

    Document Text:
    {text_snippet}
    """

    try:
        # API call syntax using gemini-2.5-flash-lite
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {
            "intents": ["General Strategy"],
            "swot": {"strengths": ["Stable operations"], "weaknesses": ["Needs optimization"], "opportunities": ["Market growth"], "threats": ["Competition"]},
            "pestle": {}, "porters": {}
        }


def generate_initial_strategy(intents, swot):
    strategies = []
    if "growth" in intents: strategies.append("Focus on scalable growth initiatives")
    if "cost_reduction" in intents: strategies.append("Optimize operational costs")
    if "market_expansion" in intents: strategies.append("Expand into new markets")
    if "digital_transformation" in intents: strategies.append("Adopt digital tools and automation")
    if "risk_management" in intents: strategies.append("Strengthen compliance and risk controls")
    if not strategies: strategies.append("Maintain stability and improve efficiency")
    return strategies

def generate_kpis(intents):
    kpis = []
    if "growth" in intents: kpis += ["Revenue Growth Rate", "Customer Acquisition Rate"]
    if "cost_reduction" in intents: kpis += ["Operational Cost Ratio", "Cost per Unit"]
    if "market_expansion" in intents: kpis += ["Market Penetration", "Regional Sales Growth"]
    if "digital_transformation" in intents: kpis += ["Automation Coverage", "System Downtime"]
    if "risk_management" in intents: kpis += ["Compliance Score", "Risk Incident Rate"]
    return list(set(kpis)) or ["Overall Business Performance Index"]

def generate_action_plan(strategies):
    return [{"strategy": s, "action": f"Implement initiative for {s}", "timeline": "3–6 months"} for s in strategies]

def prioritize_strategies(strategies, swot):
    return [{"strategy": s, "priority": "High" if "growth" in s.lower() else "Medium"} for s in strategies]

def calculate_strategic_scores(swot_data, intents=None):
    if not swot_data or not isinstance(swot_data, dict):
        return {"readiness": 50, "risk": 50, "focus": "General Strategy", "risk_label": "Moderate"}
    
    def get_weight(key):
        val = swot_data.get(key, [])
        if isinstance(val, list): 
            return sum(len(str(item)) for item in val)
        if isinstance(val, str): 
            return len(val)
        return 0

    s_weight = get_weight("strengths")
    w_weight = get_weight("weaknesses")
    o_weight = get_weight("opportunities")
    t_weight = get_weight("threats")
    
    total_weight = s_weight + w_weight + o_weight + t_weight
    
    if total_weight == 0:
        return {"readiness": 50, "risk": 50, "focus": "General Strategy", "risk_label": "Moderate"}

    base_readiness = 35
    readiness_bonus = ((s_weight + o_weight) / total_weight) * 60
    readiness = int(base_readiness + readiness_bonus)
    readiness = max(20, min(95, readiness)) 

    base_risk = 15
    risk_penalty = ((w_weight + t_weight) / total_weight) * 80
    risk = int(base_risk + risk_penalty)
    risk = max(10, min(90, risk)) 

    focus = "Balanced Growth"
    if s_weight > w_weight and o_weight >= t_weight:
        focus = "Aggressive Market Expansion"
    elif w_weight > s_weight:
        focus = "Internal Optimization & Restructuring"
    elif t_weight > o_weight:
        focus = "Defensive Strategy & Risk Mitigation"


    if risk < 35:
        risk_label = "Low"
    elif risk < 65:
        risk_label = "Moderate"
    else:
        risk_label = "Critical"

    return {
        "readiness": readiness,
        "risk": risk,
        "focus": focus,
        "risk_label": risk_label
    }

def simulate_scenario(base_scores, scenario_type):
    """
    Simulate how metrics change based on a strategic focus.
    base_scores: dict containing 'readiness' and 'risk' from the real document.
    """
    simulated = {
        "readiness": base_scores["readiness"],
        "risk": base_scores["risk"],
        "revenue": 50,  
        "cost_efficiency": 50, 
        "stability": 50 
    }

    if scenario_type == "growth":
        # Aggressive Growth: High Revenue, High Risk, Lower Stability
        simulated["focus"] = "Market Expansion"
        simulated["readiness"] += 10
        simulated["risk"] += 20  # Growth adds risk!
        simulated["revenue"] = 85
        simulated["cost_efficiency"] = 40 # Spending money to grow
        simulated["stability"] = 45
        simulated["explanation"] = "Prioritizing growth will maximize revenue potential but significantly increase risk exposure and operational costs due to aggressive expansion."

    elif scenario_type == "cost":
        # Cost Optimization: High Efficiency, Low Risk, Lower Revenue
        simulated["focus"] = "Operational Efficiency"
        simulated["readiness"] -= 5
        simulated["risk"] -= 15  # Safer
        simulated["revenue"] = 45 # Slower growth
        simulated["cost_efficiency"] = 90 # Maximum saving
        simulated["stability"] = 75
        simulated["explanation"] = "Focusing on cost reduction will drastically improve margins and stability, but may slow down market capture and revenue growth."

    elif scenario_type == "risk":
        # Risk Mitigation: Max Stability, Low Risk, Low Revenue
        simulated["focus"] = "Risk Mitigation"
        simulated["readiness"] -= 10
        simulated["risk"] -= 30  # Very safe
        simulated["revenue"] = 40
        simulated["cost_efficiency"] = 60
        simulated["stability"] = 95 # Rock solid
        simulated["explanation"] = "A defensive strategy ensures maximum compliance and stability, protecting the business from external threats at the cost of rapid expansion."

    # Clamp values between 0 and 100 so they look good on charts
    for key in ["readiness", "risk", "revenue", "cost_efficiency", "stability"]:
        simulated[key] = max(5, min(simulated[key], 98))

    # Add labels
    simulated["confidence"] = 85 # AI Confidence remains high for simulations

    return simulated

def generate_performance_metrics(raw_text):
    """
    Real-time API call to generate custom chart data for performance.html
    """
    prompt = f"""
    Analyze this business document and generate highly realistic performance metrics and KPI data specifically tailored to this company's current situation.
    
    Return ONLY a raw, valid JSON object without any markdown formatting. Use this exact structure:
    {{
        "scores": {{"readiness": int(0-100), "maturity": int(0-100), "digital": int(0-100), "risk": int(0-100)}},
        "kpi_labels": ["Custom KPI 1", "Custom KPI 2", "Custom KPI 3", "Custom KPI 4"],
        "kpi_values": [int, int, int, int],
        "growth_trend": [int, int, int, int],
        "risk_trend": [int, int, int, int]
    }}

    Document:
    {raw_text[:20000]}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Performance API Error: {e}")
        # Safe fallback if API fails
        return {
            "scores": {"readiness": 50, "maturity": 50, "digital": 50, "risk": 50},
            "kpi_labels": ["Revenue", "Efficiency", "Market Share", "Stability"],
            "kpi_values": [50, 50, 50, 50],
            "growth_trend": [50, 52, 54, 56], "risk_trend": [50, 48, 46, 44]
        }

def simulate_scenario_llm(raw_text, scenario_type):
    """
    Real-time API call to simulate what happens if a specific strategy is applied.
    """
    prompt = f"""
    You are a strategy consultant. The user wants to apply a '{scenario_type}' strategy to the company described in the document below.
    Predict the outcomes of applying this specific strategy to this specific company.
    
    Return ONLY a raw, valid JSON object without markdown. Use this exact structure:
    {{
        "focus": "A 3-4 word title for this specific strategy",
        "readiness": int(0-100),
        "risk": int(0-100),
        "revenue": int(0-100),
        "cost_efficiency": int(0-100),
        "stability": int(0-100),
        "explanation": "Write 2 highly specific sentences explaining exactly what will happen to THIS company if they focus on {scenario_type}, referencing details from the text."
    }}

    Document:
    {raw_text[:20000]}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Scenario API Error: {e}")
        return {
            "focus": f"{scenario_type.title()} Strategy",
            "readiness": 50, "risk": 50, "revenue": 50, "cost_efficiency": 50, "stability": 50,
            "explanation": "Simulation unavailable at this time."
        }

def generate_execution_roadmap(raw_text):
    """
    Generates a step-by-step execution timeline (What, Why, How) based on the document.
    """
    prompt = f"""
    You are an elite Chief Strategy Officer. Analyze this business document and create a highly actionable, step-by-step execution roadmap.
    Break the strategy down into chronological phases. For each phase, provide specific steps detailing What to do, Why it matters, and How to measure success.

    Return ONLY a raw, valid JSON object without markdown formatting. Use this exact array structure:
    [
        {{
            "phase": "Phase 1: Immediate Action (0-30 Days)",
            "focus": "Core focus of this phase in 3-5 words",
            "steps": [
                {{"what": "Specific action to take", "why": "Strategic justification", "how": "KPI or success metric"}}
            ]
        }},
        {{
            "phase": "Phase 2: Short-Term Execution (Months 1-3)",
            "focus": "...",
            "steps": [...]
        }}
    ]
    Include 3 to 4 phases total.

    Document:
    {raw_text[:20000]}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Roadmap API Error: {e}")
        # Safe fallback
        return [
            {"phase": "Phase 1: Setup", "focus": "System Audit", "steps": [{"what": "Review data", "why": "Establish baseline", "how": "Audit report completion"}]}
        ]

def generate_comparison_points(doc1_filename, doc1_swot, doc2_filename, doc2_swot):
    """
    Real-time API call to compare two strategies and extract 3 bullet points.
    """
    prompt = f"""
    Analyze the following strategic data for two business documents.
    Document 1 ({doc1_filename}): {doc1_swot}
    Document 2 ({doc2_filename}): {doc2_swot}

    Return exactly 3 short, punchy strategic bullet points (max 10 words each) for EACH document, highlighting their core strengths or primary risks.
    
    Output MUST be valid JSON in this exact format, with no other text or markdown:
    {{
        "doc1_points": ["Point 1", "Point 2", "Point 3"],
        "doc2_points": ["Point 1", "Point 2", "Point 3"]
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=prompt
        )
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        
        json_match = re.search(r'\{.*\}', clean_json, re.DOTALL)
        if json_match:
            parsed_json = json.loads(json_match.group(0))
        else:
            parsed_json = json.loads(clean_json)
            
        print("GEMINI SUCCESS! Dynamically loaded the 3 comparison points.")
        return parsed_json
        
    except Exception as e:
        print(f"========== GEMINI API CRASHED IN COMPARE ==========")
        print(f"Error details: {e}")
        print(f"===================================================")
        # Safe fallback
        return {
            "doc1_points": ["Strong market positioning.", "Review initial capital risks.", "Solid competitive advantage."],
            "doc2_points": ["Balanced operational approach.", "Mitigated supply chain risks.", "Steady growth trajectory."]
        }