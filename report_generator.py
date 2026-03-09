# report_generator.py — PulseGuard v3.0
# Professional Bank-Grade PDF Report
# DreamByte — Pakistan

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Circle, Wedge, Line
)
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from datetime import datetime
import io
import math

# ─────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#0F172A")
ACCENT_BLUE = colors.HexColor("#2563EB")
GREEN       = colors.HexColor("#16A34A")
LIGHT_GREEN = colors.HexColor("#DCFCE7")
YELLOW      = colors.HexColor("#CA8A04")
LIGHT_YELLOW= colors.HexColor("#FEF9C3")
RED         = colors.HexColor("#DC2626")
LIGHT_RED   = colors.HexColor("#FEE2E2")
LIGHT_GRAY  = colors.HexColor("#F1F5F9")
MID_GRAY    = colors.HexColor("#94A3B8")
BORDER_GRAY = colors.HexColor("#E2E8F0")
WHITE       = colors.white
BLACK       = colors.HexColor("#0F172A")

# ─────────────────────────────────────────
# SECTOR BENCHMARKS
# ─────────────────────────────────────────
SECTOR_BENCHMARKS = {
    "Cement": {
        "profit_margin":  0.082,
        "debt_to_equity": 112.4,
        "current_ratio":  1.18,
        "revenue_growth": 0.034,
    },
    "Banking": {
        "profit_margin":  0.198,
        "debt_to_equity": 780.0,
        "current_ratio":  1.12,
        "revenue_growth": 0.142,
    },
    "Oil & Gas": {
        "profit_margin":  0.224,
        "debt_to_equity": 48.2,
        "current_ratio":  1.84,
        "revenue_growth": 0.064,
    },
    "Fertilizer": {
        "profit_margin":  0.168,
        "debt_to_equity": 98.4,
        "current_ratio":  1.28,
        "revenue_growth": 0.042,
    },
    "Textile": {
        "profit_margin":  0.048,
        "debt_to_equity": 124.2,
        "current_ratio":  1.18,
        "revenue_growth": 0.028,
    },
    "Power": {
        "profit_margin":  0.098,
        "debt_to_equity": 242.4,
        "current_ratio":  0.88,
        "revenue_growth": 0.018,
    },
    "Pharmaceuticals": {
        "profit_margin":  0.138,
        "debt_to_equity": 28.4,
        "current_ratio":  2.08,
        "revenue_growth": 0.084,
    },
    "Technology": {
        "profit_margin":  0.162,
        "debt_to_equity": 22.4,
        "current_ratio":  2.42,
        "revenue_growth": 0.184,
    },
    "Consumer Goods": {
        "profit_margin":  0.108,
        "debt_to_equity": 148.2,
        "current_ratio":  1.08,
        "revenue_growth": 0.112,
    },
    "Diversified": {
        "profit_margin":  0.142,
        "debt_to_equity": 92.4,
        "current_ratio":  1.48,
        "revenue_growth": 0.068,
    },
    "Steel": {
        "profit_margin":  0.048,
        "debt_to_equity": 148.4,
        "current_ratio":  1.12,
        "revenue_growth": 0.042,
    },
    "Insurance": {
        "profit_margin":  0.118,
        "debt_to_equity": 24.4,
        "current_ratio":  1.88,
        "revenue_growth": 0.098,
    },
    "Chemicals": {
        "profit_margin":  0.078,
        "debt_to_equity": 92.4,
        "current_ratio":  1.38,
        "revenue_growth": 0.028,
    },
    "Food & Beverages": {
        "profit_margin":  0.062,
        "debt_to_equity": 168.4,
        "current_ratio":  1.04,
        "revenue_growth": 0.142,
    },
}

def get_benchmark(sector):
    return SECTOR_BENCHMARKS.get(sector, {
        "profit_margin":  0.12,
        "debt_to_equity": 100.0,
        "current_ratio":  1.5,
        "revenue_growth": 0.05,
    })


def get_risk_color(score):
    if score >= 70:   return GREEN
    elif score >= 40: return YELLOW
    else:             return RED


def get_risk_label(score):
    if score >= 70:   return "LOW RISK"
    elif score >= 40: return "MEDIUM RISK"
    else:             return "HIGH RISK"


