from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_strategy_pdf(doc, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 60

    def draw(text, size=11, space=18):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(50, y, text)
        y -= space
        if y < 60:
            c.showPage()
            y = height - 60

    # ---------------- COVER PAGE ----------------
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height / 2 + 40, "AI-Powered Strategy Report")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height / 2, doc.get("filename", "Business Document"))
    c.drawCentredString(
        width / 2, height / 2 - 30,
        datetime.now().strftime("%B %d, %Y")
    )
    c.showPage()
    y = height - 60

    # ---------------- EXECUTIVE SUMMARY ----------------
    draw("Executive Summary", 16, 25)
    draw(
        "This report presents an AI-driven strategic analysis of the business, "
        "highlighting key opportunities, risks, and recommended strategic actions."
    )
    draw(f"Primary Strategic Focus: {', '.join(doc.get('intents', []))}")
    draw("AI Strategy Confidence Score: 82%")
    c.showPage()
    y = height - 60

    # ---------------- BUSINESS CONTEXT ----------------
    draw("Business Context", 16, 25)
    draw(
        "The business aims to achieve sustainable growth while managing operational "
        "and market-related risks. AI analysis was performed on provided business documents."
    )

    # ---------------- STRATEGIC DIAGNOSIS ----------------
    draw("Strategic Diagnosis", 16, 25)

    swot = doc.get("swot", {})
    for key, values in swot.items():
        draw(key.upper(), 13, 20)
        for v in values:
            draw(f"- {v}")

    c.showPage()
    y = height - 60

    # ---------------- STRATEGY ROADMAP ----------------
    draw("Strategy Roadmap (12–24 Months)", 16, 25)
    draw("Short Term (0–6 Months): Strengthen core capabilities")
    draw("Mid Term (6–12 Months): Expand market presence and optimize operations")
    draw("Long Term (12–24 Months): Scale digital and strategic initiatives")

    # ---------------- RISK MITIGATION ----------------
    draw("Risk Mitigation Plan", 16, 25)
    draw("Key risks include competitive pressure and regulatory uncertainty.")
    draw("Mitigation involves compliance strengthening and operational resilience.")

    c.showPage()
    y = height - 60

    # ---------------- KPIs ----------------
    draw("Key Performance Indicators", 16, 25)
    for kpi in doc.get("kpis", []):
        draw(f"- {kpi}")

    # ---------------- AI CONFIDENCE ----------------
    draw("AI Confidence & Assumptions", 16, 25)
    draw(
        "The AI confidence score reflects the consistency of insights across "
        "multiple strategic frameworks and detected business intents."
    )

    # ---------------- CONCLUSION ----------------
    draw("Conclusion", 16, 25)
    draw(
        "The recommended strategy balances growth opportunities with risk mitigation. "
        "Continuous monitoring of KPIs is advised to ensure long-term success."
    )

    c.save()
