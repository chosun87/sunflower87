from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from constants import CashType
from database import Account, AccountDailyBalance, TransactionCash
from services.portfolio_service import get_enriched_accounts_data


def get_dashboard_kpi(db: Session, acc_cd: str = None) -> dict:
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    first_day_this_month = today.replace(day=1)
    last_month_end = first_day_this_month - timedelta(days=1)
    
    last_year_end = today.replace(year=today.year - 1, month=12, day=31)
    
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    last_month_end_str = last_month_end.strftime("%Y-%m-%d")
    last_year_end_str = last_year_end.strftime("%Y-%m-%d")
    
    enriched = get_enriched_accounts_data(db)
    if acc_cd:
        accounts = enriched.get("data", {}).get("accounts", [])
        acct_data = next((a for a in accounts if a["acc_cd"] == acc_cd), None)
        current_total_asset = acct_data["total_eval"] if acct_data else 0
    else:
        current_total_asset = enriched.get("data", {}).get("total_asset", 0)
        
    cash_query = db.query(TransactionCash).filter(TransactionCash.dt_deleted.is_(None))
    if acc_cd:
        cash_query = cash_query.filter(TransactionCash.acc_cd == acc_cd)
        
    all_cash = cash_query.all()
    
    total_principal = 0
    
    for tx in all_cash:
        if tx.cash_type in [CashType.DEPOSIT, "DEPOSIT"]:
            amt = tx.amount
        elif tx.cash_type in [CashType.WITHDRAW, "WITHDRAW"]:
            amt = -tx.amount
        else:
            continue
            
        total_principal += amt
            
    def get_a_start(target_date_str):
        accounts_to_check = [acc_cd] if acc_cd else [a.acc_cd for a in db.query(Account).all()]
        total = 0
        for acct in accounts_to_check:
            latest = db.query(AccountDailyBalance).filter(
                AccountDailyBalance.acc_cd == acct,
                AccountDailyBalance.trade_date <= target_date_str
            ).order_by(AccountDailyBalance.trade_date.desc()).first()
            if latest:
                total += latest.total_balance
        return total

    a_start_today = get_a_start(yesterday_str)
    a_start_this_month = get_a_start(last_month_end_str)
    a_start_this_year = get_a_start(last_year_end_str)
    
    def calc_period(a_start, a_end):
        if a_start == 0:
            profit = a_end
            return_rate = 0.0
        else:
            profit = a_end - a_start
            return_rate = round((profit / a_start) * 100, 2)
        return {"profit": int(round(profit)), "return_rate": return_rate}
        
    total_profit = current_total_asset - total_principal
    total_return_rate = round((total_profit / total_principal) * 100, 2) if total_principal > 0 else 0.0
    
    return {
        "status": "success",
        "data": {
            "today": calc_period(a_start_today, current_total_asset),
            "this_month": calc_period(a_start_this_month, current_total_asset),
            "this_year": calc_period(a_start_this_year, current_total_asset),
            "total": {
                "total_asset": int(round(current_total_asset)),
                "total_principal": int(round(total_principal)),
                "profit": int(round(total_profit)),
                "return_rate": total_return_rate
            }
        }
    }