def format_pkr(value):
    if not value:
        return "N/A"
    if value >= 1_000_000_000:
        return f"PKR {value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"PKR {value/1_000_000:.1f}M"
    return f"PKR {value:,.0f}"


def compare(company_val, benchmark_val, higher_is_better=True):
    if not company_val or not benchmark_val:
        return "N/A", MID_GRAY
    if higher_is_better:
        if company_val >= benchmark_val * 1.05:
            return "Above Average", GREEN
        elif company_val >= benchmark_val * 0.95:
            return "In Line",       YELLOW
        else:
            return "Below Average", RED
    else:
        if company_val <= benchmark_val * 0.95:
            return "Better",        GREEN
        elif company_val <= benchmark_val * 1.05:
            return "In Line",       YELLOW
        else:
            return "Worse",         RED


# ─────────────────────────────────────────
# RISK GAUGE DRAWING
# ─────────────────────────────────────────
def build_gauge(score):
    d = Drawing(120, 75)

    cx, cy, r = 60, 20, 45

    # Background arc segments
    segments = [
        (0,   40,  RED),
        (40,  70,  YELLOW),
        (70,  100, GREEN),
    ]
    for lo, hi, col in segments:
        start_angle = 180 - (lo / 100) * 180
        end_angle   = 180 - (hi / 100) * 180
        w = Wedge(cx, cy, r, end_angle, start_angle,
                  radius1=r*0.55)
        w.fillColor    = col
        w.strokeColor  = WHITE
        w.strokeWidth  = 1
        d.add(w)

    # Needle
    needle_angle = math.radians(180 - (score / 100) * 180)
    nx = cx + (r * 0.75) * math.cos(needle_angle)
    ny = cy + (r * 0.75) * math.sin(needle_angle)
    needle = Line(cx, cy, nx, ny)
    needle.strokeColor = DARK_BLUE
    needle.strokeWidth = 2.5
    d.add(needle)

    # Center dot
    dot = Circle(cx, cy, 5)
    dot.fillColor   = DARK_BLUE
    dot.strokeColor = WHITE
    dot.strokeWidth = 1
    d.add(dot)

    # Score text
    score_txt = String(cx, cy - 22, str(score),
                       fontSize=18, fontName="Helvetica-Bold",
                       fillColor=get_risk_color(score),
                       textAnchor="middle")
    d.add(score_txt)

    label_txt = String(cx, cy - 34, get_risk_label(score),
                       fontSize=7, fontName="Helvetica-Bold",
                       fillColor=get_risk_color(score),
                       textAnchor="middle")
    d.add(label_txt)

    # Labels
    for label, x, y in [("HIGH", 8, 22), ("MED", 57, 68), ("LOW", 105, 22)]:
        t = String(x, y, label, fontSize=6,
                   fontName="Helvetica",
                   fillColor=MID_GRAY,
                   textAnchor="middle")
        d.add(t)

    return d


