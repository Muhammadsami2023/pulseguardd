# utils.py
# Helper functions for PulseGuard

import datetime

# ─────────────────────────────────────────
# RISK LEVEL CALCULATOR
# Takes a score (0-100) and returns
# the risk level, color, and emoji
# ─────────────────────────────────────────
def get_risk_level(score):
    if score >= 70:
        return {
            "level": "LOW RISK",
            "color": "#FFFFFF",
            "bg": "#14532D",
            "emoji": "🟢",
            "recommendation": "Company shows strong financial health. Loan can be considered."
        }
    elif score >= 40:
        return {
            "level": "MEDIUM RISK",
            "color": "#FFFFFF",
            "bg": "#713F12",
            "emoji": "🟡",
            "recommendation": "Company shows some warning signals. Proceed with caution and extra due diligence."
        }
    elif score >= 20:
        return {
            "level": "HIGH RISK",
            "color": "#FFFFFF",
            "bg": "#7F1D1D",
            "emoji": "🔴",
            "recommendation": "Significant risk signals detected. Senior approval recommended."
        }
    else:
        return {
            "level": "CRITICAL RISK",
            "color": "#FFFFFF",
            "bg": "#450A0A",
            "emoji": "🚨",
            "recommendation": "Critical risk. Loan not recommended."
        }


# ─────────────────────────────────────────
# DATE HELPER
# Returns today's date as clean string
# ─────────────────────────────────────────
def get_today():
    return datetime.datetime.now().strftime("%d %B %Y")


# ─────────────────────────────────────────
# SCORE CHANGE DETECTOR
# Tells us if score is going up or down
# ─────────────────────────────────────────
def get_score_trend(old_score, new_score):
    diff = new_score - old_score
    if diff > 5:
        return f"⬆️ Improved by {diff} points"
    elif diff < -5:
        return f"⬇️ Declined by {abs(diff)} points — Monitor Closely"
    else:
        return f"➡️ Stable (change of {diff} points)"


# ─────────────────────────────────────────
# FORMAT CURRENCY
# Converts numbers to readable PKR format
# ─────────────────────────────────────────
def format_pkr(amount):
    if amount is None:
        return "N/A"
    try:
        amount = float(amount)
        if abs(amount) >= 1_000_000_000:
            return f"PKR {amount/1_000_000_000:.2f} Billion"
        elif abs(amount) >= 1_000_000:
            return f"PKR {amount/1_000_000:.2f} Million"
        else:
            return f"PKR {amount:,.0f}"
    except:
        return "N/A"


# ─────────────────────────────────────────
# SAFE DIVIDE
# Prevents division by zero errors
# ─────────────────────────────────────────
def safe_divide(numerator, denominator):
    try:
        if denominator == 0 or denominator is None:
            return 0
        return numerator / denominator
    except:
        return 0


