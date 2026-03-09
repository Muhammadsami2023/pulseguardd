# monitor.py
# Loan Monitoring Module for PulseGuard
# Tracks companies after loans are approved
# Alerts banks when risk signals change

import json
import os
from datetime import datetime, timedelta
from utils import get_risk_level, format_pkr

# ─────────────────────────────────────────
# STORAGE FILE
# ─────────────────────────────────────────
LOANS_FILE = "active_loans.json"


def load_loans():
    if not os.path.exists(LOANS_FILE):
        return []
    try:
        with open(LOANS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_loans(loans):
    try:
        with open(LOANS_FILE, "w") as f:
            json.dump(loans, f, indent=2, default=str)
        return True
    except:
        return False


# ─────────────────────────────────────────
# ADD A NEW LOAN TO MONITORING
# ─────────────────────────────────────────
def add_loan(ticker, company_name, loan_amount, loan_duration_months, initial_score):
    loans = load_loans()

    # Check if already monitoring this company
    for loan in loans:
        if loan["ticker"] == ticker.upper() and loan["status"] == "ACTIVE":
            return {
                "success": False,
                "message": f"{company_name} is already being monitored."
            }

    start_date = datetime.now()
    end_date = start_date + timedelta(days=loan_duration_months * 30)

    # ── Set initial alert level based on score ──
    initial_alerts = []
    initial_alert_level = "NORMAL"

    if initial_score < 40:
        initial_alert_level = "CRITICAL"
        initial_alerts.append({
            "date": start_date.strftime("%Y-%m-%d %H:%M"),
            "type": "CRITICAL",
            "message": f"🚨 CRITICAL: Loan approved with critical risk score of {initial_score}",
            "action": "Risk score is critically low at time of approval. Enhanced monitoring activated. Collateral review recommended."
        })
    elif initial_score < 60:
        initial_alert_level = "WARNING"
        initial_alerts.append({
            "date": start_date.strftime("%Y-%m-%d %H:%M"),
            "type": "WARNING",
            "message": f"⚠️ WARNING: Loan approved with medium risk score of {initial_score}",
            "action":"Risk score is below recommended threshold at time of approval. Quarterly review strongly recommended."
        })

    new_loan = {
        "id": len(loans) + 1,
        "ticker": ticker.upper(),
        "company_name": company_name,
        "loan_amount": loan_amount,
        "loan_duration_months": loan_duration_months,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "initial_score": initial_score,
        "current_score": initial_score,
        "lowest_score": initial_score,
        "status": "ACTIVE",
        "alert_level": initial_alert_level,
        "score_history": [
            {
                "date": start_date.strftime("%Y-%m-%d"),
                "score": initial_score,
                "note": "Loan approved — monitoring started"
            }
        ],
        "alerts": initial_alerts
    }

    loans.append(new_loan)
    save_loans(loans)

    return {
        "success": True,
        "message": f"✅ {company_name} added to loan monitoring.",
        "loan": new_loan
    }


# ─────────────────────────────────────────
# UPDATE LOAN WITH NEW SCORE
# ─────────────────────────────────────────
def update_loan_score(ticker, new_score):
    loans = load_loans()
    updated = False
    alert_generated = None

    for loan in loans:
        if loan["ticker"] == ticker.upper() and loan["status"] == "ACTIVE":

            old_score = loan["current_score"]
            score_drop = old_score - new_score

            loan["current_score"] = new_score
            if new_score < loan["lowest_score"]:
                loan["lowest_score"] = new_score

            loan["score_history"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "score": new_score,
                "note": "Routine monitoring check"
            })

            alert = None

            # Critical drop — more than 20 points
            if score_drop >= 20:
                alert = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "CRITICAL",
                    "message": f"🚨 CRITICAL: Score dropped {score_drop} points ({old_score} → {new_score})",
                    "action": "Immediate review recommended. Consider loan recall or collateral increase."
                }
                loan["alert_level"] = "CRITICAL"

            # Warning drop — 10 to 20 points
            elif score_drop >= 10:
                alert = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "WARNING",
                    "message": f"⚠️ WARNING: Score dropped {score_drop} points ({old_score} → {new_score})",
                    "action": "Schedule review meeting with company management."
                }
                loan["alert_level"] = "WARNING"

            # Score entered high risk zone
            elif new_score < 40 and old_score >= 40:
                alert = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "HIGH_RISK",
                    "message": f"🔴 ALERT: Company entered HIGH RISK zone (Score: {new_score})",
                    "action": "Loan at risk. Initiate enhanced monitoring protocol."
                }
                loan["alert_level"] = "HIGH_RISK"

            # Score recovered
            elif score_drop <= -10:
                alert = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "RECOVERY",
                    "message": f"✅ POSITIVE: Score improved {abs(score_drop)} points ({old_score} → {new_score})",
                    "action": "Company showing signs of recovery. Continue monitoring."
                }
                loan["alert_level"] = "NORMAL"

            if alert:
                loan["alerts"].append(alert)
                alert_generated = alert

            updated = True
            break

    if updated:
        save_loans(loans)

    return {
        "updated": updated,
        "alert": alert_generated
    }


# ─────────────────────────────────────────
# GET LOAN STATUS
# ─────────────────────────────────────────
def get_loan_status(ticker):
    loans = load_loans()
    for loan in loans:
        if loan["ticker"] == ticker.upper() and loan["status"] == "ACTIVE":
            return loan
    return None


# ─────────────────────────────────────────
# GET ALL ACTIVE LOANS SUMMARY
# ─────────────────────────────────────────
def get_all_loans_summary():
    loans = load_loans()
    active = [l for l in loans if l["status"] == "ACTIVE"]

    summary = {
        "total_active": len(active),
        "critical_alerts": len([l for l in active if l["alert_level"] == "CRITICAL"]),
        "warnings": len([l for l in active if l["alert_level"] == "WARNING"]),
        "high_risk": len([l for l in active if l["alert_level"] == "HIGH_RISK"]),
        "normal": len([l for l in active if l["alert_level"] == "NORMAL"]),
        "loans": active
    }

    return summary


# ─────────────────────────────────────────
# CLOSE A LOAN
# ─────────────────────────────────────────
def close_loan(ticker):
    loans = load_loans()
    for loan in loans:
        if loan["ticker"] == ticker.upper() and loan["status"] == "ACTIVE":
            loan["status"] = "CLOSED"
            loan["closed_date"] = datetime.now().strftime("%Y-%m-%d")
            loan["cancelled_date"] = datetime.now().strftime("%Y-%m-%d")
            save_loans(loans)
            return {
                "success": True,
                "message": f"✅ Loan for {loan['company_name']} marked as closed."
            }
    return {
        "success": False,
        "message": "No active loan found for this company."
    }


# ─────────────────────────────────────────
# GET DAYS REMAINING ON LOAN
# ─────────────────────────────────────────
def get_days_remaining(end_date_str):
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        today = datetime.now()
        delta = end_date - today
        return max(0, delta.days)
    except:
        return 0


# ─────────────────────────────────────────
# GET LOAN HEALTH STATUS
# ─────────────────────────────────────────
def get_portfolio_health(loans):
    if not loans:
        return "NO LOANS"

    critical = sum(1 for l in loans if l["alert_level"] == "CRITICAL")
    warning = sum(1 for l in loans if l["alert_level"] == "WARNING")

    if critical > 0:
        return "🚨 CRITICAL"
    elif warning > 0:
        return "⚠️ NEEDS ATTENTION"
    else:
        return "✅ HEALTHY"