# ─────────────────────────────────────────
# PRICE CHART DRAWING
# ─────────────────────────────────────────
def build_price_chart(price_history):
    if price_history is None or len(price_history) < 3:
        return None

    closes = price_history["close"].dropna().tolist()
    if len(closes) < 3:
        return None

    d       = Drawing(170*mm, 55*mm)
    w, h    = 170*mm, 55*mm
    pad_l   = 12*mm
    pad_r   = 4*mm
    pad_t   = 4*mm
    pad_b   = 8*mm
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b

    min_p = min(closes)
    max_p = max(closes)
    rng   = max_p - min_p if max_p != min_p else 1

    def px(i):
        return pad_l + (i / (len(closes) - 1)) * chart_w

    def py(v):
        return pad_b + ((v - min_p) / rng) * chart_h

    # Grid lines
    for i in range(4):
        y_val = min_p + (rng / 3) * i
        y_pos = py(y_val)
        gl = Line(pad_l, y_pos, w - pad_r, y_pos)
        gl.strokeColor = colors.HexColor("#E2E8F0")
        gl.strokeWidth = 0.5
        d.add(gl)

        lbl = String(pad_l - 1*mm, y_pos - 2,
                     f"{y_val:,.0f}",
                     fontSize=5, fontName="Helvetica",
                     fillColor=MID_GRAY,
                     textAnchor="end")
        d.add(lbl)

    # Line
    for i in range(len(closes) - 1):
        x1, y1 = px(i),   py(closes[i])
        x2, y2 = px(i+1), py(closes[i+1])
        ln = Line(x1, y1, x2, y2)
        ln.strokeColor = ACCENT_BLUE
        ln.strokeWidth = 1.5
        d.add(ln)

    # Current price dot
    last_x = px(len(closes) - 1)
    last_y = py(closes[-1])
    dot = Circle(last_x, last_y, 3)
    dot.fillColor   = GREEN
    dot.strokeColor = WHITE
    dot.strokeWidth = 1
    d.add(dot)

    # X-axis labels
    n = len(closes)
    for idx in [0, n//4, n//2, 3*n//4, n-1]:
        if idx < n:
            lbl = String(px(idx), pad_b - 5,
                         f"M{idx+1}",
                         fontSize=5, fontName="Helvetica",
                         fillColor=MID_GRAY,
                         textAnchor="middle")
            d.add(lbl)

    return d


# ─────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────
def generate_risk_report(
    ticker, company_name, score,
    score_result, company_data,
    loan_amount=None, loan_duration=None
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm,   bottomMargin=16*mm
    )

    styles = getSampleStyleSheet()
    story  = []

    def S(name, size, bold=False, color=BLACK,
          align=TA_LEFT, sa=3, sb=0):
        return ParagraphStyle(
            name,
            parent=styles["Normal"],
            fontSize=size,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            textColor=color,
            alignment=align,
            spaceAfter=sa,
            spaceBefore=sb,
            leading=size * 1.45,
        )

    T_title    = S("t1", 20, bold=True,  color=WHITE,       align=TA_CENTER)
    T_sub      = S("t2",  9, bold=False, color=colors.HexColor("#93C5FD"), align=TA_CENTER)
    T_section  = S("t3", 10, bold=True,  color=ACCENT_BLUE, sb=6)
    T_normal   = S("t4",  8, bold=False, color=BLACK)
    T_bold     = S("t5",  8, bold=True,  color=BLACK)
    T_small    = S("t6",  7, bold=False, color=MID_GRAY)
    T_center   = S("t7",  8, bold=False, color=BLACK,       align=TA_CENTER)
    T_score_sub= S("t8",  7, bold=False, color=MID_GRAY,    align=TA_CENTER)
    T_disc     = S("t9",  6, bold=False, color=MID_GRAY,    align=TA_CENTER)
    T_rec_title= S("t10",10, bold=True,  color=get_risk_color(score))
    T_rec_body = S("t11", 8, bold=False, color=BLACK)
    T_green    = S("t12", 8, bold=True,  color=GREEN)
    T_red      = S("t13", 8, bold=True,  color=RED)
    T_yellow   = S("t14", 8, bold=True,  color=YELLOW)

    fins  = company_data.get("financials", {})
    stock = company_data.get("stock",      {})
    now   = datetime.now().strftime("%d %B %Y, %H:%M")
    sector= fins.get("sector", "Diversified")
    bench = get_benchmark(sector)

    # ══════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════
    hdr = Table([
        [Paragraph("PulseGuard", T_title)],
        [Paragraph(
            "AI-Powered Loan Risk Assessment Report — Pakistan Stock Exchange",
            T_sub
        )],
    ], colWidths=[174*mm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), DARK_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 4*mm))

    # ── Info row ──
    info = Table([[
        Paragraph(f"<b>Company:</b> {company_name} ({ticker})", T_normal),
        Paragraph(f"<b>Generated:</b> {now}",                   T_normal),
        Paragraph(f"<b>Sector:</b> {sector}",                   T_normal),
        Paragraph("<b>By:</b> PulseGuard / DreamByte",          T_normal),
    ]], colWidths=[52*mm, 48*mm, 38*mm, 42*mm])
    info.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("LINEAFTER",     (0,0), (2,-1),  0.5, BORDER_GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(info)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # SCORE GAUGE + METRICS
    # ══════════════════════════════════════
    cr  = fins.get("current_ratio")
    dte = fins.get("debt_to_equity")
    pm  = fins.get("profit_margin")
    pr  = stock.get("current_price")
    mc  = fins.get("market_cap")
    rev = fins.get("revenue")
    rg  = fins.get("revenue_growth")

    gauge = build_gauge(score)

    gauge_cell = Table([
        [Paragraph("Risk Signal Score", T_score_sub)],
        [gauge],
        [Paragraph("out of 100", T_score_sub)],
    ], colWidths=[55*mm])
    gauge_cell.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))

    metrics_rows = [
        [Paragraph("Metric",        T_bold),
         Paragraph("Value",         T_bold),
         Paragraph("Sector Avg",    T_bold),
         Paragraph("Status",        T_bold)],
        [Paragraph("Current Ratio", T_normal),
         Paragraph(f"{cr:.2f}"      if cr  else "N/A", T_normal),
         Paragraph(f"{bench['current_ratio']:.2f}", T_normal),
         Paragraph(*compare(cr, bench["current_ratio"], True)[:1],
                   S("x1", 8, bold=True,
                     color=compare(cr, bench["current_ratio"], True)[1]))],
        [Paragraph("Debt/Equity",   T_normal),
         Paragraph(f"{dte:.1f}%"    if dte else "N/A", T_normal),
         Paragraph(f"{bench['debt_to_equity']:.1f}%", T_normal),
         Paragraph(*compare(dte, bench["debt_to_equity"], False)[:1],
                   S("x2", 8, bold=True,
                     color=compare(dte, bench["debt_to_equity"], False)[1]))],
        [Paragraph("Profit Margin", T_normal),
         Paragraph(f"{pm*100:.1f}%" if pm  else "N/A", T_normal),
         Paragraph(f"{bench['profit_margin']*100:.1f}%", T_normal),
         Paragraph(*compare(pm, bench["profit_margin"], True)[:1],
                   S("x3", 8, bold=True,
                     color=compare(pm, bench["profit_margin"], True)[1]))],
        [Paragraph("Revenue Growth",T_normal),
         Paragraph(f"{rg*100:.1f}%" if rg  else "N/A", T_normal),
         Paragraph(f"{bench['revenue_growth']*100:.1f}%", T_normal),
         Paragraph(*compare(rg, bench["revenue_growth"], True)[:1],
                   S("x4", 8, bold=True,
                     color=compare(rg, bench["revenue_growth"], True)[1]))],
        [Paragraph("Live Price",    T_normal),
         Paragraph(f"PKR {pr:,.0f}" if pr  else "N/A", T_normal),
         Paragraph("—", T_normal),
         Paragraph("—", T_normal)],
        [Paragraph("Market Cap",    T_normal),
         Paragraph(format_pkr(mc),  T_normal),
         Paragraph("—", T_normal),
         Paragraph("—", T_normal)],
        [Paragraph("Revenue",       T_normal),
         Paragraph(format_pkr(rev), T_normal),
         Paragraph("—", T_normal),
         Paragraph("—", T_normal)],
    ]

    metrics_tbl = Table(
        metrics_rows,
        colWidths=[32*mm, 28*mm, 28*mm, 28*mm]
    )
    metrics_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  DARK_BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
    ]))

    top_row = Table(
        [[gauge_cell, metrics_tbl]],
        colWidths=[58*mm, 116*mm]
    )
    top_row.setStyle(TableStyle([
        ("BOX",           (0,0), (-1,-1), 1, BORDER_GRAY),
        ("LINEAFTER",     (0,0), (0,-1),  1, BORDER_GRAY),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND",    (0,0), (0,-1),  LIGHT_GRAY),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(top_row)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # PRICE CHART
    # ══════════════════════════════════════
    price_history = stock.get("price_history")
    chart = build_price_chart(price_history)

    if chart:
        story.append(Paragraph(
            "Stock Price Trend — 24 Months", T_section
        ))

        chart_tbl = Table([[chart]], colWidths=[174*mm])
        chart_tbl.setStyle(TableStyle([
            ("BOX",           (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ("BACKGROUND",    (0,0), (-1,-1), WHITE),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ]))
        story.append(chart_tbl)

        # Price insight
        closes = price_history["close"].dropna().tolist()
        if len(closes) >= 6:
            six_m_chg = ((closes[-1] - closes[-6]) / closes[-6]) * 100
            yr_chg    = ((closes[-1] - closes[-12]) / closes[-12]) * 100 \
                        if len(closes) >= 12 else None

            insight = (
                f"{ticker} stock "
                f"{'declined' if six_m_chg < 0 else 'gained'} "
                f"{abs(six_m_chg):.1f}% over the past 6 months"
            )
            if yr_chg is not None:
                insight += (
                    f", and "
                    f"{'declined' if yr_chg < 0 else 'gained'} "
                    f"{abs(yr_chg):.1f}% over the past 12 months"
                )
            insight += (
                f". Current price: PKR {closes[-1]:,.0f}. "
                + ("Negative market sentiment detected."
                   if six_m_chg < -10 else
                   "Moderate price pressure observed."
                   if six_m_chg < 0 else
                   "Positive price momentum.")
            )

            ins_col = RED if six_m_chg < -10 else \
                      YELLOW if six_m_chg < 0 else GREEN
            ins_style = S("ins", 7, bold=False, color=ins_col)
            story.append(Spacer(1, 1*mm))
            story.append(Paragraph(f"Insight: {insight}", ins_style))

        story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # COMPONENT SCORES + RISK SIGNALS
    # ══════════════════════════════════════
    comp    = score_result.get("component_scores", {})
    signals = company_data.get("signals", [])

    comp_rows = [[
        Paragraph("Component", T_bold),
        Paragraph("Score",     T_bold),
        Paragraph("Status",    T_bold),
    ]]
    for component, val in comp.items():
        if val >= 70:
            st_txt = "Good"
            st_col = GREEN
        elif val >= 40:
            st_txt = "Caution"
            st_col = YELLOW
        else:
            st_txt = "At Risk"
            st_col = RED
        comp_rows.append([
            Paragraph(component, T_normal),
            Paragraph(str(val),  T_center),
            Paragraph(st_txt,    S(f"cs{val}", 8, bold=True, color=st_col, align=TA_CENTER)),
        ])

    comp_tbl = Table(comp_rows, colWidths=[45*mm, 20*mm, 20*mm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  DARK_BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
        ("RIGHTPADDING",  (0,0), (-1,-1), 7),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0), (2,-1),  "CENTER"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
    ]))

    # Signals table
    if signals:
        sev_colors_map = {
            "HIGH":   LIGHT_RED,
            "MEDIUM": LIGHT_YELLOW,
            "LOW":    LIGHT_GREEN,
        }
        sig_rows = [[
            Paragraph("Sev.",   T_bold),
            Paragraph("Signal", T_bold),
        ]]
        sig_style_list = [
            ("BACKGROUND",    (0,0), (-1,0),  DARK_BLUE),
            ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("GRID",          (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 7),
            ("RIGHTPADDING",  (0,0), (-1,-1), 7),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
        ]
        for i, sig in enumerate(signals, start=1):
            sev = sig.get("severity", "LOW")
            sig_rows.append([
                Paragraph(sev,                    T_bold),
                Paragraph(
                    f"{sig.get('message','')}\n{sig.get('detail','')}",
                    T_small
                ),
            ])
            sig_style_list.append((
                "BACKGROUND", (0,i), (-1,i),
                sev_colors_map.get(sev, WHITE)
            ))

        sig_tbl = Table(sig_rows, colWidths=[16*mm, 73*mm])
        sig_tbl.setStyle(TableStyle(sig_style_list))
    else:
        sig_tbl = Table([[
            Paragraph("No risk signals detected.", T_normal)
        ]], colWidths=[89*mm])

    mid_row = Table(
        [[
            Table([
                [Paragraph("Component Scores", T_section)],
                [comp_tbl]
            ], colWidths=[85*mm]),
            Spacer(4*mm, 1),
            Table([
                [Paragraph("Risk Signals Detected", T_section)],
                [sig_tbl]
            ], colWidths=[89*mm]),
        ]],
        colWidths=[85*mm, 4*mm, 89*mm]
    )
    mid_row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(mid_row)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # KEY RISK FACTORS
    # ══════════════════════════════════════
    story.append(Paragraph("Key Risk Factors", T_section))

    risk_factors = []
    if signals:
        for sig in signals:
            risk_factors.append(f"- {sig.get('message','')}")
    if not risk_factors:
        risk_factors.append("- No major risk factors identified at this time")

    # Add sector context
    risk_factors.append(
        f"- {sector} sector: average D/E {bench['debt_to_equity']:.0f}%, "
        f"profit margin {bench['profit_margin']*100:.1f}%"
    )

    rf_text = "\n".join(risk_factors)
    rf_para = Paragraph(rf_text.replace("\n", "<br/>"), T_normal)

    rf_tbl = Table([[rf_para]], colWidths=[174*mm])
    rf_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_RED),
        ("BOX",           (0,0), (-1,-1), 1, RED),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    story.append(rf_tbl)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # LOAN DETAILS + SUGGESTED CONDITIONS
    # ══════════════════════════════════════
    if loan_amount or loan_duration:

        # Suggested conditions based on score
        if score >= 70:
            conditions = [
                "Standard collateral coverage: 110%",
                f"Financial covenant: Debt/Equity below {bench['debt_to_equity']*1.2:.0f}%",
                "Monitoring frequency: Quarterly",
                "Interest rate: Standard rate applicable",
            ]
        elif score >= 40:
            conditions = [
                "Minimum collateral coverage: 130%",
                f"Financial covenant: Debt/Equity below {bench['debt_to_equity']:.0f}%",
                "Monitoring frequency: Monthly",
                "Trigger clause: Score drop below 40 requires review",
            ]
        else:
            conditions = [
                "Minimum collateral coverage: 160%",
                "Senior credit committee approval required",
                "Monitoring frequency: Bi-weekly",
                "Personal guarantee from directors required",
                "Trigger clause: Immediate review if score drops further",
            ]

        loan_left = Table([
            [Paragraph("Loan Details", T_section)],
            [Table([
                [Paragraph("Loan Amount",     T_bold),
                 Paragraph(format_pkr(loan_amount) if loan_amount else "N/A", T_normal)],
                [Paragraph("Duration",        T_bold),
                 Paragraph(f"{loan_duration} months" if loan_duration else "N/A", T_normal)],
                [Paragraph("Assessment Date", T_bold),
                 Paragraph(datetime.now().strftime("%d %B %Y"), T_normal)],
                [Paragraph("Assessed By",     T_bold),
                 Paragraph("PulseGuard Risk Engine v2.0", T_normal)],
            ], colWidths=[35*mm, 45*mm],
            style=TableStyle([
                ("ROWBACKGROUNDS", (0,0), (-1,-1), [LIGHT_GRAY, WHITE]),
                ("GRID",          (0,0), (-1,-1), 0.5, BORDER_GRAY),
                ("TOPPADDING",    (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("LEFTPADDING",   (0,0), (-1,-1), 7),
                ("RIGHTPADDING",  (0,0), (-1,-1), 7),
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
            ]))],
        ], colWidths=[80*mm])

        cond_items = "\n".join([f"- {c}" for c in conditions])
        cond_para  = Paragraph(
            cond_items.replace("\n", "<br/>"), T_normal
        )
        loan_right = Table([
            [Paragraph("Suggested Credit Conditions", T_section)],
            [Table([[cond_para]], colWidths=[90*mm],
                   style=TableStyle([
                       ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GREEN),
                       ("BOX",           (0,0), (-1,-1), 1, GREEN),
                       ("TOPPADDING",    (0,0), (-1,-1), 8),
                       ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                       ("LEFTPADDING",   (0,0), (-1,-1), 10),
                       ("RIGHTPADDING",  (0,0), (-1,-1), 10),
                   ]))],
        ], colWidths=[94*mm])

        loan_row = Table(
            [[loan_left, Spacer(4*mm,1), loan_right]],
            colWidths=[80*mm, 4*mm, 90*mm]
        )
        loan_row.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
            ("TOPPADDING",    (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(loan_row)
        story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # MONITORING ALERTS
    # ══════════════════════════════════════
    story.append(Paragraph("Monitoring Alerts Enabled", T_section))

    mon_items = [
        "Stock price monitoring — weekly PSX data refresh",
        "Debt ratio change alerts — triggers if D/E increases over 20%",
        "Profit margin deterioration alerts — triggers if margin drops below 5%",
        "Score drop alert — triggers if Risk Signal Score drops by 10+ points",
        "Critical alert — triggers if score falls below 40",
    ]
    mon_text = "\n".join([f"✓  {m}" for m in mon_items])
    mon_para = Paragraph(mon_text.replace("\n", "<br/>"), T_normal)

    mon_tbl = Table([[mon_para]], colWidths=[174*mm])
    mon_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GRAY),
        ("BOX",           (0,0), (-1,-1), 1, ACCENT_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    story.append(mon_tbl)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # FINAL RECOMMENDATION
    # ══════════════════════════════════════
    rec_map = {
        "LOW":      ("LOAN RECOMMENDED",
                     "Company demonstrates stable financial health "
                     "with strong fundamentals. Loan can be approved "
                     "under standard terms with quarterly monitoring.",
                     "Approved"),
        "MEDIUM":   ("PROCEED WITH CAUTION",
                     "Company shows moderate risk signals. "
                     "Recommended to proceed with additional collateral, "
                     "tighter covenants and monthly monitoring.",
                     "Approved with Conditions"),
        "HIGH":     ("HIGH RISK — EXTRA DUE DILIGENCE REQUIRED",
                     "Multiple risk signals detected. Senior credit "
                     "committee review required. Additional security "
                     "and personal guarantees recommended.",
                     "Conditional — Committee Review Required"),
        "CRITICAL": ("NOT RECOMMENDED",
                     "Critical risk signals detected across multiple "
                     "financial dimensions. Loan not recommended "
                     "without significant additional security.",
                     "Not Recommended"),
    }

    risk_lvl = get_risk_label(score).replace(" RISK", "")
    rec_title, rec_body, lending_rec = rec_map.get(
        risk_lvl, rec_map["MEDIUM"]
    )

    rec_tbl = Table([
        [Paragraph("PulseGuard Credit Recommendation", T_section),
         Paragraph(""),
         Paragraph(""),
         Paragraph("")],
        [Paragraph(f"Risk Level: {get_risk_label(score)}",
                   S("rl", 9, bold=True, color=get_risk_color(score))),
         Paragraph(""),
         Paragraph("Lending Recommendation:",
                   S("lr1", 8, bold=True, color=BLACK)),
         Paragraph(lending_rec,
                   S("lr2", 9, bold=True, color=get_risk_color(score)))],
        [Paragraph(rec_body, T_rec_body),
         Paragraph(""),
         Paragraph(""),
         Paragraph("")],
    ], colWidths=[80*mm, 10*mm, 42*mm, 42*mm])

    rec_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GRAY),
        ("BOX",           (0,0), (-1,-1), 2, get_risk_color(score)),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("SPAN",          (0,0), (3,0)),
        ("SPAN",          (0,2), (3,2)),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
    ]))
    story.append(rec_tbl)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════
    # DATA FRESHNESS + FOOTER
    # ══════════════════════════════════════
    freshness = Table([[
        Paragraph(
            f"<b>Data Freshness:</b>  "
            f"Financial data: 31 Dec 2025 (PSX Annual Reports)  |  "
            f"Market data: {datetime.now().strftime('%d %B %Y')} (Yahoo Finance PSX)  |  "
            f"Data Quality Score: {company_data.get('data_quality', 100)}%",
            T_small
        )
    ]], colWidths=[174*mm])
    freshness.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER_GRAY),
    ]))
    story.append(freshness)
    story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=BORDER_GRAY
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "This report is generated by PulseGuard, an AI-powered risk intelligence "
        "platform by DreamByte. Risk signals are for informational purposes only "
        "and do not constitute financial advice. The bank is solely responsible "
        "for all credit decisions. Data sourced from Pakistan Stock Exchange "
        "official filings and Yahoo Finance.",
        T_disc
    ))
    story.append(Spacer(1, 1*mm))
    story.append(Paragraph(
        f"PulseGuard v3.0  |  DreamByte  |  Generated {now}  |  "
        "Confidential — For Internal Bank Use Only",
        T_disc
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer