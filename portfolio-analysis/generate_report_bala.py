#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Portfolio Analysis Report - Mr. G Bala
Source: ICICI Securities Private Wealth Management statement dated July 24, 2026 (22 pages)
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, HRFlowable)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.legends import Legend

INK      = colors.HexColor("#1a2233")
MAROON   = colors.HexColor("#8a1f2d")
GOLD     = colors.HexColor("#c8922a")
SLATE    = colors.HexColor("#5b6575")
PALE     = colors.HexColor("#f4f1ea")
GREEN    = colors.HexColor("#1e7d4f")
RED      = colors.HexColor("#b03030")
LGREY    = colors.HexColor("#e8e6e1")
BLUE     = colors.HexColor("#2b5d8a")
TEAL     = colors.HexColor("#2a8a80")
PURPLE   = colors.HexColor("#6b4f8a")
ORANGE   = colors.HexColor("#c2652a")
CHART_COLORS = [MAROON, GOLD, BLUE, TEAL, PURPLE, ORANGE, GREEN, SLATE,
                colors.HexColor("#a3454f"), colors.HexColor("#7d9c48"),
                colors.HexColor("#4a7ba6"), colors.HexColor("#9c7448"),
                colors.HexColor("#5f8a6b")]

styles = getSampleStyleSheet()
def st(name, **kw):
    base = kw.pop("base", "Normal")
    styles.add(ParagraphStyle(name, parent=styles[base], **kw))

st("CoverTitle", base="Title", fontName="Helvetica-Bold", fontSize=27, leading=33,
   textColor=INK, alignment=TA_CENTER)
st("CoverSub", fontName="Helvetica", fontSize=13, leading=18, textColor=SLATE,
   alignment=TA_CENTER)
st("H1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=MAROON,
   spaceBefore=6, spaceAfter=6)
st("H2", fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=INK,
   spaceBefore=10, spaceAfter=4)
st("H3", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=MAROON,
   spaceBefore=8, spaceAfter=3)
st("Body", fontName="Helvetica", fontSize=9.3, leading=13.2, textColor=INK,
   alignment=TA_JUSTIFY, spaceAfter=5)
st("Bul", fontName="Helvetica", fontSize=9.3, leading=13.2, textColor=INK,
   leftIndent=12, bulletIndent=2, spaceAfter=3.5, alignment=TA_JUSTIFY)
st("Small", fontName="Helvetica", fontSize=8, leading=10.5, textColor=SLATE)
st("TblCell", fontName="Helvetica", fontSize=7.6, leading=9.4, textColor=INK)
st("TblCellR", fontName="Helvetica", fontSize=7.6, leading=9.4, textColor=INK,
   alignment=TA_RIGHT)
st("TblHead", fontName="Helvetica-Bold", fontSize=7.6, leading=9.2,
   textColor=colors.white)
st("KPInum", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=MAROON,
   alignment=TA_CENTER)
st("KPIlab", fontName="Helvetica", fontSize=7.6, leading=9.5, textColor=SLATE,
   alignment=TA_CENTER)
st("Callout", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK,
   alignment=TA_JUSTIFY)

def inr(v):
    neg = v < 0
    x = abs(v)
    dec = ""
    if x != int(x):
        dec = f"{x - int(x):.2f}"[1:]
    iv = int(x)
    xs = str(iv)
    if len(xs) > 3:
        last3 = xs[-3:]; rest = xs[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:]); rest = rest[:-2]
        if rest: parts.insert(0, rest)
        out = ",".join(parts) + "," + last3
    else:
        out = xs
    out += dec
    return ("(" + out + ")") if neg else out

def rs(v, cr=False, lakh=False):
    neg = v < 0
    if cr:   s = f"{abs(v)/1e7:,.2f} Cr"
    elif lakh: s = f"{abs(v)/1e5:,.2f} L"
    else:    s = inr(abs(v))
    return ("-" if neg else "") + "Rs " + s

def P(txt, style="Body"):
    return Paragraph(txt, styles[style])

def bullets(items):
    return [Paragraph(t, styles["Bul"], bulletText="•") for t in items]

def hr(color=GOLD, width=0.8):
    return HRFlowable(width="100%", thickness=width, color=color,
                      spaceBefore=2, spaceAfter=8)

def kpi_row(kpis, width=170*mm):
    n = len(kpis)
    t = Table([[Paragraph(v, styles["KPInum"]) for v, _ in kpis],
               [Paragraph(l, styles["KPIlab"]) for _, l in kpis]],
              colWidths=[width/n]*n)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PALE),
        ("BOX", (0,0), (-1,-1), 0.8, GOLD),
        ("LINEBEFORE", (1,0), (-1,-1), 0.4, GOLD),
        ("TOPPADDING", (0,0), (-1,0), 8),
        ("BOTTOMPADDING", (0,1), (-1,1), 8),
        ("TOPPADDING", (0,1), (-1,1), 0),
        ("BOTTOMPADDING", (0,0), (-1,0), 1),
    ]))
    return t

def data_table(header, rows, colw, highlight_rows=None, total_rows=None):
    hl = highlight_rows or []
    tot = total_rows or []
    head = [Paragraph(h, styles["TblHead"]) for h in header]
    body = []
    for r in rows:
        line = []
        for j, c in enumerate(r):
            sty = "TblCell" if j == 0 else "TblCellR"
            line.append(Paragraph(str(c), styles[sty]))
        body.append(line)
    t = Table([head] + body, colWidths=colw, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0,0), (-1,0), MAROON),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, PALE]),
        ("GRID", (0,0), (-1,-1), 0.35, LGREY),
        ("BOX", (0,0), (-1,-1), 0.7, SLATE),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 2.5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2.5),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]
    for i in hl:
        cmds.append(("BACKGROUND", (0,i+1), (-1,i+1), colors.HexColor("#f7e8c8")))
    for i in tot:
        cmds.append(("BACKGROUND", (0,i+1), (-1,i+1), colors.HexColor("#ddd8cc")))
        cmds.append(("FONTNAME", (0,i+1), (-1,i+1), "Helvetica-Bold"))
    t.setStyle(TableStyle(cmds))
    return t

def pie_chart(data, labels, width=430, height=150):
    d = Drawing(width, height)
    pie = Pie()
    pie.x = 8; pie.y = 10
    pie.width = 120; pie.height = 120
    pie.data = data
    pie.labels = None
    pie.slices.strokeWidth = 0.6
    pie.slices.strokeColor = colors.white
    for i in range(len(data)):
        pie.slices[i].fillColor = CHART_COLORS[i % len(CHART_COLORS)]
    d.add(pie)
    leg = Legend()
    leg.x = 145; leg.y = height - 30
    leg.alignment = "right"
    leg.fontName = "Helvetica"; leg.fontSize = 7.3
    leg.columnMaximum = 12
    leg.colorNamePairs = [(CHART_COLORS[i % len(CHART_COLORS)], labels[i])
                          for i in range(len(data))]
    d.add(leg)
    return d

def hbar(categories, values, width=470, color=MAROON, fmt="%.1f%%"):
    n = len(values)
    height = n * 15 + 40
    d = Drawing(width, height)
    bc = HorizontalBarChart()
    bc.x = 150; bc.y = 18
    bc.width = width - 200; bc.height = height - 30
    bc.data = [values]
    bc.categoryAxis.categoryNames = categories
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 7
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.valueMin = min(0, min(values)*1.15)
    bc.valueAxis.valueMax = max(values)*1.15 or 1
    bc.bars[0].fillColor = color
    bc.bars.strokeWidth = 0.3
    bc.barLabelFormat = fmt
    bc.barLabels.fontName = "Helvetica"
    bc.barLabels.fontSize = 6.6
    bc.barLabels.boxAnchor = "w"
    bc.barLabels.dx = 3
    d.add(bc)
    return d

