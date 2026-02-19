import json
from google import genai
from config import Config

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
        # New API call syntax using gemini-2.5-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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



# Keep your existing functions for strategy, kpis, etc. below...
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

def calculate_strategic_scores(swot, intents):
    """
    Calculate quantitative scores based on qualitative SWOT data.
    """
    # 1. Calculate Strategy Readiness Score (0-100)
    # logic: +15 per Strength, +10 per Opportunity, -10 per Weakness, -5 per Threat
    base_score = 50  # Start at neutral
    
    s_count = len(swot.get("strengths", []))
    w_count = len(swot.get("weaknesses", []))
    o_count = len(swot.get("opportunities", []))
    t_count = len(swot.get("threats", []))

    readiness = base_score + (s_count * 10) + (o_count * 5) - (w_count * 5) - (t_count * 2)
    readiness = max(10, min(readiness, 98))  # Clamp between 10 and 98

    # 2. Calculate Risk Exposure Score (0-100)
    # logic: +20 per Threat, +5 per Weakness
    risk_score = (t_count * 15) + (w_count * 5)
    risk_score = max(5, min(risk_score, 95))

    # 3. Determine Risk Label
    if risk_score < 30: risk_label = "Low"
    elif risk_score < 60: risk_label = "Medium"
    else: risk_label = "Critical"

    # 4. Determine Readiness Label
    if readiness > 75: readiness_label = "Strong"
    elif readiness > 50: readiness_label = "Moderate"
    else: readiness_label = "Needs Improvement"

    # 5. Primary Focus (Capitalize first intent)
    focus = intents[0].replace("_", " ").title() if intents else "General Strategy"

    return {
        "readiness": readiness,
        "readiness_label": readiness_label,
        "risk": risk_score,
        "risk_label": risk_label,
        "focus": focus
    }

def simulate_scenario(base_scores, scenario_type):
    """
    Simulate how metrics change based on a strategic focus.
    base_scores: dict containing 'readiness' and 'risk' from the real document.
    """
    # Start with the document's ACTUAL scores
    simulated = {
        "readiness": base_scores["readiness"],
        "risk": base_scores["risk"],
        "revenue": 50,  # Baseline
        "cost_efficiency": 50, # Baseline
        "stability": 50 # Baseline
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
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
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
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Scenario API Error: {e}")
        return {
            "focus": f"{scenario_type.title()} Strategy",
            "readiness": 50, "risk": 50, "revenue": 50, "cost_efficiency": 50, "stability": 50,
            "explanation": "Simulation unavailable at this time."
        }