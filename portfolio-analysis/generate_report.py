#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Portfolio Analysis Report
Source: ICICI Securities Private Wealth Management statement dated July 24, 2026
Client: Mr. B Govindarajan
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, KeepTogether, HRFlowable)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.legends import Legend

# ---------------------------------------------------------------- palette
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
                colors.HexColor("#4a7ba6"), colors.HexColor("#9c7448")]

styles = getSampleStyleSheet()

def st(name, **kw):
    base = kw.pop("base", "Normal")
    s = ParagraphStyle(name, parent=styles[base], **kw)
    styles.add(s)
    return s

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
st("BodyTight", fontName="Helvetica", fontSize=9.3, leading=13, textColor=INK,
   alignment=TA_LEFT, spaceAfter=3)
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

def rs(v, decimals=0, cr=False):
    """format rupees Indian style"""
    neg = v < 0
    v = abs(v)
    if cr:
        s = f"{v/1e7:,.2f} Cr"
    else:
        iv = int(round(v))
        s = f"{iv:,}"
        # Indian grouping
        x = str(iv)
        if len(x) > 3:
            last3 = x[-3:]; rest = x[:-3]
            parts = []
            while len(rest) > 2:
                parts.insert(0, rest[-2:]); rest = rest[:-2]
            if rest: parts.insert(0, rest)
            s = ",".join(parts) + "," + last3
    return ("-" if neg else "") + "Rs " + s

def inr(v):
    """plain Indian-grouped number"""
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

def P(txt, style="Body"):
    return Paragraph(txt, styles[style])

def bullets(items):
    return [Paragraph(t, styles["Bul"], bulletText="•") for t in items]

def hr(color=GOLD, width=0.8):
    return HRFlowable(width="100%", thickness=width, color=color,
                      spaceBefore=2, spaceAfter=8)

def kpi_row(kpis, width=170*mm):
    """kpis: list of (value, label)"""
    n = len(kpis)
    cells_v = [Paragraph(v, styles["KPInum"]) for v, _ in kpis]
    cells_l = [Paragraph(l, styles["KPIlab"]) for _, l in kpis]
    t = Table([cells_v, cells_l], colWidths=[width/n]*n)
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

def data_table(header, rows, colw, aligns=None, highlight_rows=None,
               fs=7.6, total_rows=None, red_green_col=None):
    """generic styled table. rows = list of lists of strings."""
    hl = highlight_rows or []
    tot = total_rows or []
    head = [Paragraph(h, styles["TblHead"]) for h in header]
    body = []
    for r in rows:
        line = []
        for j, c in enumerate(r):
            a = (aligns[j] if aligns else ("L" if j == 0 else "R"))
            sty = "TblCell" if a == "L" else "TblCellR"
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

def pie_chart(data, labels, width=250, height=170, title=None):
    d = Drawing(width, height)
    pie = Pie()
    pie.x = 8; pie.y = 12
    pie.width = 120; pie.height = 120
    pie.data = data
    pie.labels = None
    pie.slices.strokeWidth = 0.6
    pie.slices.strokeColor = colors.white
    for i in range(len(data)):
        pie.slices[i].fillColor = CHART_COLORS[i % len(CHART_COLORS)]
    d.add(pie)
    leg = Legend()
    leg.x = 140; leg.y = height - 30
    leg.alignment = "right"
    leg.fontName = "Helvetica"; leg.fontSize = 7.3
    leg.columnMaximum = 12
    leg.colorNamePairs = [(CHART_COLORS[i % len(CHART_COLORS)], labels[i])
                          for i in range(len(data))]
    d.add(leg)
    return d

def hbar(categories, values, width=480, height=None, color=MAROON, fmt="%.1f%%"):
    n = len(values)
    height = height or (n * 16 + 40)
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
    mn = min(0, min(values)*1.15); mx = max(values)*1.15 or 1
    bc.valueAxis.valueMin = mn; bc.valueAxis.valueMax = mx
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
# Direct equity holdings: (sector, name, shares, cost, mv, port%, div,
#                          gain, gain%, xirr12, xirrInc)
EQ = [
 ("Alcoholic Beverages","United Spirits Ltd",100,109244,141800,0.08,3400,32556,29.80,8.14,11.62),
 ("Auto Ancillary","Samvardhana Motherson Intl",3000,205361,436710,0.26,5100,231349,112.65,41.89,35.41),
 ("Auto Ancillary","Minda Corporation",100,52965,65775,0.04,150,12810,24.19,28.26,24.30),
 ("Auto Ancillary","Pricol Ltd",400,50026,250440,0.15,800,200414,400.62,40.70,43.28),
 ("Automobile","Eicher Motors Ltd",21500,159508500,166012250,97.78,0,6503750,4.08,26.09,None),
 ("Automobile","Tata Motors PAX Vehicles",150,57886,48645,0.03,1350,-9241,-15.96,-35.57,-9.19),
 ("Automobile","Maruti Suzuki India",10,86028,134030,0.08,3500,48002,55.80,7.90,15.07),
 ("Automobile","Bajaj Auto Ltd",20,159886,225670,0.13,7200,65784,41.14,38.04,37.61),
 ("Automobile","Ola Electric Mobility",6500,524910,240500,0.14,0,-284410,-54.18,-15.46,-38.17),
 ("Automobile","Hyundai Motor India",50,134290,97720,0.06,0,-36570,-27.23,-31.99,-31.99),
 ("Automobile","Tata Motors Ltd",150,26189,61185,0.04,600,34996,133.63,203.04,203.04),
 ("Banking/Finance","Bajaj Housing Finance",1500,194476,127215,0.07,0,-67261,-34.59,-29.12,-23.34),
 ("Banks","Federal Bank Ltd",250,34563,88600,0.05,850,54037,156.34,67.53,30.93),
 ("Banks","HDFC Bank Ltd",200,152380,149450,0.09,7250,-2930,-1.92,-24.36,1.05),
 ("Banks","ICICI Bank Ltd",100,72723,143460,0.08,3400,70737,97.27,-2.57,17.97),
 ("Banks","State Bank of India",250,46075,253150,0.15,17337.5,207075,449.43,26.36,34.11),
 ("Chemicals","Pidilite Industries",200,242730,312840,0.18,9000,70110,28.88,7.95,6.47),
 ("Consumer Durables","Crompton Greaves Cons.",250,101023,63112.5,0.04,3000,-37910.5,-37.53,-23.77,-10.93),
 ("E-Commerce","Eternal Ltd (Zomato)",850,191695,244035,0.14,0,52340,27.30,-8.32,19.35),
 ("Engineering","CG Power & Indl Solutions",100,72545,88380,0.05,130,15835,21.83,25.05,25.05),
 ("Engineering","Cyient DLM Ltd",100,68900,66510,0.04,0,-2390,-3.47,42.04,-1.27),
 ("Finance","Indian Railway Fin Corp",200,37160,17406,0.01,880,-19754,-53.16,-34.62,-25.07),
 ("FMCG","Hindustan Unilever",10,26435,21618,0.01,1580,-4817,-18.22,-7.68,-4.14),
 ("FMCG","Kwality Walls India",10,515,317.5,0.00,0,-197.5,-38.35,-53.40,-53.40),
 ("IT","Infosys Ltd",100,109130,104740,0.06,0,-4390,-4.02,-84.64,-84.64),
 ("Miscellaneous","VA Tech Wabag",20,31800,41146,0.02,180,9346,29.39,26.06,29.94),
 ("Pharma","Indraprastha Medical Corp",500,31670,183450,0.11,7250,151780,479.25,-20.89,53.22),
 ("Power","Tata Power Co",370,150893,139175.5,0.08,2157.5,-11717.5,-7.77,-5.51,-3.18),
 ("Oil & Gas","Indraprastha Gas Ltd",200,39540,29980,0.02,4250,-9560,-24.18,-25.72,-3.47),
]