def note_box(txt, color=MAROON, bg=colors.HexColor("#fbf3f3"), title=None):
    inner = []
    if title:
        inner.append(Paragraph(f"<b>{title}</b>", styles["Callout"]))
        inner.append(Spacer(1, 3))
    inner.append(Paragraph(txt, styles["Callout"]))
    t = Table([[inner]], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.9, color),
        ("LINEBEFORE", (0,0), (0,-1), 3, color),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    return t

# ================================================================ DATA
# Direct equity: (sector, name, qty(str), cost, mv, gain, gain%, x12, xinc)
EQ = [
 ("Automobile","Tata Motors PAX Vehicles","50",22871,16215,-6656,-29.10,-31.18,-7.20),
 ("Automobile","Hero MotoCorp Ltd","30",83531,155214,71683,85.82,24.98,17.84),
 ("Automobile","TVS Motor Company Ltd","275",169180,1077945,908765,537.16,42.51,44.24),
 ("Automobile","Ola Electric Mobility","1,000",91760,37000,-54760,-59.68,-13.15,-39.90),
 ("Automobile","Tata Motors Ltd","50",10348,20395,10047,97.09,143.28,143.28),
 ("Banks","HDFC Bank Ltd","160",124372,119560,-4812,-3.87,-22.17,-0.57),
 ("Banks","ICICI Bank Ltd","33",31221,47341.80,16120.80,51.63,-2.57,15.24),
 ("Banks","Yes Bank Ltd","7,255",104677.50,166357.15,61679.65,58.92,14.59,12.25),
 ("Banks","Bank of Maharashtra","1,250",49513,98100,48587,98.13,41.36,30.48),
 ("Banks","State Bank of India","35",25239,35441,10202,40.42,26.36,18.07),
 ("Banks","IDFC First Bank","900",42610,71910,29300,68.76,9.62,11.47),
 ("Banks","Bandhan Bank","28",8607,4643.52,-3963.48,-46.05,-9.20,-10.86),
 ("Cement","Ambuja Cements","215",120795,91063.25,-29731.75,-24.61,-31.42,-6.69),
 ("Chemicals & Fertilisers","Paradeep Phosphates","1,500",86250,204465,118215,137.06,-29.09,26.81),
 ("Construction/Real Estate","Kajaria Ceramics","2",2576,2419.20,-156.80,-6.09,3.28,-1.68),
 ("Construction/Real Estate","Brigade Enterprises","33",16000,17384.40,1384.40,8.65,-34.31,3.17),
 ("Construction/Real Estate","DLF Ltd","29",21491,18623.80,-2867.20,-13.34,-21.96,-5.19),
 ("Construction/Real Estate","H G Infra Engineering","17",17598,9212.30,-8385.70,-47.65,-49.60,-23.38),
 ("Engineering/Capital Goods","CG Power & Indl Solutions","100",54993,88380,33387,60.71,30.12,23.98),
 ("Engineering/Capital Goods","Cummins India","3",5284,16797,11513,217.88,59.10,54.98),
 ("ETF","Nippon India ETF Nifty 1D Rate Liquid BeES","19",19000,18999.81,-0.19,-0.001,None,None),
 ("Finance","M&amp;M Financial Services","400",113522,148140,34618,30.49,45.84,12.16),
 ("Finance","PNB Housing Finance","2",1632,2133.60,501.60,30.74,2.07,14.69),
 ("Finance","Indian Railway Fin Corp","250",20425,21757.50,1332.50,6.52,-34.62,4.77),
 ("Other sectors (stmt p.9 - not photographed)","Derived by difference vs grand total","-",77489.50,89480.75,11991.25,15.47,None,None),
 ("Miscellaneous","Sprayking Ltd","2,400",24522,3168,-21354,-87.08,-49.71,-65.08),
 ("Miscellaneous","Greenpanel Industries","17",6083,3286.78,-2796.22,-45.97,-39.11,-21.89),
 ("Miscellaneous","TVS Motor 6% Preference","1,100",0,11440,11440,None,None,None),
 ("Pharma & Healthcare","Cipla Ltd","50",47468,69650,22182,46.73,-5.51,8.78),
 ("Power","Tata Power Co","311",119560,116982.65,-2577.35,-2.16,-5.51,-0.19),
 ("Power","Adani Power Ltd","500",75024.95,106115,31090.05,41.44,81.16,18.33),
 ("Railways","Titagarh Rail Systems","57",59226,46483.50,-12742.50,-21.52,-9.77,-9.55),
 ("Shipping & Logistics","Allcargo Logistics","171",10980.05,1366.29,-9613.76,-87.56,-65.43,-48.24),
 ("Shipping & Logistics","Allcargo Global (ECU)","171",1505,2171.70,666.70,44.30,69.31,69.31),
 ("Steel","Tata Steel Ltd","1,100",95070,202653,107583,113.16,15.18,24.06),
 ("Telecom","Bharti Airtel Ltd","13",14817,25103,10286,69.42,-0.26,25.18),
 ("Tyres","Apollo Tyres Ltd","10",2822,4243.50,1421.50,50.37,-6.29,13.29),
]
EQ_COST = 1778063.00
EQ_MV   = 3171642.50
EQ_GAIN = 1393579.50
EQ_DIV  = 71732.15

# MF: (category, scheme, folio, units, cost, mv, pct, gain, gain%, x12, xinc, plan)
MF = [
 ("ELSS","Axis ELSS Tax Saver-G","910640088 52",26474.04,1414980.00,2526872.70,2.28,1111892.70,78.58,-1.85,10.33,"Reg"),
 ("Flexi Cap","HDFC Flexi Cap Reg-G","12084518/02",1253.73,2399879.27,2516929.17,2.27,117049.90,4.88,1.57,5.84,"Reg"),
 ("Flexi Cap","Sundaram Flexi Cap Reg-G","610167663 1",47497.63,474976.25,671687.66,0.61,196711.41,41.42,-5.52,9.34,"Reg"),
 ("Focused","SBI Focused Equity-G","23139062",15329.56,2524873.79,5962777.28,5.37,3437903.49,136.16,9.88,16.78,"Reg"),
 ("Large & Mid Cap","Sundaram Large & Mid Cap-G","610167663 1",48528.94,2224902.44,4320386.30,3.89,2095483.86,94.18,4.30,15.02,"Reg"),
 ("Large & Mid Cap","Kotak Large & Midcap Reg-G","7370207",2885.28,699965.07,1008631.90,0.91,308666.83,44.10,1.41,13.91,"Reg"),
 ("Large Cap","ICICI Pru Large Cap-G","14870215/43",7429.05,799960.00,798399.90,0.72,-1560.10,-0.20,-2.39,-0.10,"Reg"),
 ("Large Cap","Mirae Asset Large Cap Reg-G","799206566 95",79640.89,4824910.53,8801512.41,7.93,3976601.87,82.42,-2.50,11.22,"Reg"),
 ("Large Cap","Canara Robeco Large Cap Reg-G","177277917 13",47029.38,1824908.75,2861267.72,2.58,1036358.97,56.79,-4.01,10.32,"Reg"),
 ("Large Cap","Axis Large Cap Reg-G","910640088 52",61409.45,2699865.04,3632983.30,3.27,933118.26,34.56,-2.70,7.34,"Reg"),
 ("Mid Cap","PGIM India Midcap Reg-G","910159533 01",10996.29,488565.25,712449.76,0.64,223884.51,45.82,-1.52,10.43,"Reg"),
 ("Multi Cap","Kotak Multicap Reg-G","7370207",377590.89,7008239.49,7464971.95,6.73,456732.46,6.52,0.96,5.66,"Reg"),
 ("Sectoral-Banking","ICICI Pru Banking & Fin Services-G","14870215/43",12721.96,949964.98,1652200.30,1.49,702235.32,73.92,-4.01,11.74,"Reg"),
 ("Sectoral-Banking","Nippon India Banking & Fin Services-G","477271608 212",1172.81,754962.62,746161.89,0.67,-8800.73,-1.17,-1.45,-1.45,"Reg"),
 ("Sectoral-Banking","DSP Banking & Fin Services Reg-G","6193656/61",99540.89,1299935.00,1454989.16,1.31,155054.16,11.93,10.33,15.63,"Reg"),
 ("Small Cap","Nippon India Small Cap-G","477271608 212",4390.97,399980.04,778090.86,0.70,378110.82,94.53,2.13,19.21,"Reg"),
 ("Thematic-Business Cycle","ICICI Pru Business Cycle-G","14870215/43",60149.04,1499924.99,1471847.08,1.33,-28077.90,-1.87,-2.19,-2.19,"Reg"),
 ("Thematic-Infrastructure","Tata Infrastructure Reg-G","7788728/49",8317.55,1199939.98,1508790.81,1.36,308850.83,25.74,3.77,13.60,"Reg"),
 ("Thematic-Manufacturing","ICICI Pru Manufacturing-G","14870215/43",195449.59,5887928.81,7520900.34,6.78,1632971.53,27.73,8.91,12.24,"Reg"),
 ("Dynamic Asset Alloc","HDFC Balanced Advantage Reg-G","12084518/02",57007.76,19331215.82,29502883.99,26.59,10171668.16,52.62,-0.91,16.96,"Reg"),
 ("Dynamic Asset Alloc","ICICI Pru Balanced Advantage-G","14870215/43",42459.65,2999849.95,3293595.36,2.97,293745.41,9.79,4.92,5.48,"Reg"),
 ("Dynamic Asset Alloc","Tata Balanced Advantage Reg-G","7788728/49",49873.81,999950.00,1047045.84,0.94,47095.84,4.71,2.09,2.41,"Reg"),
 ("Multi Asset","Nippon India Multi Asset Alloc Reg-G","477271608 212",44079.12,999949.98,1083367.84,0.98,83417.86,8.34,10.31,10.31,"Reg"),
 ("Multi Asset","ICICI Pru Multi Asset-G","14870215/43",8506.41,5999699.89,6832225.41,6.16,832525.51,13.88,5.78,7.39,"Reg"),
 ("Multi Asset","SBI Multi Asset Allocation-G","23139062",73486.31,4602513.73,4867182.03,4.39,264668.29,5.75,7.88,7.88,"Reg"),
 ("Multi Asset","Quant Multi Asset Alloc Direct-G","510102231 523",7846.42,1399930.06,1443397.19,1.30,43467.13,3.10,20.33,20.33,"Dir"),
 ("Multi Asset","HDFC Multi-Asset Active FoF Reg-G","12084518/02",335616.15,5098715.13,6479741.07,5.84,1381025.93,27.09,5.40,11.55,"Reg"),
]
MFE_COST, MFE_MV = 39378662.31, 56411850.49
MFB_COST, MFB_MV = 41431824.58, 54549438.72
MF_COST,  MF_MV  = 80810486.89, 110961289.21
MF_GAIN = 30150802.32
SGB_COST, SGB_MV = 116831.00, 277116.90
AIF_MV = 8000080.00
ISEC_TOT = 114410048.62
GRAND = ISEC_TOT + AIF_MV     # 122,410,128.62

OUT = "/tmp/claude-0/-home-user-rstate/8e5eba92-2688-5f8a-ad4f-1b7c48e108f9/scratchpad/Portfolio_Analysis_G_Bala_Jul2026.pdf"

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(SLATE)
    canvas.drawString(20*mm, 11*mm,
        "Comprehensive Portfolio Analysis - Mr. G Bala  |  Data as on July 24, 2026  |  Source: ICICI Securities PWM statement")
    canvas.drawRightString(190*mm, 11*mm, f"Page {doc.page}")
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(0.6)
    canvas.line(20*mm, 14*mm, 190*mm, 14*mm)
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=20*mm, rightMargin=20*mm,
                        topMargin=16*mm, bottomMargin=18*mm,
                        title="Comprehensive Portfolio Analysis - G Bala",
                        author="Portfolio Analysis")
S = []

# ============================================================ COVER
S.append(Spacer(1, 34*mm))
S.append(Paragraph("COMPREHENSIVE<br/>PORTFOLIO ANALYSIS", styles["CoverTitle"]))
S.append(Spacer(1, 6*mm))
S.append(HRFlowable(width="45%", thickness=1.2, color=GOLD, hAlign="CENTER"))
S.append(Spacer(1, 6*mm))
S.append(Paragraph("Mr. G Bala", ParagraphStyle("cn", parent=styles["CoverSub"],
        fontSize=17, textColor=MAROON, fontName="Helvetica-Bold", leading=22)))
S.append(Spacer(1, 3*mm))
S.append(Paragraph("ICICI Securities Private Wealth Management Account", styles["CoverSub"]))
S.append(Paragraph("Holdings as on July 24, 2026  (Demat 'other holdings' as on June 30, 2026)", styles["CoverSub"]))
S.append(Spacer(1, 14*mm))
S.append(kpi_row([
    (rs(GRAND, cr=True), "TOTAL WEALTH ANALYSED"),
    (rs(MF_MV, cr=True), "MUTUAL FUNDS (97%)"),
    (rs(EQ_MV, lakh=True), "DIRECT EQUITY"),
    (rs(AIF_MV, lakh=True), "AIF (DEMAT BALANCE)"),
]))
S.append(Spacer(1, 10*mm))
S.append(note_box(
    "This report was prepared from photographs of 16 of the statement's 22 pages. All mutual-fund lines "
    "and equity sector totals were re-computed and tie exactly to the statement's own totals; the only "
    "gap is statement page 9 (small equity sectors worth Rs 89,481 market value, shown as a derived line), "
    "plus pages 13/19/22 which appear to carry headers, insurance or disclaimer content. This is an "
    "independent analytical exercise for education and discussion with your advisor - not investment "
    "advice. ISEC PMS 'Ace Equity Advisory' assets are excluded from the source statement.",
    title="Scope & Disclaimer"))
S.append(PageBreak())

# ============================================================ 1. EXEC SUMMARY
S.append(Paragraph("1. Executive Summary", styles["H1"]))
S.append(hr())
S.append(P(
    f"The statement covers <b>{rs(ISEC_TOT, cr=True)}</b> on the ICICI Securities books - "
    f"{rs(MF_MV, cr=True)} of mutual funds (96.99%), {rs(EQ_MV, lakh=True)} of direct stocks (2.77%) and "
    f"{rs(SGB_MV, lakh=True)} of Sovereign Gold Bonds (0.24%, listed by the platform under NCDs). Adding the "
    f"{rs(AIF_MV, lakh=True)} Sundaram Category II AIF sitting in the demat account, total wealth analysed is "
    f"<b>{rs(GRAND, cr=True)} (~Rs 12.24 crore)</b>."))
