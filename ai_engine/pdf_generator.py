import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.units import inch

# --- SAFE MODE GRAPHICS IMPORTS ---
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend

# ==========================================
# 1. HELPER: CONTENT EXPANSION
# ==========================================
def expand_text(section_name, content_list):
    if not content_list:
        return [Paragraph("No specific data detected for this section.", get_body_style())]

    intros = {
        "swot": "The following SWOT analysis evaluates the organization's internal strengths and weaknesses against external opportunities and threats.",
        "pestle": "A macro-environmental scan (PESTLE) was conducted to assess external pressures.",
        "roadmap": "Based on the diagnostic findings, the following strategic roadmap outlines high-priority initiatives."
    }

    intro_text = intros.get(section_name, "Analysis of key strategic factors:")
    
    elements = []
    elements.append(Paragraph(intro_text, get_body_style()))
    elements.append(Spacer(1, 10))
    
    for item in content_list:
        text = str(item).replace("•", "").strip()
        p = Paragraph(f"• {text}", get_body_style())
        elements.append(p)
        elements.append(Spacer(1, 6))

    return elements

# ==========================================
# 2. STYLE DEFINITIONS
# ==========================================
def get_header_style():
    return ParagraphStyle(
        'Header', parent=getSampleStyleSheet()['Heading1'],
        fontName='Helvetica-Bold', fontSize=24, leading=28,
        textColor=colors.HexColor('#1e293b'), alignment=TA_CENTER, spaceAfter=30
    )

def get_sub_header_style():
    return ParagraphStyle(
        'SubHeader', parent=getSampleStyleSheet()['Heading2'],
        fontName='Helvetica-Bold', fontSize=16, leading=20,
        textColor=colors.HexColor('#4f46e5'), spaceBefore=20, spaceAfter=10
    )

def get_body_style():
    return ParagraphStyle(
        'Body', parent=getSampleStyleSheet()['Normal'],
        fontName='Helvetica', fontSize=11, leading=16,
        textColor=colors.HexColor('#334155'), alignment=TA_JUSTIFY, spaceAfter=10
    )

# ==========================================
# 3. CHART FUNCTIONS (CENTERED)
# ==========================================
def create_sentiment_pie(sentiment_str):
    """Creates a centered semi-circle gauge."""
    d = Drawing(450, 170)
    pc = Pie()
    pc.x = 140    
    pc.y = 20
    pc.width = 170
    pc.height = 170

    if "Optimistic" in sentiment_str:
        value = 75
        main_color = colors.HexColor('#10b981')
    elif "Cautious" in sentiment_str:
        value = 40
        main_color = colors.HexColor('#f59e0b')
    else:
        value = 50
        main_color = colors.HexColor('#3b82f6')

    pc.data = [value, 100 - value]
    pc.labels = ['', ''] 
    pc.simpleLabels = 0
    pc.sameRadii = 1
    pc.slices.strokeWidth = 1
    pc.slices.strokeColor = colors.white
    pc.slices[0].fillColor = main_color
    pc.slices[1].fillColor = colors.HexColor('#e5e7eb') 

    d.add(pc)

    percent_text = String(225, 95, f"{value}%")
    percent_text.fontSize = 24
    percent_text.fontName = "Helvetica-Bold"
    percent_text.fillColor = colors.HexColor('#1f2937')
    percent_text.textAnchor = "middle"
    d.add(percent_text)

    label_text = String(225, 75, sentiment_str.split('/')[0])
    label_text.fontSize = 12
    label_text.fontName = "Helvetica"
    label_text.fillColor = colors.HexColor('#6b7280')
    label_text.textAnchor = "middle"
    d.add(label_text)

    d.add(Rect(320, 110, 12, 12, fillColor=main_color, strokeColor=None))
    legend_label = String(338, 112, sentiment_str.split('/')[0])
    legend_label.fontSize = 10
    legend_label.fontName = "Helvetica"
    legend_label.fillColor = colors.HexColor('#374151')
    d.add(legend_label)

    return d

def create_swot_bar_chart(swot_data):
    """Creates a centered bar chart."""
    d = Drawing(450, 140)
    s = len(swot_data.get('strengths', []))
    w = len(swot_data.get('weaknesses', []))
    o = len(swot_data.get('opportunities', []))
    t = len(swot_data.get('threats', []))
    
    bc = VerticalBarChart()
    bc.x = 75
    bc.y = 30
    bc.height = 100
    bc.width = 300
    bc.data = [[s, w, o, t]]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(s,w,o,t) + 2
    bc.categoryAxis.categoryNames = ['Strengths', 'Weaknesses', 'Opport.', 'Threats']
    bc.bars[0].fillColor = colors.HexColor('#4f46e5')
    
    d.add(bc)
    return d

# ==========================================
# 4. PAGE TEMPLATE
# ==========================================
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.lightgrey)
    canvas.line(50, 50, A4[0]-50, 50)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.gray)
    page_num = canvas.getPageNumber()
    text = f"StrategixAI Generated Report | Confidential | Page {page_num}"
    canvas.drawCentredString(A4[0]/2, 35, text)
    canvas.restoreState()

