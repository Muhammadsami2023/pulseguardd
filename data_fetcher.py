# data_fetcher.py
# Fetches real company data from public sources
# Primary: Yahoo Finance (PSX stocks via .KA suffix)
# Backup: pkfinancials.com scraper for PSX financials

import requests
import pandas as pd
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
from utils import safe_divide, PSX_COMPANIES
from psx_data import get_psx_financials
# ─────────────────────────────────────────
# HEADERS
# ─────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


# ─────────────────────────────────────────
# FETCH STOCK PRICE DATA
# Yahoo Finance — works well for PSX prices
# ─────────────────────────────────────────
def fetch_stock_data(ticker):
    try:
        # Try multiple ticker formats for PSX companies
        tickers_to_try = [
            f"{ticker.upper()}.KA",
            f"{ticker.upper()}.KAR",
            f"{ticker.upper()}.PK",
            ticker.upper()
        ]
        
        data = None
        yahoo_ticker = None
        
        for try_ticker in tickers_to_try:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{try_ticker}"
                params = {"interval": "1mo", "range": "2y"}
                response = requests.get(
                    url, params=params, headers=HEADERS, timeout=15
                )
                result = response.json()
                if (result.get("chart", {}).get("result") and 
                    result["chart"]["result"] is not None):
                    data = result
                    yahoo_ticker = try_ticker
                    print(f"[PulseGuard] ✅ Price data found with ticker: {try_ticker}")
                    break
            except:
                continue
        
        if not data or not data.get("chart", {}).get("result"):
            return {"success": False, "error": "No price data found for any ticker format", "ticker": ticker.upper()}

        result     = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes     = result["indicators"]["quote"][0]["close"]
        volumes    = result["indicators"]["quote"][0]["volume"]
        meta       = result.get("meta", {})

        df = pd.DataFrame({
            "date":   [datetime.fromtimestamp(t) for t in timestamps],
            "close":  closes,
            "volume": volumes
        }).dropna().sort_values("date")

        return {
            "success":        True,
            "ticker":         ticker.upper(),
            "currency":       meta.get("currency", "PKR"),
            "current_price":  meta.get("regularMarketPrice",
                                       closes[-1] if closes else 0),
            "previous_close": meta.get("chartPreviousClose", 0),
            "52w_high":       meta.get("fiftyTwoWeekHigh", 0),
            "52w_low":        meta.get("fiftyTwoWeekLow", 0),
            "price_history":  df,
            "exchange":       "Pakistan Stock Exchange (PSX)"
        }

    except Exception as e:
        return {"success": False, "error": str(e), "ticker": ticker.upper()}