S.append(P(
    "This is a <b>fund-first portfolio</b>: professionally managed, genuinely diversified across market caps "
    "and styles, with an even 51:49 split between pure-equity funds and hybrid (balanced-advantage / "
    "multi-asset) funds. There is no single-stock risk of any consequence - the entire direct-equity book is "
    "2.8% of wealth. The portfolio's issues are of the opposite kind: <b>redundancy, cost and clutter</b> "
    "rather than concentration."))
S.append(Spacer(1, 2))
S.append(note_box(
    f"<b>The MF engine works: {rs(MF_COST, cr=True)} invested has grown to {rs(MF_MV, cr=True)} "
    f"(+37.3%), XIRR 12.74% since inception.</b> But it is spread across 27 scheme-lines from 13 different "
    "AMCs - including 4 large-cap funds, 3 banking-sector funds and 5 multi-asset funds - and 26 of 27 lines "
    "are Regular plans. The same result is achievable with 8-10 schemes at roughly Rs 7-11 lakh per year "
    "less in embedded distributor commissions.", title="KEY FINDING - Over-diversification with a fee drag"))
S.append(Spacer(1, 4))
S.append(Paragraph("Headline scorecard", styles["H2"]))
rows = [
 ["Mutual funds (27 lines, 13 AMCs)", inr(MF_COST), inr(MF_MV), inr(MF_GAIN), "+37.3%", "XIRR 12.74% incep., 1.81% last 12m"],
 ["  - equity schemes (19)", inr(MFE_COST), inr(MFE_MV), inr(17033188.17), "+43.3%", "XIRR 11.62% incep."],
 ["  - hybrid schemes (8)", inr(MFB_COST), inr(MFB_MV), inr(13117614.15), "+31.7%", "XIRR 14.43% incep."],
 ["Direct equity (~40 stocks)", inr(EQ_COST), inr(EQ_MV), inr(EQ_GAIN), "+78.4%", "XIRR 19.75% incep.; TVS Motor is 34% of it"],
 ["Sovereign Gold Bond 2.50% Dec-31", inr(SGB_COST), inr(SGB_MV), inr(160285.90), "+137.2%", "Tax-free if held to maturity"],
 ["Sundaram Cat-II AIF (demat bal.)", "n/a", inr(AIF_MV), "n/a", "-", "80 units; valuation opaque - verify"],
 ["Total analysed", "", inr(GRAND), "", "", ""],
]
S.append(data_table(
    ["Block", "Cost (Rs)", "Market Value (Rs)", "Unrealised P&amp;L (Rs)", "Return", "Comment"],
    rows, [40*mm, 25*mm, 27*mm, 25*mm, 13*mm, 40*mm],
    total_rows=[6], highlight_rows=[0]))
S.append(Spacer(1, 5))
S.append(Paragraph("Top 5 findings", styles["H2"]))
S.extend(bullets([
 "<b>Sound architecture, too many parts:</b> 27 MF lines across 13 AMCs; heavy overlap (4 large-cap + 1 multicap + 2 flexi-cap + 1 focused fund all fish in the same large-cap pond; 3 separate banking-sector funds hold the same few banks).",
 "<b>HDFC Balanced Advantage alone is Rs 2.95 Cr - 26.6% of the MF book</b> and ~24% of total wealth. It has earned its place (16.96% XIRR), but one scheme carrying a quarter of family wealth deserves a deliberate cap.",
 "<b>Fee drag:</b> ~Rs 10.95 Cr sits in Regular plans (all but Quant Multi Asset). At a 0.6-1.0% p.a. commission differential, that is roughly <b>Rs 6.6-11 lakh every year</b> - the single largest recoverable cost in this portfolio.",
 "<b>The trailing year was flat:</b> MF 12-month XIRR is just 1.81% (equity sleeve 1.67%, hybrids 1.96%), and most large-cap funds printed negative 12-month XIRRs. Nothing broken - but it sharpens the case for cutting costs and clutter.",
 "<b>Two blind spots:</b> the Rs 80 lakh AIF is carried at demat balance (Rs 100,001/unit), which 'may not reflect current value' per the statement - obtain the fund's NAV statement; and PMS Ace Equity Advisory assets are excluded from this report entirely.",
]))
S.append(PageBreak())

# ============================================================ 2. ALLOCATION
S.append(Paragraph("2. Asset Allocation & Structure", styles["H1"]))
S.append(hr())
S.append(P(
    "The statement's asset-class table shows Equity 99.76% / Fixed Income 0.24%. On a look-through basis the "
    "picture is more moderate: the eight hybrid schemes (49% of the MF book) internally hold roughly 30-45% "
    "in debt and arbitrage, and the multi-asset funds add gold. True economic equity exposure is roughly "
    "70-75% of the ISEC book - a genuinely balanced construction, unusual and commendable for a portfolio "
    "this size."))
alloc_rows = [
 ["MF - pure equity schemes (19)", inr(MFE_MV), f"{MFE_MV/GRAND*100:.1f}%"],
 ["MF - hybrid schemes (8: BAF + multi-asset)", inr(MFB_MV), f"{MFB_MV/GRAND*100:.1f}%"],
 ["Direct stocks (~40 positions)", inr(EQ_MV), f"{EQ_MV/GRAND*100:.1f}%"],
 ["Sovereign Gold Bond (2.50% Dec 2031)", inr(SGB_MV), f"{SGB_MV/GRAND*100:.2f}%"],
 ["Sundaram Category II AIF", inr(AIF_MV), f"{AIF_MV/GRAND*100:.1f}%"],
 ["Total", inr(GRAND), "100.0%"],
]
S.append(data_table(["Component", "Value (Rs)", "% of total wealth"],
                    alloc_rows, [75*mm, 48*mm, 47*mm], total_rows=[5]))
S.append(Spacer(1, 6))
S.append(pie_chart(
    [MFE_MV, MFB_MV, EQ_MV, SGB_MV, AIF_MV],
    ["Equity mutual funds 46.1%", "Hybrid mutual funds 44.6%",
     "Direct stocks 2.6%", "Sovereign Gold Bond 0.2%", "AIF 6.5%"]))
S.append(Spacer(1, 4))
S.append(Paragraph("What this allocation implies", styles["H2"]))
S.extend(bullets([
 "<b>Drawdown resilience is real.</b> In a -25% equity market with hybrids falling ~12%, this portfolio loses roughly 17-18% versus ~24% for an all-equity book - the hybrid half is doing its job.",
 "<b>Liquidity is good except the AIF.</b> Funds and stocks are T+2/T+3 liquid; the Rs 80 L Category II AIF is locked to the fund's tenure and exit terms - treat it as illiquid until the fund documents say otherwise.",
 "<b>Gold exposure exists twice:</b> directly via the SGB (0.24%) and indirectly inside the five multi-asset funds (which together hold Rs 2.07 Cr, typically 10-25% in gold) - aggregate gold is likely ~2-4% of wealth.",
 "<b>No emergency/debt bucket on this statement:</b> apart from hybrid-internal debt there are no liquid, arbitrage or short-duration funds. A 12-24 month expense reserve in liquid instruments is still worth carving out.",
]))
S.append(PageBreak())