# Mutual funds: (category, scheme, folio, units, cost, mv, port%, gain, gain%, xirr12, xirrInc, plan)
MF = [
 ("ELSS","Axis ELSS Tax Saver-G","910174019 42",9064.98,362970.12,865227.34,0.88,502257.22,138.37,-1.85,10.63,"Reg"),
 ("Flexi Cap","HDFC Flexi Cap Reg-G","3855503/62",2395.38,3499825.27,4808849.45,4.90,1309024.19,37.40,1.11,13.82,"Reg"),
 ("Flexi Cap","Franklin India Flexi Cap Reg-G","18500483",1072.53,1299935.25,1693925.72,1.73,393990.47,30.31,-4.43,10.10,"Reg"),
 ("Flexi Cap","Franklin India Flexi Cap Reg-G","19838697",1372.80,716496.64,2168160.23,2.21,1451663.59,202.61,-4.43,11.42,"Reg"),
 ("Large & Mid Cap","Kotak Large & Midcap Reg-G","12939515",12111.45,2999850.17,4233909.63,4.32,1234059.46,41.14,1.41,13.18,"Reg"),
 ("Large Cap","ICICI Pru Large Cap-G","6730915/36",159961.51,10002849.95,17191063.37,17.53,7188213.43,71.86,-2.39,12.48,"Reg"),
 ("Large Cap","Axis Large Cap Reg-G","910174019 42",66723.29,2349947.49,3947349.95,4.03,1597402.47,67.98,-2.70,9.66,"Reg"),
 ("Large Cap","HDFC Large Cap Fund Reg-G","3855503/62",888.16,485763.31,996618.50,1.02,510855.19,105.17,-2.05,10.70,"Reg"),
 ("Large Cap","HDFC Large Cap Fund Reg-G","7327620/56",374.22,126918.67,419922.36,0.43,293003.69,230.86,-2.05,11.49,"Reg"),
 ("Sectoral - Transport","HDFC Transportation & Logistics-G","3855503/62",232734.84,2999849.99,4320489.59,4.41,1320639.60,44.02,13.98,21.61,"Reg"),
 ("Sectoral - Metal ETF","Groww Nifty Metal ETF-G","510196522 96",4999.00,49990.00,59436.61,0.06,9446.61,18.90,33.79,33.79,"ETF"),
 ("Thematic - Mfg","ICICI Pru Manufacturing-G","6730915/36",275549.71,6999649.94,10603152.96,10.81,3603503.01,51.48,9.25,20.17,"Reg"),
 ("Value","ICICI Pru Value-G","6730915/36",539.57,249987.72,246728.72,0.25,-3259.00,-1.30,-1.37,9.75,"Reg"),
 ("Aggressive Hybrid","HDFC Hybrid Equity Reg-G","3855503/62",91369.53,5587052.33,10282452.23,10.49,4695399.90,84.04,-6.28,9.90,"Reg"),
 ("Aggressive Hybrid","HDFC Hybrid Equity Reg-G","7327620/56",2089.87,107097.48,235187.70,0.24,128090.22,119.60,-6.28,9.25,"Reg"),
 ("Dynamic Asset Alloc","HDFC Balanced Advantage Reg-G","3855503/62",35234.01,14941686.16,18234446.31,18.59,3292760.14,22.04,-1.39,9.90,"Reg"),
 ("Dynamic Asset Alloc","HDFC Balanced Advantage Reg-G","6987292/18",164.66,30094.20,85213.95,0.09,55119.75,183.16,-0.49,13.54,"Reg"),
 ("Dynamic Asset Alloc","HDFC Balanced Advantage Reg-G","7077067/62",213.93,39098.86,110711.32,0.11,71612.46,183.16,-0.49,13.54,"Reg"),
 ("Dynamic Asset Alloc","HDFC Balanced Advantage Reg-G","7189839/82",180.74,33034.40,93539.36,0.10,60504.96,183.16,-0.49,13.54,"Reg"),
 ("Dynamic Asset Alloc","HDFC Balanced Advantage Reg-G","7327620/56",217.06,39672.57,112335.83,0.11,72663.26,183.16,-0.49,13.54,"Reg"),
 ("Dynamic Asset Alloc","ICICI Pru Balanced Advantage-G","6730915/36",121582.89,5995214.06,9431184.85,9.62,3435970.80,57.31,4.99,10.74,"Reg"),
 ("Multi Asset","Kotak Multi Asset Alloc Direct-G","12939515",61462.77,999949.99,996741.71,1.02,-3208.28,-0.32,-1.84,-1.84,"Dir"),
 ("Multi Asset","ICICI Pru Multi Asset-G","6730915/36",5439.28,3499824.57,4368750.33,4.45,868925.76,24.83,5.73,11.58,"Reg"),
 ("Multi Asset","Quant Multi Asset Alloc Direct-G","510106092 962",13915.54,2499875.09,2559848.28,2.61,59973.19,2.40,20.70,20.70,"Dir"),
]

EQ_COST = sum(r[3] for r in EQ)          # 162,519,538
EQ_MV   = sum(r[4] for r in EQ)          # 169,789,310.5
EQ_GAIN = EQ_MV - EQ_COST
MF_COST = 65916634.23
MF_MV   = 98065246.32
MF_GAIN = 32148612.10
TOT_MV  = 267854556.80
ULIP_MV = 6348403.16
DEMAT_OTHER = 54999.0
GRAND = TOT_MV + ULIP_MV + DEMAT_OTHER

EICHER_MV = 166012250.0
EX_EICHER_COST = EQ_COST - 159508500
EX_EICHER_MV = EQ_MV - EICHER_MV

# ---------------------------------------------------------------- doc
OUT = "/tmp/claude-0/-home-user-rstate/8e5eba92-2688-5f8a-ad4f-1b7c48e108f9/scratchpad/Portfolio_Analysis_B_Govindarajan_Jul2026.pdf"

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(SLATE)
    canvas.drawString(20*mm, 11*mm,
        "Comprehensive Portfolio Analysis  |  Data as on July 24, 2026  |  Source: ICICI Securities PWM statement")
    canvas.drawRightString(190*mm, 11*mm, f"Page {doc.page}")
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(0.6)
    canvas.line(20*mm, 14*mm, 190*mm, 14*mm)
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=20*mm, rightMargin=20*mm,
                        topMargin=16*mm, bottomMargin=18*mm,
                        title="Comprehensive Portfolio Analysis - B Govindarajan",
                        author="Portfolio Analysis")

