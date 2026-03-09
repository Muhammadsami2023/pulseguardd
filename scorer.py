# scorer.py
# The brain of PulseGuard
# Takes all signals and calculates Risk Signal Score

from utils import safe_divide, get_risk_level

# ─────────────────────────────────────────
# SCORING WEIGHTS
# How much each factor affects the score
# Total must always = 100
# ─────────────────────────────────────────
WEIGHTS = {
    "liquidity":     25,   # Can they pay short-term bills?
    "profitability": 25,   # Are they making money?
    "debt":          20,   # How much do they owe?
    "cashflow":      20,   # Is cash flowing in or out?
    "price_trend":   10,   # What is market saying?
}


# ─────────────────────────────────────────
# SCORE LIQUIDITY (0-100)
# Based on current ratio
# ─────────────────────────────────────────
def score_liquidity(financials):
    cr = financials.get("current_ratio")
    
    if cr is None:
        return 50  # Neutral if no data
    
    if cr >= 2.5:
        return 100
    elif cr >= 2.0:
        return 90
    elif cr >= 1.5:
        return 75
    elif cr >= 1.2:
        return 60
    elif cr >= 1.0:
        return 45
    elif cr >= 0.7:
        return 25
    else:
        return 10


# ─────────────────────────────────────────
# SCORE PROFITABILITY (0-100)
# Based on profit margin and ROE
# ─────────────────────────────────────────
def score_profitability(financials):
    pm = financials.get("profit_margin")
    roe = financials.get("return_on_equity")
    
    if pm is None and roe is None:
        return 50  # Neutral if no data
    
    score = 50  # Start neutral
    
    # Profit margin scoring
    if pm is not None:
        if pm >= 0.20:
            score += 25
        elif pm >= 0.10:
            score += 15
        elif pm >= 0.05:
            score += 5
        elif pm >= 0:
            score -= 5
        elif pm >= -0.05:
            score -= 20
        else:
            score -= 35
    
    # Return on equity scoring
    if roe is not None:
        if roe >= 0.20:
            score += 25
        elif roe >= 0.10:
            score += 15
        elif roe >= 0.05:
            score += 5
        elif roe >= 0:
            score -= 5
        else:
            score -= 25
    
    return max(0, min(100, score))


# ─────────────────────────────────────────
# SCORE DEBT (0-100)
# Based on debt-to-equity ratio
# ─────────────────────────────────────────
def score_debt(financials):
    dte = financials.get("debt_to_equity")
    
    if dte is None:
        return 50  # Neutral if no data
    
    # Lower debt = higher score
    if dte <= 30:
        return 100
    elif dte <= 60:
        return 85
    elif dte <= 100:
        return 70
    elif dte <= 150:
        return 50
    elif dte <= 200:
        return 30
    elif dte <= 300:
        return 15
    else:
        return 5


# ─────────────────────────────────────────
# SCORE CASHFLOW (0-100)
# Based on free cashflow and operating cashflow
# ─────────────────────────────────────────
def score_cashflow(financials):
    fcf = financials.get("free_cashflow")
    ocf = financials.get("operating_cashflow")
    revenue = financials.get("revenue")
    
    if fcf is None and ocf is None:
        return 50  # Neutral if no data
    
    score = 50  # Start neutral
    
    # Free cashflow relative to revenue
    if fcf is not None and revenue is not None and revenue > 0:
        fcf_ratio = safe_divide(fcf, revenue)
        if fcf_ratio >= 0.15:
            score += 30
        elif fcf_ratio >= 0.08:
            score += 20
        elif fcf_ratio >= 0.03:
            score += 10
        elif fcf_ratio >= 0:
            score += 0
        elif fcf_ratio >= -0.05:
            score -= 20
        else:
            score -= 35
    
    # Operating cashflow check
    if ocf is not None:
        if ocf > 0:
            score += 20
        else:
            score -= 20
    
    return max(0, min(100, score))