# ============================================================ 3. EQUITY
S.append(Paragraph("3. Direct Equity - Deep Dive (~40 holdings, 2.8% of wealth)", styles["H1"]))
S.append(hr())
S.append(P(
    f"Cost {rs(EQ_COST, lakh=True)} → market value {rs(EQ_MV, lakh=True)} (+78.4%), dividends received "
    f"{rs(EQ_DIV)}, XIRR since inception 19.75% - on paper an excellent record. In substance it is "
    f"<b>one real position plus a long tail</b>: TVS Motor (275 shares, up 537%, worth {rs(1077945, lakh=True)}) "
    "is 34% of the equity book by itself, the TVS 6% preference shares another Rs 11,440, and the remaining "
    "~38 positions average under Rs 60,000 each."))
S.append(Paragraph("3.1 Complete holdings register", styles["H2"]))
hdr = ["Sector / Stock", "Qty", "Cost (Rs)", "Mkt Value (Rs)", "P&amp;L (Rs)", "P&amp;L %", "XIRR 12m", "XIRR Incep."]
rows = []
cur = None
for sec, nm, q, c, m, g, gp, x12, xin in EQ:
    if sec != cur:
        rows.append([f"<b>{sec}</b>", "", "", "", "", "", "", ""])
        cur = sec
    rows.append([nm, q, inr(c), inr(m), inr(g),
                 ("-" if gp is None else f"{gp:+.1f}%"),
                 ("-" if x12 is None else f"{x12:+.1f}%"),
                 ("-" if xin is None else f"{xin:+.1f}%")])
rows.append(["<b>GRAND TOTAL</b>", "", inr(EQ_COST), inr(EQ_MV), inr(EQ_GAIN), "+78.4%", "+13.5%", "+19.8%"])
S.append(data_table(hdr, rows,
        [46*mm, 11*mm, 22*mm, 23*mm, 21*mm, 13*mm, 17*mm, 17*mm],
        total_rows=[len(rows)-1]))
S.append(Spacer(1, 3))
S.append(P("<i>The TVS 6% preference shares (1,100 units, zero cost shown) came from TVS Motor's bonus "
           "preference-share issue - the Rs 11,440 gain is booked as short-term. The 'Other sectors' line "
           "reconstructs statement page 9, which was not photographed, from the difference between the "
           "photographed sector sub-totals and the printed grand total.</i>", "Small"))
S.append(PageBreak())