# ==========================================
# 5. MAIN GENERATION FUNCTION
# ==========================================
def generate_strategy_pdf(doc, output_path):
    doc_template = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
    )
    Story = []
    h1 = get_header_style()
    h2 = get_sub_header_style()
    body = get_body_style()

    # --- PAGE 1: COVER ---
    Story.append(Spacer(1, 2 * inch))
    Story.append(Paragraph("STRATEGIC ANALYSIS REPORT", h1))
    Story.append(Paragraph(f"Document: {doc.get('filename', 'Unknown')}", ParagraphStyle('Subtitle', parent=body, alignment=TA_CENTER, fontSize=14)))
    Story.append(Spacer(1, 1 * inch))
    
    data = [
        ['Generated By', 'StrategixAI Enterprise Engine'],
        ['Date', datetime.now().strftime("%B %d, %Y")],
        ['Confidentiality', 'Strictly Confidential']
    ]
    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#334155')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    Story.append(t)
    Story.append(PageBreak())

    # --- PAGE 2: EXECUTIVE DASHBOARD ---
    Story.append(Paragraph("1. Executive Summary", h2))
    
    # Written Summary
    summary_content = doc.get('summary', 'No summary available.')
    summary_html = f"<b>AI Executive Abstract:</b><br/><br/>{summary_content}"
    
    t_summary = Table([[Paragraph(summary_html, body)]], colWidths=[440])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 15),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    Story.append(t_summary)
    Story.append(Spacer(1, 20))

    # Visuals
    Story.append(Paragraph("<b>Strategic Indicators</b>", body))
    try:
        Story.append(create_sentiment_pie(doc.get('sentiment', 'Neutral')))
        Story.append(Spacer(1, 0))
        Story.append(create_swot_bar_chart(doc.get('swot', {})))
        Story.append(Spacer(1, 20))
    except Exception as e:
        print(f"Chart Error: {e}")

    # Focus Areas
    Story.append(Paragraph("Strategic Focus Areas:", body))
    focus_data = [['GROWTH', 'EFFICIENCY', 'RISK', 'DIGITAL']]
    t_focus = Table(focus_data, colWidths=[110]*4)
    t_focus.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#4f46e5')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#10b981')),
        ('BACKGROUND', (2,0), (2,0), colors.HexColor('#ef4444')),
        ('BACKGROUND', (3,0), (3,0), colors.HexColor('#f59e0b')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    Story.append(t_focus)
    Story.append(PageBreak())

    # --- PAGE 3: SWOT & PESTLE ---
    Story.append(Paragraph("2. SWOT Analysis", h2))
    Story.extend(expand_text("swot", []))

    swot = doc.get("swot", {})
    def format_list(lst): return "\n\n• ".join(lst[:5]) if lst else "No data."

    swot_data = [
        [Paragraph(f"<b>STRENGTHS</b><br/><br/>• {format_list(swot.get('strengths', []))}", body),
         Paragraph(f"<b>WEAKNESSES</b><br/><br/>• {format_list(swot.get('weaknesses', []))}", body)],
        [Paragraph(f"<b>OPPORTUNITIES</b><br/><br/>• {format_list(swot.get('opportunities', []))}", body),
         Paragraph(f"<b>THREATS</b><br/><br/>• {format_list(swot.get('threats', []))}", body)]
    ]
    t_swot = Table(swot_data, colWidths=[220, 220])
    t_swot.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#eff6ff')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#fff1f2')),
        ('BACKGROUND', (0,1), (0,1), colors.HexColor('#f0fdf4')),
        ('BACKGROUND', (1,1), (1,1), colors.HexColor('#fff7ed')),
        ('PADDING', (0,0), (-1,-1), 15),
    ]))
    Story.append(t_swot)
    Story.append(Spacer(1, 20))
    
    # Pestle
    Story.append(Paragraph("3. Environmental Scan (PESTLE)", h2))
    pestle = doc.get("pestle", {})
    pestle_data = [[k, v] for k, v in pestle.items()] or [["No Data", ""]]
    t_pestle = Table(pestle_data, colWidths=[100, 340])
    t_pestle.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    Story.append(t_pestle)
    Story.append(PageBreak())

    # --- PAGE 4: ROADMAP & RISK ---
    Story.append(Paragraph("4. Strategic Roadmap", h2))
    Story.extend(expand_text("roadmap", []))
    
    strategies = doc.get("prioritized_strategies", []) or [{"strategy": "Review objectives", "priority": "Medium"}]
    strat_data = [["Priority", "Initiative", "Timeline"]]
    for s in strategies[:6]:
        strat_data.append([s.get('priority', 'Medium'), Paragraph(s.get('strategy', ''), body), "3-6 Months"])

    t_strat = Table(strat_data, colWidths=[80, 280, 80])
    t_strat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    Story.append(t_strat)
    
    Story.append(Spacer(1, 30))
    Story.append(Paragraph("5. Critical Risk Management", h2))
    
    risk_data = [["Risk Factor", "Impact Analysis"]]
    for threat in swot.get('threats', [])[:4]:
        risk_data.append([Paragraph(threat, body), "High Impact"])
    if len(risk_data) == 1: risk_data.append(["No critical risks detected.", "Low"])

    t_risk = Table(risk_data, colWidths=[300, 140])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ef4444')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    Story.append(t_risk)

    # --- DISCLAIMER (ADDED AT BOTTOM) ---
    Story.append(Spacer(1, 50))
    disclaimer = "DISCLAIMER: This report was generated by StrategixAI using automated natural language processing. It should be used as a decision-support tool and not as professional financial or legal advice."
    Story.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', parent=body, fontSize=8, textColor=colors.gray)))

    doc_template.build(Story, onFirstPage=add_page_number, onLaterPages=add_page_number)