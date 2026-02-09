def generate_swot(raw_text):
    """
    Generate basic SWOT analysis from text
    """
    text = raw_text.lower()

    strengths, weaknesses, opportunities, threats = [], [], [], []

    strength_keywords = ["strong", "experienced", "brand", "leader", "advanced"]
    weakness_keywords = ["weak", "delay", "cost", "lack", "inefficient"]
    opportunity_keywords = ["opportunity", "growth", "expand", "market", "demand"]
    threat_keywords = ["risk", "competition", "regulation", "loss", "uncertain"]

    for w in strength_keywords:
        if w in text:
            strengths.append(f"Strong capability related to {w}")

    for w in weakness_keywords:
        if w in text:
            weaknesses.append(f"Issue related to {w}")

    for w in opportunity_keywords:
        if w in text:
            opportunities.append(f"Opportunity in {w}")

    for w in threat_keywords:
        if w in text:
            threats.append(f"Threat due to {w}")

    if not strengths:
        strengths.append("Stable operational foundation")
    if not weaknesses:
        weaknesses.append("Minor internal inefficiencies")
    if not opportunities:
        opportunities.append("Potential growth opportunity")
    if not threats:
        threats.append("Moderate external risks")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats
    }


def generate_initial_strategy(intents, swot):
    """
    Generate strategies based on intent + SWOT
    """
    strategies = []

    if "growth" in intents:
        strategies.append("Focus on scalable growth initiatives")

    if "cost_reduction" in intents:
        strategies.append("Optimize operational costs")

    if "market_expansion" in intents:
        strategies.append("Expand into new markets")

    if "digital_transformation" in intents:
        strategies.append("Adopt digital tools and automation")

    if "risk_management" in intents:
        strategies.append("Strengthen compliance and risk controls")

    if not strategies:
        strategies.append("Maintain stability and improve efficiency")

    return strategies


def generate_kpis(intents):
    """
    Generate KPIs based on intent
    """
    kpis = []

    if "growth" in intents:
        kpis += ["Revenue Growth Rate", "Customer Acquisition Rate"]

    if "cost_reduction" in intents:
        kpis += ["Operational Cost Ratio", "Cost per Unit"]

    if "market_expansion" in intents:
        kpis += ["Market Penetration", "Regional Sales Growth"]

    if "digital_transformation" in intents:
        kpis += ["Automation Coverage", "System Downtime"]

    if "risk_management" in intents:
        kpis += ["Compliance Score", "Risk Incident Rate"]

    return list(set(kpis)) or ["Overall Business Performance Index"]


def generate_action_plan(strategies):
    """
    Generate action plan
    """
    return [
        {
            "strategy": s,
            "action": f"Implement initiative for {s}",
            "timeline": "3–6 months"
        }
        for s in strategies
    ]


def prioritize_strategies(strategies, swot):
    """
    Assign priority levels
    """
    prioritized = []

    for s in strategies:
        priority = "Medium"

        if "growth" in s.lower() and swot["opportunities"]:
            priority = "High"

        if "risk" in s.lower() and swot["threats"]:
            priority = "High"

        prioritized.append({
            "strategy": s,
            "priority": priority
        })

    return prioritized