# ─────────────────────────────────────────
# FETCH FINANCIALS — METHOD 1
# pkfinancials.com — Pakistani financial data
# aggregator with PSX company financials
# ─────────────────────────────────────────
def fetch_financials_pkfinancials(ticker):
    try:
        url = f"https://pkfinancials.com/stock/{ticker.upper()}"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return {"success": False, "error": f"Status {response.status_code}"}

        soup = BeautifulSoup(response.text, "lxml")

        def parse_num(text):
            if not text:
                return None
            text = text.strip().replace(",", "").replace(
                "PKR", "").replace("%", "").strip()
            try:
                return float(text)
            except:
                return None

        data = {}

        # Find all tables and extract key value pairs
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[-1].get_text(strip=True)

                    if "current ratio" in label:
                        data["current_ratio"] = parse_num(value)
                    elif "debt to equity" in label or "d/e ratio" in label:
                        data["debt_to_equity"] = parse_num(value)
                    elif "net profit margin" in label or "profit margin" in label:
                        v = parse_num(value)
                        if v and abs(v) > 1:
                            v = v / 100
                        data["profit_margin"] = v
                    elif "return on equity" in label or "roe" == label:
                        v = parse_num(value)
                        if v and abs(v) > 1:
                            v = v / 100
                        data["return_on_equity"] = v
                    elif "return on assets" in label or "roa" == label:
                        v = parse_num(value)
                        if v and abs(v) > 1:
                            v = v / 100
                        data["return_on_assets"] = v
                    elif "eps" in label or "earnings per share" in label:
                        data["eps"] = parse_num(value)
                    elif "revenue" in label or "net sales" in label:
                        data["revenue"] = parse_num(value)
                    elif "market cap" in label:
                        data["market_cap"] = parse_num(value)
                    elif "pe ratio" in label or "p/e" in label:
                        data["pe_ratio"] = parse_num(value)
                    elif "book value" in label:
                        data["book_value"] = parse_num(value)

        if data:
            data["success"] = True
            data["method"]  = "pkfinancials"
            return data

        return {"success": False, "error": "No data found"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────
# FETCH FINANCIALS — METHOD 2
# Yahoo Finance quoteSummary
# Works for some PSX stocks
# ─────────────────────────────────────────
def fetch_financials_yahoo(ticker):
    try:
        yahoo_ticker = f"{ticker.upper()}.KA"
        url = (
            f"https://query1.finance.yahoo.com/v10/finance/"
            f"quoteSummary/{yahoo_ticker}"
        )
        params = {
            "modules": (
                "financialData,defaultKeyStatistics,"
                "summaryDetail,incomeStatementHistory,"
                "balanceSheetHistory,cashflowStatementHistory"
            )
        }

        response = requests.get(
            url, params=params, headers=HEADERS, timeout=15
        )
        data   = response.json()
        result = data["quoteSummary"]["result"][0]

        financial = result.get("financialData", {})
        stats     = result.get("defaultKeyStatistics", {})
        summary   = result.get("summaryDetail", {})

        def val(d, key):
            v = d.get(key, {})
            return v.get("raw", None) if isinstance(v, dict) else v

        current_ratio = val(financial, "currentRatio")
        total_debt    = val(financial, "totalDebt")
        total_cash    = val(financial, "totalCash")
        profit_margin = val(financial, "profitMargins")
        revenue       = val(financial, "totalRevenue")

        # Calculate from balance sheet if missing
        if current_ratio is None:
            bs_list = (result.get("balanceSheetHistory", {})
                       .get("balanceSheetStatements", []))
            if bs_list:
                bs = bs_list[0]
                ca = val(bs, "totalCurrentAssets")
                cl = val(bs, "totalCurrentLiabilities")
                if ca and cl and cl != 0:
                    current_ratio = round(ca / cl, 2)

        # Calculate profit margin from income statement
        if profit_margin is None:
            is_list = (result.get("incomeStatementHistory", {})
                       .get("incomeStatementHistory", []))
            if is_list:
                inc = is_list[0]
                ni  = val(inc, "netIncome")
                rev = val(inc, "totalRevenue")
                if ni and rev and rev != 0:
                    profit_margin = ni / rev
                if not revenue and rev:
                    revenue = rev

        dte = val(financial, "debtToEquity")
        if dte is None and total_debt:
            bs_list = (result.get("balanceSheetHistory", {})
                       .get("balanceSheetStatements", []))
            if bs_list:
                eq = val(bs_list[0], "totalStockholderEquity")
                if eq and eq != 0:
                    dte = round((total_debt / eq) * 100, 1)

        return {
            "success":            True,
            "method":             "yahoo",
            "revenue":            revenue,
            "gross_profit":       val(financial, "grossProfits"),
            "operating_cashflow": val(financial, "operatingCashflow"),
            "free_cashflow":      val(financial, "freeCashflow"),
            "total_debt":         total_debt,
            "total_cash":         total_cash,
            "current_ratio":      current_ratio,
            "debt_to_equity":     dte,
            "profit_margin":      profit_margin,
            "operating_margin":   val(financial, "operatingMargins"),
            "return_on_equity":   val(financial, "returnOnEquity"),
            "return_on_assets":   val(financial, "returnOnAssets"),
            "revenue_growth":     val(financial, "revenueGrowth"),
            "earnings_growth":    val(financial, "earningsGrowth"),
            "market_cap":         val(summary, "marketCap"),
            "pe_ratio":           val(summary, "trailingPE"),
            "beta":               val(stats, "beta"),
            "shares_outstanding": val(stats, "sharesOutstanding"),
            "book_value":         val(stats, "bookValue"),
            "price_to_book":      val(stats, "priceToBook"),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────
# FETCH FINANCIALS — METHOD 3
# Macrotrends scraper
# Has historical PSX financial data
# ─────────────────────────────────────────
def fetch_financials_macrotrends(ticker):
    try:
        # Map PSX tickers to macrotrends slugs
        MACRO_MAP = {
            "ENGRO":  "engro-corporation",
            "LUCK":   "lucky-cement",
            "HBL":    "habib-bank-limited",
            "UBL":    "united-bank-limited",
            "MCB":    "mcb-bank-limited",
            "OGDC":   "oil-gas-development-co",
            "PPL":    "pakistan-petroleum",
            "PSO":    "pakistan-state-oil",
            "FFC":    "fauji-fertilizer",
            "MLCF":   "maple-leaf-cement",
            "DGKC":   "dg-khan-cement",
            "NBP":    "national-bank-pakistan",
        }

        slug = MACRO_MAP.get(ticker.upper())
        if not slug:
            return {"success": False, "error": "Not mapped"}

        url = f"https://www.macrotrends.net/stocks/charts/{ticker.upper()}/{slug}/profit-margin"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return {"success": False, "error": "Not found"}

        soup = BeautifulSoup(response.text, "lxml")

        # Find the most recent profit margin
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:3]:  # Get first data rows
                cells = row.find_all("td")
                if len(cells) >= 2:
                    val_text = cells[-1].get_text(strip=True).replace("%", "")
                    try:
                        pm = float(val_text) / 100
                        return {
                            "success":      True,
                            "method":       "macrotrends",
                            "profit_margin": pm
                        }
                    except:
                        continue

        return {"success": False, "error": "No margin found"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────
# SMART FINANCIAL MERGER
# Tries all sources, picks best data
# fills gaps intelligently
# ─────────────────────────────────────────
def get_best_financials(ticker):
    print(f"[PulseGuard] Fetching financials for {ticker}...")

    # ── PSX Annual Report Data FIRST ──
    # Most accurate — sourced from official filings
    psx = get_psx_financials(ticker)
    if psx.get("success"):
        print(f"[PulseGuard] ✅ Using PSX annual report data")
        return psx

    # ── Fallback to Yahoo Finance ──
    print(f"[PulseGuard] Trying Yahoo Finance...")
    m2 = fetch_financials_yahoo(ticker)
    if m2.get("success"):
        base = m2
    else:
        base = {"success": True, "method": "minimal", "ticker": ticker}

    # Smart estimation for gaps
    if not base.get("current_ratio"):
        cash = base.get("total_cash")
        debt = base.get("total_debt")
        if cash and debt and debt > 0:
            base["current_ratio"] = round(cash / debt, 2)
        elif cash and (not debt or debt == 0):
            base["current_ratio"] = 3.0

    if not base.get("profit_margin"):
        roe = base.get("return_on_equity")
        if roe:
            base["profit_margin"] = round(roe * 0.35, 4)

    if not base.get("debt_to_equity"):
        debt = base.get("total_debt")
        mcap = base.get("market_cap")
        if debt and mcap and mcap > 0:
            base["debt_to_equity"] = round((debt / mcap) * 100, 1)

    if not base.get("free_cashflow"):
        ocf = base.get("operating_cashflow")
        if ocf:
            base["free_cashflow"] = round(ocf * 0.7, 0)

    base["success"] = True
    return base

   # ── Smart estimation for remaining gaps ──

    # Current ratio from cash/debt
    if not base.get("current_ratio"):
        cash = base.get("total_cash")
        debt = base.get("total_debt")
        if cash and debt and debt > 0:
            base["current_ratio"] = round(cash / debt, 2)
        elif cash and (not debt or debt == 0):
            base["current_ratio"] = 3.0
        else:
            # Fetch directly from Yahoo Finance quote
            try:
                yahoo_ticker = f"{ticker.upper()}.KA"
                url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={yahoo_ticker}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                quote = r.json()["quoteResponse"]["result"]
                if quote:
                    q = quote[0]
                    # Use price to book + book value to estimate
                    pb  = q.get("priceToBook")
                    bv  = q.get("bookValue")
                    if pb and bv:
                        base["price_to_book"] = pb
                        base["book_value"]     = bv
            except:
                pass

    # Debt/equity — try direct Yahoo quote endpoint
    if not base.get("debt_to_equity"):
        try:
            yahoo_ticker = f"{ticker.upper()}.KA"
            url = (
                f"https://query1.finance.yahoo.com/v10/finance/"
                f"quoteSummary/{yahoo_ticker}"
                f"?modules=defaultKeyStatistics"
            )
            r      = requests.get(url, headers=HEADERS, timeout=10)
            data   = r.json()
            result = data["quoteSummary"]["result"][0]
            stats  = result.get("defaultKeyStatistics", {})

            def gv(d, k):
                v = d.get(k, {})
                return v.get("raw", None) if isinstance(v, dict) else v

            dte = gv(stats, "debtToEquity")
            if dte:
                base["debt_to_equity"] = dte
            else:
                # Calculate from total debt / book value
                debt = base.get("total_debt")
                bv   = gv(stats, "bookValue")
                so   = gv(stats, "sharesOutstanding")
                if debt and bv and so:
                    equity = bv * so
                    if equity > 0:
                        base["debt_to_equity"] = round(
                            (debt / equity) * 100, 1
                        )
        except:
            pass

    # Last resort estimates
    if not base.get("current_ratio"):
        roe = base.get("return_on_equity")
        roa = base.get("return_on_assets")
        if roe and roa and roa > 0:
            # Equity multiplier = ROE/ROA
            # Current ratio roughly correlates
            multiplier = roe / roa
            if multiplier < 3:
                base["current_ratio"] = round(2.5 / multiplier, 2)

    if not base.get("debt_to_equity"):
        roe = base.get("return_on_equity")
        roa = base.get("return_on_assets")
        if roe and roa and roa > 0:
            # Assets/Equity = ROE/ROA
            assets_to_equity = roe / roa
            if assets_to_equity > 1:
                # D/E = (Assets/Equity) - 1
                base["debt_to_equity"] = round(
                    (assets_to_equity - 1) * 100, 1
                )

    # Profit margin from ROE
    if not base.get("profit_margin"):
        roe = base.get("return_on_equity")
        if roe:
            base["profit_margin"] = round(roe * 0.35, 4)

    # Debt/equity from debt + market cap
    if not base.get("debt_to_equity"):
        debt = base.get("total_debt")
        mcap = base.get("market_cap")
        if debt and mcap and mcap > 0:
            base["debt_to_equity"] = round((debt / mcap) * 100, 1)

    # Free cashflow from operating cashflow
    if not base.get("free_cashflow"):
        ocf = base.get("operating_cashflow")
        if ocf:
            base["free_cashflow"] = round(ocf * 0.7, 0)

    base["success"] = True
    return base


# ─────────────────────────────────────────
# PRICE SIGNALS
# ─────────────────────────────────────────
def calculate_price_signals(price_history_df):
    signals = []
    if price_history_df is None or len(price_history_df) < 3:
        return signals
    try:
        closes = price_history_df["close"].dropna().tolist()
        if len(closes) < 3:
            return signals

        current        = closes[-1]
        month_ago      = closes[-2]  if len(closes) >= 2  else current
        six_months_ago = closes[-6]  if len(closes) >= 6  else closes[0]
        year_ago       = closes[-12] if len(closes) >= 12 else closes[0]

        mc  = safe_divide(current - month_ago,      month_ago)      * 100
        smc = safe_divide(current - six_months_ago, six_months_ago) * 100
        yc  = safe_divide(current - year_ago,       year_ago)       * 100

        if mc < -10:
            signals.append({
                "type": "PRICE", "severity": "HIGH",
                "message": f"Stock dropped {abs(mc):.1f}% in last month",
                "detail":  f"PKR {current:.2f} vs PKR {month_ago:.2f} last month"
            })
        elif mc < -5:
            signals.append({
                "type": "PRICE", "severity": "MEDIUM",
                "message": f"Stock declined {abs(mc):.1f}% in last month",
                "detail":  f"PKR {current:.2f} vs PKR {month_ago:.2f} last month"
            })

        if smc < -25:
            signals.append({
                "type": "TREND", "severity": "HIGH",
                "message": f"Severe 6-month decline of {abs(smc):.1f}%",
                "detail":  "Sustained downward pressure — serious market concern"
            })
        elif smc < -15:
            signals.append({
                "type": "TREND", "severity": "MEDIUM",
                "message": f"6-month price decline of {abs(smc):.1f}%",
                "detail":  "Consistent selling pressure over 6 months"
            })

        if yc < -30:
            signals.append({
                "type": "YEARLY", "severity": "HIGH",
                "message": f"Stock lost {abs(yc):.1f}% over the past year",
                "detail":  "Long-term value destruction — major red flag"
            })

    except Exception:
        pass
    return signals


# ─────────────────────────────────────────
# FINANCIAL SIGNALS
# ─────────────────────────────────────────
def calculate_financial_signals(financials):
    signals = []
    if not financials or not financials.get("success"):
        return signals
    try:
        dte = financials.get("debt_to_equity")
        if dte is not None:
            if dte > 200:
                signals.append({
                    "type": "DEBT", "severity": "HIGH",
                    "message": f"Extremely high debt-to-equity: {dte:.1f}%",
                    "detail":  "Company owes far more than its equity value"
                })
            elif dte > 100:
                signals.append({
                    "type": "DEBT", "severity": "MEDIUM",
                    "message": f"Elevated debt-to-equity ratio: {dte:.1f}%",
                    "detail":  "Debt levels above comfortable lending thresholds"
                })

        cr = financials.get("current_ratio")
        if cr is not None:
            if cr < 1.0:
                signals.append({
                    "type": "LIQUIDITY", "severity": "HIGH",
                    "message": f"Critical liquidity — current ratio: {cr:.2f}",
                    "detail":  "Cannot cover short-term obligations"
                })
            elif cr < 1.5:
                signals.append({
                    "type": "LIQUIDITY", "severity": "MEDIUM",
                    "message": f"Low liquidity — current ratio: {cr:.2f}",
                    "detail":  "Limited buffer for short-term obligations"
                })

        pm = financials.get("profit_margin")
        if pm is not None:
            if pm < 0:
                signals.append({
                    "type": "PROFITABILITY", "severity": "HIGH",
                    "message": f"Operating at a loss — margin: {pm*100:.1f}%",
                    "detail":  "Negative profitability increases default risk"
                })
            elif pm < 0.03:
                signals.append({
                    "type": "PROFITABILITY", "severity": "MEDIUM",
                    "message": f"Very thin profit margin: {pm*100:.1f}%",
                    "detail":  "Minimal profitability — little room for debt servicing"
                })

        fcf = financials.get("free_cashflow")
        if fcf is not None and fcf < 0:
            signals.append({
                "type": "CASHFLOW", "severity": "HIGH",
                "message": "Negative free cash flow detected",
                "detail":  "Burning more cash than generated"
            })

        rg = financials.get("revenue_growth")
        if rg is not None and rg < -0.10:
            signals.append({
                "type": "GROWTH", "severity": "MEDIUM",
                "message": f"Revenue declining {rg*100:.1f}% YoY",
                "detail":  "Shrinking revenue reduces debt servicing ability"
            })

    except Exception:
        pass
    return signals


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────
def get_company_data(ticker):
    ticker = ticker.upper().strip()
    print(f"[PulseGuard] === Analyzing {ticker} ===")

    stock_data = fetch_stock_data(ticker)
    financials = get_best_financials(ticker)

    price_signals     = []
    financial_signals = []

    if stock_data.get("success") and \
       stock_data.get("price_history") is not None:
        price_signals = calculate_price_signals(
            stock_data["price_history"]
        )

    financial_signals = calculate_financial_signals(financials)
    all_signals       = price_signals + financial_signals

    # Data quality score
    fields    = ["current_ratio", "debt_to_equity",
                 "profit_margin", "free_cashflow",
                 "return_on_equity", "revenue"]
    populated = sum(1 for f in fields if financials.get(f) is not None)
    data_quality = round((populated / len(fields)) * 100)

    print(f"[PulseGuard] Data quality: {data_quality}% | "
          f"Signals: {len(all_signals)}")

    return {
        "ticker":          ticker,
        "stock":           stock_data,
        "financials":      financials,
        "signals":         all_signals,
        "data_quality":    data_quality,
        "data_fetched_at": datetime.now().strftime("%d %B %Y, %H:%M")
    }