# ─────────────────────────────────────────
# SCORE PRICE TREND (0-100)
# Based on stock price movement
# ─────────────────────────────────────────
def score_price_trend(stock_data):
    if not stock_data.get("success"):
        return 50  # Neutral if no data
    
    price_history = stock_data.get("price_history")
    
    if price_history is None or len(price_history) < 3:
        return 50
    
    try:
        closes = price_history["close"].dropna().tolist()
        
        if len(closes) < 3:
            return 50
        
        current = closes[-1]
        six_months_ago = closes[-6] if len(closes) >= 6 else closes[0]
        year_ago = closes[-12] if len(closes) >= 12 else closes[0]
        
        # 6 month change
        six_month_change = safe_divide(
            (current - six_months_ago), six_months_ago
        ) * 100
        
        # Yearly change
        yearly_change = safe_divide(
            (current - year_ago), year_ago
        ) * 100
        
        score = 50  # Start neutral
        
        # 6 month scoring
        if six_month_change >= 20:
            score += 25
        elif six_month_change >= 10:
            score += 15
        elif six_month_change >= 0:
            score += 5
        elif six_month_change >= -10:
            score -= 10
        elif six_month_change >= -25:
            score -= 25
        else:
            score -= 35
        
        # Yearly scoring
        if yearly_change >= 20:
            score += 25
        elif yearly_change >= 0:
            score += 10
        elif yearly_change >= -20:
            score -= 10
        else:
            score -= 25
        
        return max(0, min(100, score))
        
    except:
        return 50


# ─────────────────────────────────────────
# SIGNAL PENALTY
# Each warning signal reduces the score
# ─────────────────────────────────────────
def apply_signal_penalty(base_score, signals):
    penalty = 0
    
    for signal in signals:
        severity = signal.get("severity", "LOW")
        if severity == "HIGH":
            penalty += 8
        elif severity == "MEDIUM":
            penalty += 4
        elif severity == "LOW":
            penalty += 2
    
    final_score = base_score - penalty
    return max(0, min(100, final_score))


# ─────────────────────────────────────────
# MAIN SCORING FUNCTION
# This is what app.py will call
# ─────────────────────────────────────────
def calculate_risk_score(company_data):
    financials = company_data.get("financials", {})
    stock_data = company_data.get("stock", {})
    signals = company_data.get("signals", [])
    
    # Check if we have enough data
    has_financials = financials.get("success", False)
    has_stock = stock_data.get("success", False)
    
    if not has_financials and not has_stock:
        return {
            "score": None,
            "error": "Could not fetch data for this company. Please check the ticker symbol.",
            "component_scores": {},
            "risk": None
        }
    
    # ── Calculate each component score ──
    liq_score  = score_liquidity(financials)    if has_financials else 50
    prof_score = score_profitability(financials) if has_financials else 50
    debt_score = score_debt(financials)          if has_financials else 50
    cf_score   = score_cashflow(financials)      if has_financials else 50
    price_score = score_price_trend(stock_data)  if has_stock      else 50

    # ── Weighted final score ──
    base_score = (
        liq_score   * WEIGHTS["liquidity"]     / 100 +
        prof_score  * WEIGHTS["profitability"] / 100 +
        debt_score  * WEIGHTS["debt"]          / 100 +
        cf_score    * WEIGHTS["cashflow"]      / 100 +
        price_score * WEIGHTS["price_trend"]   / 100
    )

    # ── Apply signal penalties ──
    final_score = apply_signal_penalty(base_score, signals)
    final_score = round(final_score)

    # ── Get risk level ──
    risk = get_risk_level(final_score)

    return {
        "score": final_score,
        "error": None,
        "component_scores": {
            "Liquidity":     round(liq_score),
            "Profitability": round(prof_score),
            "Debt Health":   round(debt_score),
            "Cash Flow":     round(cf_score),
            "Market Trend":  round(price_score),
        },
        "weights": WEIGHTS,
        "signals": signals,
        "risk": risk,
        "penalties_applied": len(signals)
    }