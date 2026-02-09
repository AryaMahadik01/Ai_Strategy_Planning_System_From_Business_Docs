from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_strategy_pdf(doc, output_path):
    """
    Generate consulting-style strategy PDF
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 40

    def draw_line(text):
        nonlocal y
        c.drawString(40, y, text)
        y -= 18
        if y < 40:
            c.showPage()
            y = height - 40

    draw_line("AI-Powered Strategy Planning Report")
    draw_line("=" * 60)
    draw_line("")

    draw_line(f"Document Name: {doc.get('filename')}")
    draw_line("")

    draw_line("Executive Summary:")
    draw_line(doc.get("summary", "N/A"))
    draw_line("")

    draw_line("Detected Business Intents:")
    for i in doc.get("intents", []):
        draw_line(f"- {i}")

    draw_line("")
    draw_line("SWOT Analysis:")

    swot = doc.get("swot", {})
    for key, values in swot.items():
        draw_line(key.upper())
        for v in values:
            draw_line(f"  - {v}")

    draw_line("")
    draw_line("Recommended Strategies:")
    for s in doc.get("strategies", []):
        draw_line(f"- {s}")

    draw_line("")
    draw_line("Key Performance Indicators (KPIs):")
    for k in doc.get("kpis", []):
        draw_line(f"- {k}")

    c.save()
