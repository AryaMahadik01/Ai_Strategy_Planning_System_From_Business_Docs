def generate_swot(raw_text):
    """
    Generate basic SWOT analysis from text
    """
    text = raw_text.lower()
    
    # Expanded keywords for better detection
    swot_map = {
        "strengths": ["strong", "experienced", "brand", "leader", "advanced", "expert", "quality", "efficient"],
        "weaknesses": ["weak", "delay", "cost", "lack", "inefficient", "poor", "issue", "problem"],
        "opportunities": ["opportunity", "growth", "expand", "market", "demand", "trend", "potential"],
        "threats": ["risk", "competition", "regulation", "loss", "uncertain", "compliance", "pressure"]
    }

    results = {k: [] for k in swot_map}

    # Context-aware extraction (simple window)
    sentences = text.split('.')
    for sentence in sentences:
        for category, keywords in swot_map.items():
            if any(k in sentence for k in keywords) and len(results[category]) < 4:
                # Clean up the sentence slightly
                clean_sent = sentence.strip().capitalize()
                if 10 < len(clean_sent) < 150: # Avoid noise
                    results[category].append(clean_sent)

    # Fallbacks if nothing found
    if not results["strengths"]: results["strengths"] = ["Operational stability detected"]
    if not results["weaknesses"]: results["weaknesses"] = ["No major internal inefficiencies detected"]
    if not results["opportunities"]: results["opportunities"] = ["Market expansion potential"]
    if not results["threats"]: results["threats"] = ["Standard market competition"]

    return results

def generate_pestle(raw_text):
    """
    Generate PESTLE Analysis
    """
    text = raw_text.lower()
    pestle = {
        "Political": ["government", "regulation", "policy", "tax", "trade"],
        "Economic": ["inflation", "interest", "economy", "budget", "cost"],
        "Social": ["culture", "demographic", "customer", "lifestyle", "trend"],
        "Technological": ["ai", "automation", "digital", "tech", "software"],
        "Legal": ["law", "compliance", "act", "rights", "intellectual"],
        "Environmental": ["green", "sustainability", "carbon", "waste", "climate"]
    }
    
    analysis = {}
    for category, keywords in pestle.items():
        found = False
        for k in keywords:
            if k in text:
                analysis[category] = f"Factors related to {k} detected."
                found = True
                break
        if not found:
            analysis[category] = "No significant factors detected."
            
    return analysis

def generate_porters(raw_text):
    """
    Generate Porter's Five Forces
    """
    return {
        "Competitive Rivalry": "High" if "competit" in raw_text.lower() else "Medium",
        "Supplier Power": "Medium",
        "Buyer Power": "High" if "customer" in raw_text.lower() else "Medium",
        "Threat of Substitutes": "Low",
        "Threat of New Entrants": "Medium"
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