S.append(Paragraph("3.2 Winners, losers and hygiene", styles["H1"]))
S.append(hr())
S.append(Paragraph("Standout winners", styles["H3"]))
win = [
 ["TVS Motor Company", "+537%", inr(908765), "+44.2%", "The book's engine; also echoed by TVS pref shares"],
 ["Cummins India", "+218%", inr(11513), "+55.0%", "3 shares - great % on a token position"],
 ["Paradeep Phosphates", "+137%", inr(118215), "+26.8%", "2nd biggest rupee winner"],
 ["Tata Steel", "+113%", inr(107583), "+24.1%", "6.4% of equity book"],
 ["Bank of Maharashtra", "+98%", inr(48587), "+30.5%", "PSU bank re-rating"],
 ["Tata Motors", "+97%", inr(10047), "+143.3%*", "*young position, XIRR exaggerated"],
 ["Hero MotoCorp", "+86%", inr(71683), "+17.8%", "Solid two-wheeler compounder"],
]
S.append(data_table(["Stock", "Abs. gain", "Gain (Rs)", "XIRR incep.", "Read"],
        win, [38*mm, 17*mm, 22*mm, 19*mm, 74*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Broken positions (candidates for exit / tax-loss harvest)", styles["H3"]))
los = [
 ["Allcargo Logistics", "-87.6%", inr(-9613.76), "Thesis long gone; harvest the loss"],
 ["Sprayking Ltd", "-87.1%", inr(-21354), "Micro-cap punt failed; exit"],
 ["Ola Electric Mobility", "-59.7%", inr(-54760), "Biggest rupee loss; conviction check overdue"],
 ["H G Infra Engineering", "-47.7%", inr(-8385.70), "17 shares - noise"],
 ["Bandhan Bank", "-46.1%", inr(-3963.48), "28 shares - noise"],
 ["Greenpanel Industries", "-46.0%", inr(-2796.22), "17 shares - noise"],
 ["Ambuja Cements", "-24.6%", inr(-29731.75), "2nd biggest rupee loss"],
 ["Titagarh Rail", "-21.5%", inr(-12742.50), "Railway theme cooled"],
]
S.append(data_table(["Stock", "Loss %", "Loss (Rs)", "Read"],
        los, [38*mm, 16*mm, 22*mm, 94*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Hygiene observations", styles["H2"]))
S.extend(bullets([
 "Roughly Rs 1.3 lakh of harvestable losses sit in the tail (Ola, Ambuja, Sprayking, Titagarh, Allcargo, HG Infra, Greenpanel, Bandhan, DLF, Tata Power, Kajaria) - useful against the Rs 42K short-term and future gains.",
 "Sub-Rs-10,000 positions (Kajaria 2 sh, Cummins 3 sh, PNB Housing 2 sh, Apollo 10 sh, Airtel 13 sh, HG Infra 17 sh, Greenpanel 17 sh, Bandhan 28 sh...) exist mainly as statement clutter - fold the tail into the MF book.",
 "The one strategic question: TVS Motor. At 34% of the equity book but only 0.9% of wealth it is not a risk problem - it is a 'let the winner run vs trim' judgement call. A stop-discipline or partial trim into the next auto up-cycle would be reasonable.",
 "The Nifty 1D Rate Liquid BeES ETF (Rs 19,000) is the only cash-like instrument in the entire portfolio - symbolically the right idea, 1000x too small.",
]))
S.append(PageBreak())

# ============================================================ 4. MF DEEP DIVE
S.append(Paragraph("4. Mutual Funds - Deep Dive (27 lines, 13 AMCs)", styles["H1"]))
S.append(hr())
S.append(P(
    f"Cost {rs(MF_COST, cr=True)} → value {rs(MF_MV, cr=True)}, unrealised gain {rs(MF_GAIN, cr=True)} "
    "(+37.3%). Since-inception XIRR 12.74% - a solid outcome, notably driven by the hybrid sleeve "
    "(14.43% XIRR) outperforming the pure-equity sleeve (11.62%) on a money-weighted basis, thanks to "
    "well-timed large deployments into HDFC Balanced Advantage. Trailing 12-month XIRR is 1.81% - a flat "
    "year across the board."))
S.append(Paragraph("4.1 Complete scheme register", styles["H2"]))
hdr = ["Category / Scheme (Folio)", "Units", "Cost (Rs)", "Value (Rs)", "P&amp;L %", "XIRR 12m", "XIRR Inc.", "Plan"]
rows = []
cur = None
for cat, nm, fol, u, c, m, pct, g, gp, x12, xin, plan in MF:
    if cat != cur:
        rows.append([f"<b>{cat}</b>", "", "", "", "", "", "", ""])
        cur = cat
    rows.append([f"{nm}<br/><font size=6 color='#5b6575'>{fol}</font>", f"{u:,.0f}",
                 inr(c), inr(m), f"{gp:+.1f}%", f"{x12:+.1f}%", f"{xin:+.1f}%", plan])
rows.append(["<b>Equity schemes sub-total (19)</b>", "", inr(MFE_COST), inr(MFE_MV), "+43.3%", "+1.67%", "+11.62%", ""])
rows.append(["<b>Hybrid schemes sub-total (8)</b>", "", inr(MFB_COST), inr(MFB_MV), "+31.7%", "+1.96%", "+14.43%", ""])
rows.append(["<b>GRAND TOTAL</b>", "", inr(MF_COST), inr(MF_MV), "+37.3%", "+1.81%", "+12.74%", ""])
S.append(data_table(hdr, rows,
        [52*mm, 14*mm, 24*mm, 24*mm, 14*mm, 14*mm, 14*mm, 12*mm],
        total_rows=[len(rows)-3, len(rows)-2, len(rows)-1]))
S.append(PageBreak())

S.append(Paragraph("4.2 Category & AMC structure", styles["H1"]))
S.append(hr())
cat_rows = [
 ["Dynamic Asset Allocation (BAF)", inr(33843525.19), "30.5%", "HDFC (Rs 2.95 Cr!) + ICICI + Tata"],
 ["Multi Asset (5 schemes)", inr(20705913.54), "18.7%", "ICICI, SBI, HDFC FoF, Quant, Nippon"],
 ["Large Cap (4 schemes)", inr(16094163.33), "14.5%", "Mirae biggest; ICICI Pru LC flat since buy"],
 ["Thematic (3: Mfg/Infra/Bus-Cycle)", inr(10501538.23), "9.5%", "ICICI Mfg Rs 75 L is the anchor"],
 ["Multi Cap", inr(7464971.95), "6.7%", "Kotak - weak 5.66% XIRR"],
 ["Focused", inr(5962777.28), "5.4%", "SBI Focused - the best performer (+136%)"],
 ["Large & Mid Cap (2)", inr(5329018.20), "4.8%", "Sundaram + Kotak"],
 ["Sectoral - Banking (3 schemes)", inr(3853351.35), "3.5%", "Triple bet on one sector"],
 ["Flexi Cap (2)", inr(3188616.83), "2.9%", "HDFC + Sundaram"],
 ["ELSS", inr(2526872.70), "2.3%", "Axis - lock-in likely over"],
 ["Small Cap", inr(778090.86), "0.7%", "Nippon (+94.5%)"],
 ["Mid Cap", inr(712449.76), "0.6%", "PGIM"],
]
S.append(data_table(["Category", "Value (Rs)", "% of MF", "Schemes"],
        cat_rows, [46*mm, 30*mm, 18*mm, 76*mm]))
S.append(Spacer(1, 6))
amc = [("HDFC", 38499554.23), ("ICICI Prudential", 21569168.39),
       ("SBI", 10829959.31), ("Mirae Asset", 8801512.41),
       ("Kotak", 8473603.85), ("Axis", 6159856.00),
       ("Sundaram", 4992073.96), ("Canara Robeco", 2861267.72),
       ("Nippon India", 2607620.59), ("Tata", 2555836.65),
       ("DSP", 1454989.16), ("Quant", 1443397.19), ("PGIM", 712449.76)]
S.append(Paragraph("AMC spread (13 houses)", styles["H2"]))
S.append(hbar([a for a, _ in amc], [v/MF_MV*100 for _, v in amc], color=GOLD))
S.append(Spacer(1, 4))
S.extend(bullets([
 "<b>Redundancy map:</b> 4 large-cap funds + 1 multicap + 2 flexi-caps + 1 focused fund = 8 schemes chasing broadly the same universe (Rs 3.27 Cr). 3 banking-sector funds duplicate what every diversified fund already holds. 5 multi-asset funds (Rs 2.07 Cr) do the same job as one or two.",
 "<b>Scheme-level concentration is the one real position risk:</b> HDFC BAF at 26.6% of the MF book. A single-scheme cap of ~15% (rebalance the excess into a second BAF or short-duration debt) is the textbook fix.",
 "<b>13 AMCs is diversification theatre:</b> beyond 4-6 houses, extra AMCs add paperwork, not safety. Candidates to exit on performance + redundancy: ICICI Pru Large Cap (flat), Nippon Banking (negative), ICICI Business Cycle (negative), Kotak Multicap (5.7% XIRR), HDFC Flexi Cap (5.8% XIRR), Axis Large Cap (7.3%).",
 "<b>All-growth plans, clean tax hygiene</b> - no dividend leakage anywhere. Good.",
]))
S.append(PageBreak())

S.append(Paragraph("4.3 Scheme-level performance read", styles["H1"]))
S.append(hr())
S.append(Paragraph("Best compounders (XIRR since inception)", styles["H3"]))
best = [
 ["Quant Multi Asset (Direct)", "+20.3%", "Young but strong; the only Direct plan in the book"],
 ["Nippon India Small Cap", "+19.2%", "+94.5% absolute; small position deserves more weight"],
 ["HDFC Balanced Advantage", "+17.0%", "Rs 2.95 Cr anchor; the portfolio's best big decision"],
 ["SBI Focused Equity", "+16.8%", "+136% absolute - best pure-equity scheme here"],
 ["DSP Banking & Fin Services", "+15.6%", "The one banking fund that is working"],
 ["Sundaram Large & Mid Cap", "+15.0%", "+94% absolute on Rs 22.2 L cost"],
 ["Kotak Large & Midcap", "+13.9%", "Consistent"],
 ["Tata Infrastructure", "+13.6%", "Cyclical theme, currently ahead"],
]
S.append(data_table(["Scheme", "XIRR incep.", "Read"], best, [52*mm, 20*mm, 98*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Laggards / attention list", styles["H3"]))
lag = [
 ["ICICI Pru Business Cycle", "-2.2%", "Negative since purchase; thematic without conviction"],
 ["Nippon Banking & Fin Services", "-1.5%", "Negative; redundant with DSP Banking"],
 ["ICICI Pru Large Cap", "-0.1%", "Flat since buy; merge into Mirae"],
 ["Tata Balanced Advantage", "+2.4%", "Young and modest; consolidate into main BAFs"],
 ["ICICI Pru Balanced Advantage", "+5.5%", "Far behind HDFC BAF twin"],
 ["Kotak Multicap", "+5.7%", "Rs 74.6 L at a mediocre run-rate - biggest underperforming rupee block"],
 ["HDFC Flexi Cap", "+5.8%", "Bought near highs (ST gains present)"],
 ["Axis Large Cap", "+7.3%", "Chronic Axis equity underperformance"],
 ["SBI Multi Asset", "+7.9%", "OK, but 5 multi-asset funds is 3 too many"],
]
S.append(data_table(["Scheme", "XIRR incep.", "Read"], lag, [52*mm, 20*mm, 98*mm]))
S.append(Spacer(1, 5))
S.append(P(
    "Money-weighted nuance: most equity schemes show negative 12-month XIRR (-1.5% to -5.5%) while the "
    "since-inception numbers remain healthy - the last year was flat-to-down for Indian large caps, and "
    "nothing in the register suggests scheme-specific breakdowns beyond the laggards flagged above."))
S.append(PageBreak())

# ============================================================ 5. SGB / AIF / GAPS
S.append(Paragraph("5. Gold Bond, AIF & Other Items", styles["H1"]))
S.append(hr())
S.append(Paragraph("5.1 Sovereign Gold Bond 2.50% - 28 Dec 2031", styles["H2"]))
sgb = [
 ["Units / cost", "19 units at Rs 6,149 avg = " + rs(SGB_COST)],
 ["Market value", rs(SGB_MV) + "  (Rs 14,585.10/unit, +137.2%)"],
 ["Coupon", "2.50% p.a. on issue price, paid half-yearly, taxed at slab"],
 ["Maturity", "28 Dec 2031 - redemption via RBI is CAPITAL-GAINS TAX FREE for individuals"],
 ["XIRR", "43.07% last 12m / 40.35% since inception (gold rally)"],
 ["Note", "The platform lists it under 'Non-Convertible Debentures' - it is a sovereign gold bond, not corporate credit"],
]
t = Table([[Paragraph(f"<b>{a}</b>", styles["TblCell"]), Paragraph(b, styles["TblCell"])] for a, b in sgb],
          colWidths=[38*mm, 132*mm])
t.setStyle(TableStyle([
    ("GRID", (0,0), (-1,-1), 0.35, LGREY),
    ("BACKGROUND", (0,0), (0,-1), PALE),
    ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
]))
S.append(t)
S.append(Spacer(1, 3))
S.append(P("<b>Recommendation: hold to maturity.</b> Selling on-exchange before Dec 2031 forfeits the "
           "capital-gains exemption and SGB secondary-market liquidity is poor. This is the portfolio's "
           "best tax-structured asset."))
S.append(Spacer(1, 5))
S.append(Paragraph("5.2 Sundaram Category II Alternative Investment Trust - Rs 80.0 lakh", styles["H2"]))
S.append(note_box(
    "80 units at Rs 100,001 demat balance = Rs 80,00,080 (as on 30 Jun 2026). The statement itself warns "
    "this 'may not reflect the current value of your investments' and points to the 'Alternate Investment "
    "Funds III' section of the Other Products statement. At ~6.5% of total wealth this is the largest "
    "single non-MF exposure in the portfolio and the least transparent: obtain (a) the AIF's latest NAV "
    "statement, (b) drawdown/commitment schedule - whether further capital calls are pending, (c) tenure "
    "and expected distribution timeline, and (d) the fee stack (Cat-II AIFs typically charge 1.5-2% + "
    "carry). Until then, treat the Rs 80 L figure as a placeholder, not a valuation.",
    title="Action required - valuation opacity"))
S.append(Spacer(1, 5))
S.append(Paragraph("5.3 Known data gaps", styles["H2"]))
S.extend(bullets([
 "Statement page 9 (equity sectors between Finance and Miscellaneous - likely FMCG/IT and similar): reconstructed by difference as cost Rs 77,490 / value Rs 89,481 / dividends Rs 1,563. Individual stock names not visible.",
 "Statement pages 13, 19 and 22 were not photographed: page 13 is the MF section opener (all 27 scheme lines reconcile exactly, so nothing is missing there); page 19 may carry an insurance-holdings table; page 22 the disclaimer. If an insurance policy exists, it is not reflected here.",
 "PMS 'Ace Equity Advisory' AUA is excluded from this statement by ICICI's own note; EPF/PPF, bank FDs, real estate and any non-ISEC folios are outside this analysis.",
]))
S.append(PageBreak())

# ============================================================ 6. RISK
S.append(Paragraph("6. Risk Analysis", styles["H1"]))
S.append(hr())
risk_rows = [
 ["Single-scheme concentration", "MODERATE", "HDFC BAF = 26.6% of MF book / ~24% of wealth. A diversified hybrid, so not a solvency risk - but one fund manager decision-set carries a quarter of the family's assets."],
 ["Redundancy / overlap", "HIGH", "27 schemes, 13 AMCs, 8 large-cap-universe funds, 3 banking funds, 5 multi-asset funds. Cost and complexity risk rather than market risk."],
 ["Fee drag", "HIGH", "~Rs 10.95 Cr in Regular plans = Rs 6.6-11 L/yr of avoidable commissions (0.6-1.0% differential)."],
 ["Valuation opacity (AIF)", "MODERATE", "Rs 80 L (6.5% of wealth) at stale demat value; capital-call and liquidity terms unknown."],
 ["Market risk", "MODERATE", "Look-through equity ~70-75%. Hybrid sleeve cushions drawdowns meaningfully."],
 ["Liquidity risk", "LOW-MOD", "Everything except the AIF is liquid; no dedicated cash/debt bucket though."],
 ["Single-stock risk", "LOW", "Largest stock (TVS Motor) is under 1% of wealth."],
 ["Sector risk", "LOW-MOD", "Banking overweight via 3 sectoral funds + bank-heavy diversified funds; auto tilt in direct book."],
 ["Data completeness", "NOTE", "PMS excluded; pages 9/13/19/22 not photographed; AIF at demat balance."],
]
S.append(data_table(["Risk", "Rating", "Detail"],
        risk_rows, [36*mm, 20*mm, 114*mm]))
S.append(Spacer(1, 6))
S.append(Paragraph("Stress scenarios (illustrative)", styles["H2"]))
sc = [
 ["Broad bear: equity funds/stocks -25%, hybrids -12%", "-Rs 2.14 Cr", "-17.5%"],
 ["Severe crash: equity -35%, hybrids -18%", "-Rs 3.07 Cr", "-25.1%"],
 ["Banking-sector shock: bank funds -30%, diversified -10%, hybrids -6%", "-Rs 1.13 Cr", "-9.2%"],
 ["Same broad bear after consolidation + 15% debt sleeve", "~-Rs 1.7 Cr", "~-14%"],
]
S.append(data_table(["Scenario", "Wealth impact", "% of total"],
        sc, [95*mm, 40*mm, 35*mm]))
S.append(Spacer(1, 4))
S.append(P(
    "Contrast with a concentrated portfolio: this book's worst case is driven by the whole market, not by "
    "any single name. That is the healthiest kind of risk to carry - the remaining work is about efficiency "
    "(fees, overlap) and transparency (AIF), not survival."))
S.append(PageBreak())

# ============================================================ 7. TAX
S.append(Paragraph("7. Tax Position & Planning", styles["H1"]))
S.append(hr())
S.append(Paragraph("Where the unrealised gains sit (per statement)", styles["H2"]))
tx = [
 ["Mutual funds - long-term", inr(29815193.89), "Rs 2.98 Cr LTCG if fully redeemed; 12.5% above Rs 1.25 L/yr exemption"],
 ["Mutual funds - short-term", inr(335608.43), "Mostly in multi-asset/BAF folios; 20% if realised now"],
 ["Direct equity - long-term", inr(1351575.11), "Includes TVS Rs 9.09 L"],
 ["Direct equity - short-term", inr(42004.39), "Incl. TVS preference Rs 11,440"],
 ["SGB", inr(160285.90), "Tax-free at RBI redemption (Dec 2031); taxable if sold on-exchange earlier"],
]
S.append(data_table(["Bucket", "Unrealised gain (Rs)", "Comment"],
        tx, [45*mm, 40*mm, 85*mm]))
S.append(Spacer(1, 5))
S.extend(bullets([
 "<b>Consolidation is a taxable event - sequence it.</b> Selling laggard schemes triggers LTCG at 12.5% beyond the Rs 1.25 L annual exemption. Prioritise exits where embedded gains are small or negative: ICICI Business Cycle (loss), Nippon Banking (loss), ICICI Pru Large Cap (flat), Tata BAF (+4.7%), Kotak Multicap (+6.5%), SBI Multi Asset (+5.8%) - roughly Rs 1.7 Cr of value can be consolidated at a tax cost of only ~Rs 1-2 lakh.",
 "<b>Keep the big winners compounding:</b> SBI Focused (+Rs 34.4 L gain), Mirae (+Rs 39.8 L), HDFC BAF (+Rs 1.02 Cr), Sundaram L&amp;M (+Rs 21 L) - switching these has a heavy tax price; leave them (or migrate via Regular→Direct switch spread over years, using the exemption).",
 "<b>Harvest the direct-equity losses (~Rs 1.3 L)</b> against the Rs 42K ST gains and future redemptions; the broken micro-caps (Sprayking, Allcargo, Ola, Greenpanel, HG Infra, Bandhan, Titagarh, Ambuja) have no portfolio role at their size.",
 "<b>SGB:</b> do nothing until Dec 2031 - the exemption at maturity is the whole point. Coupons remain taxable at slab.",
 "<b>ELSS lock-in check:</b> Axis ELSS units older than 3 years are free - eligible for the same consolidation queue.",
]))
S.append(Spacer(1, 5))
S.append(note_box(
    "Perspective on the fee-vs-tax trade: paying ~Rs 1-2 L of LTCG once to eliminate ~Rs 7-11 L of "
    "commissions every year pays back in under 3 months. The order of operations matters: exit losers first "
    "(no tax), then low-gain schemes, then use each year's Rs 1.25 L exemption for the rest.",
    title="The consolidation math"))
S.append(PageBreak())

# ============================================================ 8. ACTION PLAN
S.append(Paragraph("8. Action Plan (prioritised)", styles["H1"]))
S.append(hr())
S.append(Paragraph("Priority 1 - within the next quarter", styles["H2"]))
S.extend(bullets([
 "<b>Get the AIF's real NAV and terms.</b> Rs 80 L (6.5% of wealth) is currently a book entry. Confirm valuation, pending capital calls, tenure, exit windows and fees; decide hold/secondary-exit with that data.",
 "<b>Start the consolidation queue (tax-cheap first):</b> exit ICICI Business Cycle, Nippon Banking, ICICI Pru Large Cap, Tata BAF; fold proceeds into the retained core (suggested: Mirae Large Cap, SBI Focused, Sundaram L&amp;M, Nippon Small Cap, HDFC BAF, ICICI Multi Asset, Quant MA Direct + one flexi-cap).",
 "<b>Cap HDFC BAF at ~15-20% of the MF book:</b> redirect its excess plus new inflows into a second hybrid or a short-duration/target-maturity debt fund - this simultaneously fixes the missing debt bucket.",
 "<b>Carve out an emergency sleeve:</b> 12-24 months of expenses into liquid/arbitrage funds (the Rs 19,000 Liquid BeES position shows the intent - scale it).",
]))
S.append(Paragraph("Priority 2 - this financial year", styles["H2"]))
S.extend(bullets([
 "<b>Regular → Direct migration</b> where no advice is being paid for: begin with every scheme in the consolidation queue (switch = same tax event anyway) and the low-gain hybrids; stagger high-gain schemes across FYs using the Rs 1.25 L exemption. Recoverable: Rs 6.6-11 L/yr.",
 "<b>Prune the direct-equity tail:</b> keep TVS (with a written trim/stop rule), Tata Steel, Paradeep, Hero, and perhaps the bank trio; exit the ~30 sub-Rs-50K positions and all broken names, harvesting ~Rs 1.3 L of losses.",
 "<b>Reduce banking-sector triplication:</b> retain DSP Banking (working), exit ICICI & Nippon banking funds.",
 "<b>Decide the multi-asset roster:</b> ICICI Multi Asset + Quant Direct as keepers; SBI/Nippon/HDFC FoF as merge candidates.",
]))
S.append(Paragraph("Priority 3 - structural hygiene", styles["H2"]))
S.extend(bullets([
 "Shrink from 13 AMCs toward 5-6; from 27 scheme-lines toward 8-10.",
 "Hold the SGB to Dec 2031 maturity; account for the ~2-4% look-through gold when sizing any new gold purchases.",
 "Pull the PMS (Ace Equity Advisory) statement and the 'Other Products' AIF-III section; re-run total-wealth allocation including them.",
 "Update nominations across folios while consolidating; check whether statement page 19 lists any insurance policy and fold it into the plan.",
 "Set an annual review: allocation vs target, scheme XIRR vs category benchmark, single-scheme cap compliance, and a one-page fee audit.",
]))
S.append(Spacer(1, 6))
S.append(Paragraph("What is already right (keep doing it)", styles["H2"]))
S.extend(bullets([
 "The core architecture - roughly half hybrid, half equity, all growth plans - is textbook-sensible and has delivered 12.74% XIRR with real downside cushioning.",
 "Big, patient positions in quality schemes (HDFC BAF, Mirae, SBI Focused, ICICI Manufacturing) show conviction sizing where it matters.",
 "The SGB purchase was excellent - up 137% with a tax-free exit ahead.",
 "Direct-equity speculation was kept to pocket-money size - the discipline the first-order numbers reward.",
]))
S.append(PageBreak())

# ============================================================ 9. APPENDIX
S.append(Paragraph("9. Appendix - Source Data & Reconciliation", styles["H1"]))
S.append(hr())
S.append(Paragraph("Statement reconciliation", styles["H2"]))
rec = [
 ["Stocks (stmt p.3/p.12)", inr(3171642.50), "2.77%", "16 photographed sector sub-totals + derived p.9 block tie to grand total"],
 ["Mutual Fund - Equity (p.3/p.17)", inr(56411850.49), "49.31%", "19 scheme lines sum EXACTLY to sub-total"],
 ["Mutual Fund - Balanced (p.3/p.18)", inr(54549438.73), "47.68%", "8 scheme lines sum EXACTLY to sub-total"],
 ["Fixed income - SGB as NCD (p.20)", inr(277116.90), "0.24%", "Matches asset-class table"],
 ["ISEC portfolio total", inr(ISEC_TOT), "100.00%", "Verified: 3,171,642.50 + 110,961,289.22 + 277,116.90"],
 ["Sundaram Cat-II AIF (p.21, 30-Jun)", inr(AIF_MV), "-", "Demat balance; outside asset-class table"],
 ["Grand total analysed", inr(GRAND), "-", ""],
]
S.append(data_table(["Item", "Value (Rs)", "% (ISEC book)", "Check"],
        rec, [48*mm, 32*mm, 22*mm, 68*mm], total_rows=[4,6]))
S.append(Spacer(1, 5))
S.append(Paragraph("Notes, caveats and data quality", styles["H2"]))
S.extend(bullets([
 "Transcribed from photographs of 16 of 22 statement pages. Both MF sleeve sub-totals reconcile to the rupee against the sum of individual scheme lines, and the equity grand total reconciles against sector sub-totals after deriving the un-photographed page 9 block (cost Rs 77,489.50 / value Rs 89,480.75 / dividends Rs 1,563).",
 "XIRR figures are as printed by ICICI Securities - money-weighted, position-specific; extreme values on young or tiny positions (Tata Motors +143%, Allcargo Global +69%) reflect short windows, not sustainable rates.",
 "Equity dividends received since inception: Rs 71,732.15. MF dividend column nil throughout (growth plans).",
 "The statement's notes: PMS Ace Equity Advisory AUA excluded; AIF demat value may not reflect current value; PE/RE funds carried at drawdown cost; report 'not valid without disclaimer'.",
 "This document is for education and for discussion with a SEBI-registered investment advisor and a chartered accountant; it is not a recommendation to buy or sell any security.",
]))
S.append(Spacer(1, 8))
S.append(hr(MAROON, 1.0))
S.append(P("<b>Bottom line:</b> a Rs 12.24 crore portfolio with the right skeleton - half hybrid, half equity, "
           "no dangerous concentrations, a 12.74% compounding record and a tax-free gold kicker. The upgrades are "
           "managerial, not structural: cut 27 scheme-lines to 8-10, migrate Regular to Direct (worth Rs 7-11 lakh a "
           "year), cap the single biggest scheme, verify the Rs 80 lakh AIF's true value, and give the portfolio the "
           "one thing it lacks - an explicit debt-and-liquidity sleeve.", "Callout"))

doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("PDF written:", OUT)