# ─────────────────────────────────────────
# PSX LISTED COMPANIES
# Our initial list of companies we support
# ─────────────────────────────────────────
PSX_COMPANIES = {
    # ── BANKING ──
    "HBL":    "Habib Bank Limited",
    "UBL":    "United Bank Limited",
    "MCB":    "MCB Bank Limited",
    "NBP":    "National Bank of Pakistan",
    "ABL":    "Allied Bank Limited",
    "BAFL":   "Bank Alfalah Limited",
    "MEBL":   "Meezan Bank Limited",
    "BAHL":   "Bank Al Habib Limited",
    "AKBL":   "Askari Bank Limited",
    "FABL":   "Faysal Bank Limited",

    # ── OIL & GAS ──
    "OGDC":   "Oil & Gas Development Company",
    "PPL":    "Pakistan Petroleum Limited",
    "PSO":    "Pakistan State Oil",
    "MARI":   "Mari Petroleum Company",
    "POL":    "Pakistan Oilfields Limited",
    "HASCOL": "Hascol Petroleum Limited",

    # ── CEMENT ──
    "LUCK":   "Lucky Cement",
    "MLCF":   "Maple Leaf Cement",
    "DGKC":   "D.G. Khan Cement",
    "ACPL":   "Attock Cement",
    "PIOC":   "Pioneer Cement",
    "KOHC":   "Kohat Cement",
    "CHCC":   "Cherat Cement",
    "FCCL":   "Fauji Cement Company",

    # ── FERTILIZER ──
    "FFC":    "Fauji Fertilizer Company",
    "FFBL":   "Fauji Fertilizer Bin Qasim",
    "ENGRO":  "Engro Corporation",
    "EFERT":  "Engro Fertilizers Limited",

    # ── POWER ──
    "HUBC":   "Hub Power Company",
    "KAPCO":  "Kot Addu Power Company",
    "NCPL":   "Nishat Chunian Power",
    "NPL":    "Nishat Power Limited",
    "KEL":    "K-Electric Limited",

    # ── TEXTILE ──
    "NML":    "Nishat Mills Limited",
    "NCL":    "Nishat Chunian Limited",
    "GATM":   "Gul Ahmed Textile Mills",
    "KTML":   "Kohinoor Textile Mills",
    "ADMM":   "Adamjee Insurance",

    # ── FOOD & BEVERAGES ──
    "NESTLE": "Nestle Pakistan",
    "CBL": "Continental Biscuits Limited",
    "UNITY": "Unity Foods",
    "UNITY":  "Unity Foods",
    "TREET":  "Treet Corporation",
    "QUICE":  "Quice Food Industries",

    # ── PHARMA ──
    "SEARL":  "The Searle Company",
    "GLAXO":  "GlaxoSmithKline Pakistan",
    "ABOT":   "Abbott Laboratories Pakistan",
    "FEROZ":  "Ferozsons Laboratories",

    # ── CHEMICALS & CONSUMER ──
    "ICI":    "ICI Pakistan",
    "COLG":   "Colgate Palmolive Pakistan",
    "UNILEVER": "Unilever Pakistan",

    # ── TELECOM ──
    "TRG":    "TRG Pakistan Limited",
    "SYS":    "Systems Limited",
    "NETSOL": "NetSol Technologies",

    # ── DIVERSIFIED ──
    "DAWH":   "Dawood Hercules Corporation",
    "DSFL":   "Dewan Sugar Mills",

    # ── CEMENT (Additional) ──
    "CHCC":    "Cherat Cement",
    "FCCL":    "Fauji Cement Company",
    "POWER":   "Power Cement",
    "BWCL":    "Bestway Cement",
    # ── OIL & GAS (Additional) ──
    "HASCOL":  "Hascol Petroleum",
    "APL":     "Attock Petroleum",
    "SHEL":    "Shell Pakistan",
    "ATRL":    "Attock Refinery",
    "NRL":     "National Refinery",
    # ── POWER (Additional) ──
    "NCPL":    "Nishat Chunian Power",
    "NPL":     "Nishat Power Limited",
    "LALPIR":  "Lalpir Power",
    # ── TEXTILE (Additional) ──
    "NCL":     "Nishat Chunian Limited",
    "KTML":    "Kohinoor Textile Mills",
    "CRTM":    "Crescent Textile Mills",
    # ── PHARMA (Additional) ──
    "FEROZ":   "Ferozsons Laboratories",
    "HINOON":  "Highnoon Laboratories",
    "SAPL":    "Sanofi-Aventis Pakistan",
    # ── TECHNOLOGY (Additional) ──
    "NETSOL":  "NetSol Technologies",
    "TRG":     "TRG Pakistan",
    # ── CONSUMER GOODS ──
    "PAKT":    "Pakistan Tobacco Company",
    "WAVE":    "Wave Foods",
    "TREET":   "Treet Corporation",
    "UNILEVER":"Unilever Pakistan",
    # ── FOOD ──
    "QUICE":   "Quice Food Industries",
    # ── INSURANCE ──
    "ADMM":    "Adamjee Insurance",
    "EFU":     "EFU General Insurance",
    "JLICL":   "Jubilee Life Insurance",
    "AICL":    "Adamjee Insurance Company",
    # ── STEEL ──
    "MUGHAL":  "Mughal Iron & Steel",
    "ISL":     "International Steels",
    "ASTL":    "Amreli Steels",
    # ── TRANSPORT ──
    "PNSC":    "Pakistan National Shipping",
    # ── CHEMICALS (Additional) ──
    "LOTCHEM": "Lotte Chemical Pakistan",
    "EPCL":    "Engro Polymer & Chemicals",
    # ── PAPER ──
    "PKGS":    "Packages Limited",
    "PAPER":   "Security Papers Limited",
}


def get_company_name(ticker):
    return PSX_COMPANIES.get(ticker.upper(), ticker.upper())


def get_all_tickers():
    return list(PSX_COMPANIES.keys())