S = []

# ============================================================ COVER
S.append(Spacer(1, 34*mm))
S.append(Paragraph("COMPREHENSIVE<br/>PORTFOLIO ANALYSIS", styles["CoverTitle"]))
S.append(Spacer(1, 6*mm))
S.append(HRFlowable(width="45%", thickness=1.2, color=GOLD, hAlign="CENTER"))
S.append(Spacer(1, 6*mm))
S.append(Paragraph("Mr. B Govindarajan", ParagraphStyle("cn", parent=styles["CoverSub"],
        fontSize=17, textColor=MAROON, fontName="Helvetica-Bold", leading=22)))
S.append(Spacer(1, 3*mm))
S.append(Paragraph("ICICI Securities Private Wealth Management Account", styles["CoverSub"]))
S.append(Paragraph("Holdings as on July 24, 2026  (Demat 'other holdings' as on June 30, 2026)", styles["CoverSub"]))
S.append(Spacer(1, 14*mm))
S.append(kpi_row([
    (rs(GRAND, cr=True), "TOTAL WEALTH ANALYSED"),
    (rs(EQ_MV, cr=True), "DIRECT EQUITY"),
    (rs(MF_MV, cr=True), "MUTUAL FUNDS"),
    (rs(ULIP_MV, cr=True), "ULIP FUND VALUE"),
]))
S.append(Spacer(1, 10*mm))
S.append(note_box(
    "This report was prepared from photographs of the ICICI Securities PWM portfolio statement. "
    "It is an independent analytical exercise for education and discussion with your advisor; it is "
    "not investment advice, and figures should be re-verified against the original statement. "
    "ISEC PMS 'Ace Equity Advisory' assets are explicitly excluded from the source statement "
    "(see Section 9), so any PMS holdings are additional to the numbers here.",
    title="Scope & Disclaimer"))
S.append(PageBreak())

# ============================================================ 1. EXEC SUMMARY
S.append(Paragraph("1. Executive Summary", styles["H1"]))
S.append(hr())
S.append(P(
    f"The statement covers <b>{rs(TOT_MV, cr=True)}</b> of market-linked investments "
    f"({rs(EQ_MV, cr=True)} direct equity + {rs(MF_MV, cr=True)} mutual funds), plus a ULIP worth "
    f"{rs(ULIP_MV, cr=True)} and residual demat holdings of {rs(DEMAT_OTHER)}. Total wealth analysed: "
    f"<b>{rs(GRAND, cr=True)} (~Rs 27.4 crore)</b>."))
S.append(P(
    "The portfolio is <b>100% equity/equity-linked</b> on the ICICI Securities books — the statement shows "
    "no fixed income, no debt mutual funds (other than a written-off segregated Franklin holding), and no gold, "
    "other than indirect debt/gold inside hybrid funds. The defining feature of the portfolio — and by far its "
    "biggest risk — is a single stock:"))
S.append(Spacer(1, 2))
S.append(note_box(
    f"<b>Eicher Motors = {rs(EICHER_MV, cr=True)} — 97.8% of the direct equity book and roughly 60.5% of "
    f"total wealth.</b> 21,500 shares bought at an average of Rs 7,419 (cost {rs(159508500, cr=True)}), now at "
    f"Rs 7,721.50. The entire unrealised gain of {rs(6503750)} is <b>short-term</b>, i.e. the position was built "
    "within the last 12 months. One company, one sector, one earnings call now decides the fate of this "
    "family's wealth. A 20% drawdown in this one stock erases ~Rs 3.3 crore — more than the combined value "
    "of every other direct stock held.", title="CRITICAL FINDING — Single-stock concentration"))
S.append(Spacer(1, 4))
S.append(Paragraph("Headline scorecard", styles["H2"]))
rows = [
 ["Direct equity (28 stocks)", inr(EQ_COST), inr(EQ_MV), inr(EQ_GAIN), "+4.5%", "Distorted by recent Eicher buy"],
 ["  - of which Eicher Motors", inr(159508500), inr(EICHER_MV), inr(6503750), "+4.1%", "97.8% of equity book, all ST gain"],
 ["  - equity ex-Eicher (27 stocks)", inr(EX_EICHER_COST), inr(EX_EICHER_MV), inr(EX_EICHER_MV-EX_EICHER_COST), "+25.4%", "Long-tail of small positions"],
 ["Mutual funds (24 lines)", inr(MF_COST), inr(MF_MV), inr(MF_GAIN), "+48.8%", "XIRR 11.65% since inception"],
 ["ULIP (ICICI Pru Elite Wealth II)", inr(2500000), inr(ULIP_MV), inr(3848403), "+153.9%", "Est. XIRR ~10.8% over 11 yrs"],
 ["Other demat", "-", inr(DEMAT_OTHER), "-", "-", "Groww MF units + 1 VECV share"],
 ["Total analysed", inr(EQ_COST+MF_COST+2500000), inr(GRAND), "", "", ""],
]
S.append(data_table(
    ["Block", "Cost (Rs)", "Market Value (Rs)", "Unrealised P&amp;L (Rs)", "Return", "Comment"],
    rows, [40*mm, 26*mm, 28*mm, 26*mm, 14*mm, 36*mm],
    total_rows=[6], highlight_rows=[1]))
S.append(Spacer(1, 5))
S.append(Paragraph("Top 5 findings", styles["H2"]))
S.extend(bullets([
 "<b>Extreme concentration:</b> Eicher Motors is ~60.5% of total wealth; the auto ecosystem overall (Eicher + other auto stocks + auto-ancillaries + HDFC Transportation & Logistics fund) is ~Rs 17.2 crore, i.e. ~63% of everything.",
 "<b>Zero fixed income:</b> asset-class table shows Equity 100.00%. For a portfolio of this size there is no liquidity buffer, no rebalancing dry powder, and full drawdown exposure. Only ~28% sits in hybrid funds where the fund manager holds some debt internally.",
 "<b>The mutual fund book is the quiet performer:</b> Rs 6.59 Cr invested has become Rs 9.81 Cr (+48.8%, XIRR 11.65%). Large, sensible positions in large-cap, balanced-advantage and manufacturing funds have compounded well — but 22 of 24 lines are Regular plans, costing an estimated ~Rs 60-100 lakh per decade in extra commissions versus Direct plans.",
 "<b>A long tail of clutter:</b> 27 direct stocks together are just 2.2% of the equity book; 13 of them are in loss (Ola Electric -54%, IRFC -53%, Kwality Walls -38%, Crompton -38%, Bajaj Housing -35%). None is large enough to matter — they add monitoring burden, not returns.",
 "<b>Data gaps to close:</b> ISEC PMS (Ace Equity Advisory) AUA is excluded from this statement; the Franklin Credit Risk segregated portfolio (25,369 units) is carried at nil; MF 12-month XIRR is just 0.56%, signalling a flat trailing year for the whole book.",
]))
S.append(PageBreak())

# ============================================================ 2. ALLOCATION
S.append(Paragraph("2. Asset Allocation & Structure", styles["H1"]))
S.append(hr())
S.append(P(
    "The statement's own asset-class summary (ISEC book only): Stocks 63.39%, Mutual Fund-Equity 19.25%, "
    "Mutual Fund-Balanced 17.36%, Fixed Income 0.00%. Including the ULIP and other demat units, the "
    "true picture of the analysed wealth is below."))
alloc_rows = [
 ["Direct equity - Eicher Motors", inr(EICHER_MV), f"{EICHER_MV/GRAND*100:.1f}%"],
 ["Direct equity - other 27 stocks", inr(EX_EICHER_MV), f"{EX_EICHER_MV/GRAND*100:.1f}%"],
 ["MF - pure equity schemes", inr(51554834.44), f"{51554834.44/GRAND*100:.1f}%"],
 ["MF - hybrid/balanced schemes", inr(46510411.88), f"{46510411.88/GRAND*100:.1f}%"],
 ["ULIP fund value", inr(ULIP_MV), f"{ULIP_MV/GRAND*100:.1f}%"],
 ["Other demat holdings", inr(DEMAT_OTHER), f"{DEMAT_OTHER/GRAND*100:.2f}%"],
 ["Total", inr(GRAND), "100.0%"],
]
S.append(data_table(["Component", "Value (Rs)", "% of total wealth"],
                    alloc_rows, [70*mm, 50*mm, 50*mm], total_rows=[6]))
S.append(Spacer(1, 6))
S.append(pie_chart(
    [EICHER_MV, EX_EICHER_MV, 51554834.44, 46510411.88, ULIP_MV],
    ["Eicher Motors 60.5%", "Other direct stocks 1.4%", "Equity MFs 18.8%",
     "Hybrid MFs 17.0%", "ULIP 2.3%"],
    width=430, height=150))
S.append(Spacer(1, 4))
S.append(Paragraph("What this allocation implies", styles["H2"]))
S.extend(bullets([
 "<b>Effective equity exposure is ~90%+.</b> Hybrid funds (BAF/multi-asset/aggressive hybrid, Rs 4.65 Cr) typically run 30-80% net equity; assuming ~55% average, look-through equity is roughly Rs 24.5 Cr of Rs 27.4 Cr.",
 "<b>Concentration dwarfs diversification.</b> The entire 24-scheme, Rs 9.8 Cr mutual fund edifice diversifies less than the single Eicher position concentrates: a Herfindahl (HHI) calculation on total wealth gives ~0.37 — equivalent to holding fewer than 3 independent positions.",
 "<b>No liability/liquidity layer.</b> There is no visible emergency-fund, bond, arbitrage or liquid-fund allocation on this statement. Any cash need during a market fall would force selling equity at the worst time.",
 "<b>Dividend yield is negligible</b> (~Rs 79,365 dividends received since inception across all stocks, ~0.05% on current equity value) — the portfolio produces essentially no income stream.",
]))
S.append(PageBreak())

# ============================================================ 3. EQUITY DEEP DIVE
S.append(Paragraph("3. Direct Equity — Deep Dive (28 holdings)", styles["H1"]))
S.append(hr())
S.append(P(
    f"Cost {rs(EQ_COST, cr=True)} → market value {rs(EQ_MV, cr=True)} (+4.5%). Stripping out Eicher, the "
    f"residual 27 stocks cost {rs(EX_EICHER_COST, cr=True)} and are worth {rs(EX_EICHER_MV, cr=True)} "
    "(+25.4%) — decent in aggregate, but the median position is only ~Rs 1.3 lakh, so even the 4-baggers "
    "(Pricol +401%, Indraprastha Medical +479%, SBI +449%) moved family wealth by less than 0.1% each."))
S.append(Paragraph("3.1 Complete holdings register", styles["H2"]))
hdr = ["Sector / Stock", "Qty", "Cost (Rs)", "Mkt Value (Rs)", "P&amp;L (Rs)", "P&amp;L %", "XIRR 12m", "XIRR Incep."]
rows = []
cur = None
for sec, nm, q, c, m, pct, dv, g, gp, x12, xin in EQ:
    if sec != cur:
        rows.append([f"<b>{sec}</b>", "", "", "", "", "", "", ""])
        cur = sec
    rows.append([nm, f"{q:,}", inr(c), inr(m), inr(g), f"{gp:+.1f}%",
                 ("-" if x12 is None else f"{x12:+.1f}%"),
                 ("-" if xin is None else f"{xin:+.1f}%")])
rows.append(["<b>TOTAL (28 stocks)</b>", "", inr(EQ_COST), inr(EQ_MV), inr(EQ_GAIN), "+4.5%", "", ""])
S.append(data_table(hdr, rows,
        [42*mm, 12*mm, 24*mm, 24*mm, 22*mm, 14*mm, 16*mm, 16*mm],
        total_rows=[len(rows)-1]))
S.append(Spacer(1, 4))
S.append(P("<i>Note: Eicher Motors' 'XIRR since inception' is blank in the statement because the "
           "position is younger than a year; its 12-month XIRR of 26.09% reflects a favourable entry, "
           "and the P&L% (+4.1%) reflects price movement on the full Rs 15.95 Cr outlay.</i>", "Small"))
S.append(PageBreak())

S.append(Paragraph("3.2 Winners, losers and what they tell us", styles["H1"]))
S.append(hr())
S.append(Paragraph("Biggest winners (by % gain since purchase)", styles["H3"]))
win = [
 ["Indraprastha Medical Corp", "+479%", inr(151780), "53.2%", "Small position, huge multiple - textbook winner kept too small"],
 ["State Bank of India", "+449%", inr(207075), "34.1%", "PSU bank re-rating captured"],
 ["Pricol Ltd", "+401%", inr(200414), "43.3%", "Auto-ancillary compounder"],
 ["Federal Bank", "+156%", inr(54037), "30.9%", "Strong hold"],
 ["Tata Motors Ltd", "+134%", inr(34996), "203.0%*", "*XIRR inflated by short holding period"],
 ["Samvardhana Motherson", "+113%", inr(231349), "35.4%", "Largest non-Eicher winner in Rs"],
 ["ICICI Bank", "+97%", inr(70737), "18.0%", "Compounder"],
]
S.append(data_table(["Stock", "Abs. gain %", "Gain (Rs)", "XIRR incep.", "Read"],
        win, [40*mm, 18*mm, 22*mm, 18*mm, 72*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Biggest losers (by % loss since purchase)", styles["H3"]))
los = [
 ["Ola Electric Mobility", "-54.2%", inr(-284410), "Biggest rupee loss ex-Eicher risk; thesis broken? Exit candidate / tax-loss harvest"],
 ["IRFC", "-53.2%", inr(-19754), "Bought near PSU-rally top"],
 ["Kwality Walls India", "-38.4%", inr(-197.5), "Rs 317 position - demat dust"],
 ["Crompton Greaves Cons.", "-37.5%", inr(-37910), "Consumer durables drag"],
 ["Bajaj Housing Finance", "-34.6%", inr(-67261), "IPO-era entry at rich valuation"],
 ["Hyundai Motor India", "-27.2%", inr(-36570), "Recent IPO, all short-term loss"],
 ["Indraprastha Gas", "-24.2%", inr(-9560), "Regulatory margin squeeze"],
 ["Hindustan Unilever", "-18.2%", inr(-4817), "10 shares - negligible"],
 ["Tata Motors PAX", "-16.0%", inr(-9241), "Post-demerger stub"],
]
S.append(data_table(["Stock", "Loss %", "Loss (Rs)", "Read"],
        los, [40*mm, 16*mm, 22*mm, 92*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Sector exposure of the equity book", styles["H2"]))
S.append(P("Automobile alone is 98.25% of direct equity. Aggregating the auto ecosystem across the whole "
           "portfolio (Eicher + 6 other auto stocks + 3 ancillaries + the HDFC Transportation & Logistics fund) "
           "gives <b>~Rs 17.19 crore = ~62.7% of total wealth</b> exposed to one cyclical, "
           "capex-heavy, EV-disruptable sector."))
S.extend(bullets([
 "Banks + finance stocks: Rs 7.79 lakh (0.46% of equity) - immaterial.",
 "Every other sector (FMCG, IT, pharma, power, chemicals, oil & gas) is below 0.2% of the equity book each.",
 "The 27 non-Eicher stocks look like an accumulated 'watchlist with money' - 13 sub-Rs-1-lakh positions, several from IPO allotments (Ola, Hyundai, Bajaj Housing) still carried at losses.",
]))
S.append(PageBreak())

# ============================================================ 4. MF DEEP DIVE
S.append(Paragraph("4. Mutual Funds — Deep Dive (24 lines, 13 schemes)", styles["H1"]))
S.append(hr())
S.append(P(
    f"Cost {rs(MF_COST, cr=True)} → value {rs(MF_MV, cr=True)}, unrealised gain {rs(MF_GAIN, cr=True)} "
    "(+48.8%). Since-inception XIRR 11.65% — a respectable outcome versus large-cap index returns, achieved "
    "with hybrid cushioning. Trailing 12-month XIRR is just <b>0.56%</b>, consistent with a flat/choppy market "
    "year; the negative 12-month XIRRs on most pure-equity funds (-1.4% to -4.4%) confirm it."))
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
rows.append(["<b>Equity schemes sub-total</b>", "", inr(32144034.51), inr(51554834.44), "+60.4%", "+1.40%", "+12.69%", ""])
rows.append(["<b>Balanced schemes sub-total</b>", "", inr(33772599.72), inr(46510411.88), "+37.7%", "-0.46%", "+10.28%", ""])
rows.append(["<b>GRAND TOTAL</b>", "", inr(MF_COST), inr(MF_MV), "+48.8%", "+0.56%", "+11.65%", ""])
S.append(data_table(hdr, rows,
        [52*mm, 14*mm, 24*mm, 24*mm, 14*mm, 14*mm, 14*mm, 12*mm],
        total_rows=[len(rows)-3, len(rows)-2, len(rows)-1], fs=7.2))
S.append(Spacer(1, 3))
S.append(P("<i>Also on the books: Franklin India Credit Risk Fund - Segregated Portfolio 3 (25,369.34 units, "
           "folio 18500483) carried at nil value - the side-pocket created from the 2020 Franklin debt episode. "
           "Any future recovery is a bonus; keep the folio alive and track AMC payout notices.</i>", "Small"))
S.append(PageBreak())

S.append(Paragraph("4.2 Category & AMC structure", styles["H1"]))
S.append(hr())
cat_rows = [
 ["Dynamic Asset Allocation (BAF)", inr(28067431.62), "28.6%", "HDFC BAF (5 folios!) + ICICI BAF"],
 ["Large Cap", inr(22554954.18), "23.0%", "ICICI Pru Large Cap is single biggest scheme (17.5%)"],
 ["Thematic - Manufacturing", inr(10603152.96), "10.8%", "ICICI Pru Manufacturing"],
 ["Aggressive Hybrid", inr(10517639.93), "10.7%", "HDFC Hybrid Equity (2 folios)"],
 ["Flexi Cap", inr(8670935.40), "8.8%", "HDFC + Franklin (2 folios)"],
 ["Multi Asset", inr(7925340.32), "8.1%", "Kotak + ICICI + Quant"],
 ["Sectoral - Auto & Transport", inr(4320489.59), "4.4%", "HDFC Transportation & Logistics"],
 ["Large & Mid Cap", inr(4233909.63), "4.3%", "Kotak"],
 ["ELSS", inr(865227.34), "0.9%", "Axis ELSS"],
 ["Value", inr(246728.72), "0.25%", "ICICI Pru Value"],
 ["Sectoral - Metal ETF", inr(59436.61), "0.06%", "Groww Nifty Metal ETF"],
]
S.append(data_table(["Category", "Value (Rs)", "% of MF", "Schemes"],
        cat_rows, [46*mm, 30*mm, 18*mm, 76*mm]))
S.append(Spacer(1, 6))
amc = [("HDFC MF", 39699766.60), ("ICICI Prudential MF", 41840880.23),
       ("Kotak MF", 5230651.34), ("Axis MF", 4812577.29),
       ("Franklin Templeton", 3862085.95), ("Quant MF", 2559848.28),
       ("Groww MF", 59436.61)]
S.append(Paragraph("AMC concentration", styles["H2"]))
S.append(hbar([a for a, _ in amc], [v/MF_MV*100 for _, v in amc],
              width=470, color=GOLD))
S.append(Spacer(1, 4))
S.extend(bullets([
 "<b>ICICI Pru (42.7%) + HDFC (40.5%) = 83% of the MF book.</b> AMC-house concentration is a real, if second-order, risk (house investment style, key-person changes). Adding a third/fourth house at meaningful weight is advisable as the book grows.",
 "<b>Folio sprawl:</b> HDFC Balanced Advantage is held across five folios, HDFC Large Cap and HDFC Hybrid Equity across two each, Franklin Flexi Cap across two. Consolidating folios simplifies tracking, nominations and eventual succession.",
 "<b>Regular-plan drag:</b> 22 of 24 lines are Regular plans (only Kotak Multi Asset and Quant Multi Asset are Direct). At a typical 0.6-1.0% p.a. distributor-commission differential on ~Rs 9.4 Cr of Regular holdings, the annual cost is roughly <b>Rs 5.5-9.5 lakh</b> - Rs 60 lakh to Rs 1 crore per decade if the corpus merely stays flat. Where an advisor genuinely earns this via advice, fine; otherwise switching to Direct (after weighing capital-gains tax on switch) is the single largest 'free lunch' in this portfolio.",
 "<b>Category logic is broadly sound:</b> ~47% hybrid gives real drawdown cushioning; large-cap tilt in the equity sleeve is sensible. The oddities are the tiny tail positions (Value fund Rs 2.5L, Metal ETF Rs 59K, ELSS Rs 8.7L) that add lines without moving the needle.",
]))
S.append(PageBreak())

S.append(Paragraph("4.3 Scheme-level performance read", styles["H1"]))
S.append(hr())
S.append(Paragraph("Best compounders (XIRR since inception)", styles["H3"]))
best = [
 ["Groww Nifty Metal ETF", "+33.8%", "Tiny and young - not meaningful"],
 ["HDFC Transportation & Logistics", "+21.6%", "Thematic auto bet that worked; overlaps Eicher risk"],
 ["Quant Multi Asset (Direct)", "+20.7%", "Young position"],
 ["ICICI Pru Manufacturing", "+20.2%", "Rs 1.06 Cr position, +51.5% absolute - genuine contributor"],
 ["HDFC Flexi Cap", "+13.8%", "Rs 48 L position, steady"],
 ["HDFC BAF (older folios)", "+13.5%", "Long-held small folios show the fund's real long-run power"],
 ["Kotak Large & Midcap", "+13.2%", "Solid"],
 ["ICICI Pru Large Cap", "+12.5%", "Biggest scheme, biggest rupee gain (Rs 71.9 L)"],
]
S.append(data_table(["Scheme", "XIRR incep.", "Read"], best, [52*mm, 20*mm, 98*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Laggards / attention list", styles["H3"]))
lag = [
 ["Kotak Multi Asset (Direct)", "-1.8%", "Young; watch, not worry"],
 ["Axis Large Cap", "+9.7%", "Chronic Axis underperformance era; switch candidate into existing large-cap"],
 ["Axis ELSS Tax Saver", "+10.6%", "Lock-in likely over; roll into mainstream equity when tax-efficient"],
 ["HDFC Hybrid Equity (folio /56)", "+9.3%", "Duplicate folio of same scheme"],
 ["ICICI Pru Value", "+9.8%", "Rs 2.5 L orphan position"],
 ["Franklin Flexi Cap folios", "+10.1% / +11.4%", "OK performance; two folios of same scheme should be one"],
]
S.append(data_table(["Scheme", "XIRR incep.", "Read"], lag, [52*mm, 24*mm, 94*mm]))
S.append(Spacer(1, 5))
S.append(Paragraph("Equity vs hybrid sleeves", styles["H2"]))
sleeve = [
 ["Pure equity sleeve", inr(32144034.51), inr(51554834.44), "+60.4%", "+12.69%", "Driven by large-cap & manufacturing"],
 ["Hybrid sleeve", inr(33772599.72), inr(46510411.88), "+37.7%", "+10.28%", "Lower return, much lower volatility"],
]
S.append(data_table(["Sleeve", "Cost (Rs)", "Value (Rs)", "Abs. return", "XIRR", "Comment"],
        sleeve, [30*mm, 28*mm, 28*mm, 20*mm, 18*mm, 46*mm]))
S.append(Spacer(1, 4))
S.append(P("The ~2.4 percentage-point XIRR gap between the sleeves is the price paid for the hybrid cushion. "
           "Given the monstrous single-stock risk sitting next door in the equity account, this cushion is "
           "currently the portfolio's only real shock absorber - it should be preserved (or even enlarged with "
           "genuine fixed income) until the Eicher position is diversified."))
S.append(PageBreak())

# ============================================================ 5. ULIP
S.append(Paragraph("5. Insurance (ULIP) & Other Demat Holdings", styles["H1"]))
S.append(hr())
S.append(Paragraph("5.1 ICICI Pru Elite Wealth II - RP (Policy 19369756)", styles["H2"]))
ul = [
 ["Issued / Matures", "30 Jun 2015 / 30 Jun 2035"],
 ["Life cover", inr(5000000)],
 ["Premium", inr(500000) + " p.a. x 5 years (paid till 30 Jun 2020 - premium term complete)"],
 ["Total premiums paid", inr(2500000)],
 ["Fund value (24 Jul 2026)", inr(6348403.16)],
 ["Multiple on premiums", "2.54x over ~11 years"],
 ["Estimated XIRR", "~10.8% p.a. (5 annual outflows 2015-19 vs today's value)"],
]
t = Table([[Paragraph(f"<b>{a}</b>", styles["TblCell"]), Paragraph(b, styles["TblCell"])] for a, b in ul],
          colWidths=[45*mm, 125*mm])
t.setStyle(TableStyle([
    ("GRID", (0,0), (-1,-1), 0.35, LGREY),
    ("BACKGROUND", (0,0), (0,-1), PALE),
    ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
]))
S.append(t)
S.append(Spacer(1, 4))
S.extend(bullets([
 "A ~10.8% net XIRR is genuinely decent for a ULIP - charges are now largely behind (they front-load), so the ongoing economics resemble a moderately-priced equity fund with a small life cover attached.",
 "Under current tax law, ULIP maturity proceeds stay tax-exempt u/s 10(10D) for policies issued before Feb 2021 with premium ≤ Rs 2.5L/yr - this policy (Rs 5L premium) should be checked with a tax advisor; the 2021 amendment applies to policies issued after 1 Feb 2021, so this 2015 policy's maturity should remain exempt. That exemption argues for holding to 2035 rather than surrendering.",
 "Life cover of Rs 50 L is trivial against Rs 27+ Cr of wealth and presumably substantial family expenses - if income protection matters, a separate term policy is the right instrument; the ULIP should be viewed purely as an investment.",
]))
S.append(Spacer(1, 5))
S.append(Paragraph("5.2 Other holdings in demat (30 Jun 2026)", styles["H2"]))
od = [
 ["INF666M01NI0", "Groww Mutual Fund units", "4,999", "11.00", inr(54989)],
 ["INE014T01013", "VE Commercial Vehicles Ltd", "1", "10.00", inr(10)],
 ["", "<b>Total</b>", "", "", inr(54999)],
]
S.append(data_table(["ISIN", "Scrip", "Qty", "Price (Rs)", "Value (Rs)"],
        od, [32*mm, 62*mm, 20*mm, 26*mm, 30*mm], total_rows=[2]))
S.append(Spacer(1, 3))
S.append(P("The single VE Commercial Vehicles share (unlisted; from the 2011 Eicher restructuring era or a "
           "corporate action) and the Groww MF units held in demat form are housekeeping items - the Groww "
           "units duplicate the Metal ETF exposure category and could be consolidated into the main MF fold.", "Body"))
S.append(Spacer(1, 5))
S.append(Paragraph("5.3 PMS - the missing piece", styles["H2"]))
S.append(note_box(
    "The statement's explanatory note says: 'AUA for ISEC PMS Ace Equity Advisory are not included in this "
    "report.' If the family holds a PMS with ICICI Securities (or elsewhere), its holdings, costs and overlap "
    "with this portfolio are invisible here. Before acting on any recommendation in this report, pull the "
    "monthly PMS statement and check: (a) whether the PMS also holds auto/Eicher exposure (compounding the "
    "concentration), and (b) total-wealth asset allocation including PMS.", title="PMS data gap"))
S.append(PageBreak())

# ============================================================ 6. RISK
S.append(Paragraph("6. Risk Analysis", styles["H1"]))
S.append(hr())
risk_rows = [
 ["Single-stock concentration", "SEVERE", "Eicher = 60.5% of wealth. Prudent norm: no single stock >5-10%. A -30% stock move = -Rs 5.0 Cr (-18% of wealth)."],
 ["Sector concentration", "SEVERE", "Auto ecosystem ~63% of wealth (incl. transport fund & ancillaries). Cyclical + EV disruption + export/tariff sensitivity."],
 ["Asset-class concentration", "HIGH", "100% equity-linked on ISEC books. No bonds/liquid funds visible; hybrids are the only cushion (~17% of wealth, internally ~40% debt)."],
 ["Liquidity risk", "MODERATE", "Eicher is liquid large-cap, exit is mechanically easy - but a Rs 16.6 Cr sale has tax and timing consequences; no cash buffer exists for emergencies."],
 ["Tax-event risk", "MODERATE", "Eicher gain currently 100% short-term (20% STCG). Premature exit locks in higher tax; but waiting for LTCG (12.5%) must be weighed against concentration risk every single day."],
 ["AMC concentration", "LOW-MOD", "83% of MF book with 2 AMCs (ICICI Pru + HDFC)."],
 ["Product hygiene", "LOW", "5 folios of one scheme, Regular-plan fee drag, Franklin side-pocket, orphan micro-positions - operational, fixable."],
 ["Data completeness", "NOTE", "PMS excluded; 'other holdings' dated 30-Jun vs 24-Jul for the rest; report validity depends on original statement disclaimer."],
]
S.append(data_table(["Risk", "Rating", "Detail"],
        risk_rows, [34*mm, 20*mm, 116*mm]))
S.append(Spacer(1, 6))
S.append(Paragraph("Stress scenarios (illustrative)", styles["H2"]))
sc = [
 ["Auto down-cycle: Eicher -30%, other auto -25%, MFs -8%", "-Rs 5.9 Cr", "-21.5%"],
 ["Broad bear market: equity -25%, hybrids -12%", "-Rs 6.6 Cr", "-24.1%"],
 ["Eicher company-specific shock: -40%, rest flat", "-Rs 6.6 Cr", "-24.2%"],
 ["Post-diversification (Eicher trimmed to 10%, 50% bonds added): same bear market", "~-Rs 2.5-3 Cr", "~-10%"],
]
S.append(data_table(["Scenario", "Wealth impact", "% of total"],
        sc, [95*mm, 40*mm, 35*mm]))
S.append(Spacer(1, 4))
S.append(P("The last row is the point: the portfolio's downside is a <i>choice</i>, not a fate. Diversifying "
           "the single-stock and single-sector bets cuts worst-case drawdowns by more than half without "
           "necessarily giving up long-run equity returns."))
S.append(Spacer(1, 4))
S.append(Paragraph("Behavioural observations", styles["H2"]))
S.extend(bullets([
 "The MF book shows patient, systematic behaviour (large positions, multi-year holding, +48.8%). The direct-equity book ex-Eicher shows the opposite - many small speculative entries, IPO punts held through -30-50% losses.",
 "The Eicher position is either (a) deep conviction/insider-style knowledge (e.g. professional connection to the company), (b) an inheritance/ESOP-type event, or (c) a very large momentum bet. Each has a different right answer - but none of them justifies 60% of family wealth in one ticker for long.",
]))
S.append(PageBreak())

# ============================================================ 7. TAX
S.append(Paragraph("7. Tax Position & Planning", styles["H1"]))
S.append(hr())
S.append(Paragraph("Where the unrealised gains sit (per statement)", styles["H2"]))
tx = [
 ["Direct equity - short-term", inr(6701189), "Dominated by Eicher Rs 65.04 L ST gain (auto subtotal ST Rs 64.54 L net of Ola/Hyundai ST losses)"],
 ["Direct equity - long-term", inr(568583.5), "Modest; several LT losses embedded too (ties to total equity gain Rs 72.70 L)"],
 ["Mutual funds - short-term", inr(36897.11), "Negligible"],
 ["Mutual funds - long-term", inr(32111715.00), "The big one: Rs 3.21 Cr LTCG if fully redeemed"],
]
S.append(data_table(["Bucket", "Unrealised gain (Rs)", "Comment"],
        tx, [45*mm, 40*mm, 85*mm]))
S.append(Spacer(1, 5))
S.extend(bullets([
 "<b>Eicher timing trade-off:</b> selling today taxes ~Rs 65 L of gain at 20% STCG (~Rs 13 L). Once holdings cross 12 months, the rate drops to 12.5% LTCG (saving ~Rs 4.9 L on today's gain) - but every month of waiting carries ~Rs 16.6 Cr of single-stock risk. A staged sell-down (e.g. tranches monthly as lots cross the 1-year mark, or immediately for risk control on a portion) balances both. The statement shows purchase lots' aging via ST/LT split - ask for the lot-wise report to sequence sales precisely.",
 "<b>Tax-loss harvesting inventory:</b> booked losses can offset gains - Ola Electric (-Rs 2.84 L, part ST), Hyundai (-Rs 36.6K ST), Bajaj Housing (-Rs 67.3K LT), Crompton (-Rs 37.9K LT), IRFC (-Rs 19.8K LT), IGL, Tata Power, Tata Motors PAX, HUL, Infosys, Cyient DLM, Kwality Walls - total roughly Rs 5.4 L of harvestable losses that can shelter part of the Eicher STCG if realised in the same FY.",
 "<b>MF redemptions:</b> Rs 3.21 Cr of LT gains means any large restructuring (e.g. Regular→Direct switches, scheme consolidation) is a taxable event at 12.5% beyond the Rs 1.25 L annual exemption. Sequence switches over multiple FYs, use the annual exemption each year, and prioritise switching the schemes with the smallest embedded gains first (e.g. Quant/Kotak Multi Asset, ICICI Value, newer folios).",
 "<b>Dividends</b> are taxed at slab; current dividend flow is negligible, so no action.",
 "<b>ULIP:</b> hold-to-maturity likely preserves Sec 10(10D) exemption (pre-2021 policy) - confirm with CA; avoid partial withdrawals that could complicate the exemption.",
]))
S.append(Spacer(1, 5))
S.append(note_box(
    "Illustrative arithmetic on the Eicher trim: selling 90% of the position (Rs 14.9 Cr) after lots turn "
    "long-term, at today's prices, would realise roughly Rs 5.9 L x 90% = ~Rs 58.5 L LT gain, taxed ~Rs 7.2 L "
    "after the Rs 1.25 L exemption - about 0.5% of the amount being de-risked. Tax is not a reason to stay "
    "concentrated.", title="Perspective"))
S.append(PageBreak())

# ============================================================ 8. RECOMMENDATIONS
S.append(Paragraph("8. Action Plan (prioritised)", styles["H1"]))
S.append(hr())
S.append(Paragraph("Priority 1 - within the next quarter", styles["H2"]))
S.extend(bullets([
 "<b>De-risk Eicher Motors.</b> Define a target weight (5-10% of wealth = Rs 1.4-2.7 Cr) and a written sell-down schedule: immediate partial sale for risk control (accepting 20% STCG on that slice), remainder in tranches as lots cross 12 months. Consider a stop-loss discipline on the retained stake. If there is an emotional/professional attachment to the stock, cap it explicitly rather than implicitly.",
 "<b>Redeploy proceeds into a real asset allocation.</b> E.g. 55-60% diversified equity (existing MF line-up can absorb it), 30-35% fixed income (target-maturity gilt/PSU funds, short-duration funds, arbitrage for <1yr money), 5-10% gold/international. This single step converts the stress-test drawdown from ~-24% to ~-10%.",
 "<b>Build the liquidity layer:</b> 12-24 months of expenses in liquid/arbitrage funds before anything else.",
 "<b>Pull the PMS statement</b> and re-run allocation including it; verify no additional auto/Eicher overlap.",
]))
S.append(Paragraph("Priority 2 - this financial year", styles["H2"]))
S.extend(bullets([
 "<b>Harvest the ~Rs 5.4 L of embedded small-stock losses</b> in the same FY as Eicher sales to offset STCG; exit the broken-thesis names outright (Ola Electric, IRFC, Kwality Walls, Crompton, Bajaj Housing if conviction is gone).",
 "<b>Prune the equity tail:</b> fold the remaining sub-Rs-3-L positions into the MF book or a single flexi-cap fund - 27 stocks for 1.4% of wealth is pure administrative drag.",
 "<b>Begin Regular→Direct migration</b> where advice isn't being paid for: start with low-gain schemes; use the Rs 1.25 L LTCG exemption annually. Estimated saving: Rs 5.5-9.5 L per year.",
 "<b>Consolidate folios:</b> 5 HDFC BAF folios → 1; 2 HDFC Large Cap → 1; 2 HDFC Hybrid Equity → 1; 2 Franklin Flexi Cap → 1. Update nominations everywhere while at it.",
]))
S.append(Paragraph("Priority 3 - structural hygiene", styles["H2"]))
S.extend(bullets([
 "Reduce two-AMC dominance (83%) as new money flows: add a third house or index funds.",
 "Retire micro-positions in the MF book (ICICI Value Rs 2.5 L, Metal ETF Rs 59 K, Groww demat units Rs 55 K) into core schemes; roll Axis ELSS into a mainstream fund once lock-in lapsed.",
 "Track Franklin segregated-portfolio recovery payouts (folio 18500483).",
 "Hold ULIP to 2035 maturity for tax-free proceeds (verify 10(10D) with CA); buy separate term cover if income protection is needed.",
 "Set an annual review: allocation vs target, XIRR vs benchmark (Nifty 50 TRI / CRISIL hybrid indices), and a one-page risk dashboard (top position %, sector %, equity %).",
]))
S.append(Spacer(1, 6))
S.append(Paragraph("What is already right (keep doing it)", styles["H2"]))
S.extend(bullets([
 "The MF core - large-cap + BAF + manufacturing - has compounded at 11.65% XIRR with real downside cushioning; position sizes are sensible and holding periods long.",
 "The ULIP's costs are sunk and it now compounds respectably tax-free - patience here is being rewarded.",
 "Winners like Samvardhana Motherson, SBI, ICICI Bank, Pricol show genuine stock-picking ability when position-sized deliberately - the skill is present; the sizing discipline is what needs to catch up.",
]))
S.append(PageBreak())

# ============================================================ 9. APPENDIX
S.append(Paragraph("9. Appendix — Source Data & Reconciliation", styles["H1"]))
S.append(hr())
S.append(Paragraph("Statement reconciliation", styles["H2"]))
rec = [
 ["Stocks (statement p.3)", inr(169789310.50), "63.39%", "Matches sum of 28 holdings (p.5-10)"],
 ["Mutual Fund - Equity (p.3)", inr(51554834.43), "19.25%", "Matches MF equity sub-total (p.14)"],
 ["Mutual Fund - Balanced (p.3)", inr(46510411.87), "17.36%", "Matches MF balanced sub-total (p.16)"],
 ["Fixed income / MF-Debt (p.3)", "0", "0.00%", "Franklin segregated units carried at nil"],
 ["ISEC portfolio total", inr(267854556.80), "100.00%", "Verified: components sum exactly"],
 ["ULIP fund value (p.18)", inr(6348403.16), "-", "Outside asset-class table"],
 ["Other demat (p.19, 30-Jun)", inr(54999), "-", "Outside asset-class table"],
 ["Grand total analysed", inr(GRAND), "-", ""],
]
S.append(data_table(["Item", "Value (Rs)", "% (ISEC book)", "Check"],
        rec, [48*mm, 34*mm, 24*mm, 64*mm], total_rows=[4,7]))
S.append(Spacer(1, 5))
S.append(Paragraph("Notes, caveats and data quality", styles["H2"]))
S.extend(bullets([
 "Figures were transcribed from 15 photographs of the PDF statement; minor OCR-level transcription risk exists. All section totals were re-computed and tie to the statement's own totals (stocks total re-verified to the rupee: Rs 16,97,89,310.50).",
 "XIRR figures are as printed by ICICI Securities; 'XIRR since inception' is position-specific money-weighted return, not scheme performance. Extreme values on tiny/young positions (e.g. Infosys -84.6%, Tata Motors +203%) reflect short holding windows.",
 "The statement notes: PMS Ace Equity Advisory AUA excluded; private equity/real-estate funds valued at drawdown cost; report 'not valid without disclaimer'. Insurance data is limited to ICICI Prudential policies shared with I-Sec - other insurers' policies, EPF/PPF, bank FDs and real estate are outside this analysis.",
 "Dividend 'received since inception' totals ~Rs 79,365 across equities; MF dividend column is nil (all growth plans - good tax hygiene).",
 "Estimated ULIP XIRR (~10.8%) computed from 5 annual premiums of Rs 5 L (2015-2019) against the 24-Jul-2026 fund value; actual XIRR depends on exact premium dates.",
 "This document is for education and discussion with a SEBI-registered investment advisor and a chartered accountant; it is not a recommendation to buy or sell any security.",
]))
S.append(Spacer(1, 8))
S.append(hr(MAROON, 1.0))
S.append(P("<b>Bottom line:</b> a Rs 27.4 crore portfolio with a well-built Rs 9.8 crore mutual-fund engine, "
           "a respectable ULIP, real stock-picking flashes - and one decision (Eicher at 60% of wealth) that "
           "currently overrides everything else. Fix the concentration and the asset allocation, harvest the "
           "tax losses while doing it, cut the fee drag, and this becomes a genuinely robust family portfolio.", "Callout"))

doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("PDF written:", OUT)
