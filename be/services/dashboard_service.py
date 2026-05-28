from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from constants import CashType
from database import Account, AccountDailyBalance, TransactionCash
from services.portfolio_service import get_enriched_accounts_data


def get_dashboard_kpi(db: Session, acc_cd: str = None) -> dict:
    unique_dates = db.query(AccountDailyBalance.trade_date).distinct().order_by(AccountDailyBalance.trade_date.desc()).all()
    unique_dates = [d[0] for d in unique_dates]

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

    latest_date = None
    prev_date = None
    prev_month_end_date = None
    prev_year_end_date = None

    if unique_dates:
        latest_date = unique_dates[0]
        latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")

        if len(unique_dates) > 1:
            prev_date = unique_dates[1]
        
        for d in unique_dates[1:]:
            dt = datetime.strptime(d, "%Y-%m-%d")
            if dt.year < latest_dt.year or (dt.year == latest_dt.year and dt.month < latest_dt.month):
                if not prev_month_end_date:
                    prev_month_end_date = d
            if dt.year < latest_dt.year:
                if not prev_year_end_date:
                    prev_year_end_date = d

    def get_balance_for_date(target_date_str):
        if not target_date_str:
            return 0
        accounts_to_check = [acc_cd] if acc_cd else [a.acc_cd for a in db.query(Account).all()]
        total = 0
        for acct in accounts_to_check:
            latest = (
                db.query(AccountDailyBalance)
                .filter(
                    AccountDailyBalance.acc_cd == acct,
                    AccountDailyBalance.trade_date <= target_date_str,
                )
                .order_by(AccountDailyBalance.trade_date.desc())
                .first()
            )
            if latest:
                total += latest.total_balance
        return total

    latest_balance = get_balance_for_date(latest_date)
    prev_balance = get_balance_for_date(prev_date)
    prev_month_balance = get_balance_for_date(prev_month_end_date)
    prev_year_balance = get_balance_for_date(prev_year_end_date)

    def get_net_deposit(start_date_str, end_date_str):
        if not end_date_str:
            return 0
        net = 0
        for tx in all_cash:
            tx_date = str(tx.dt_cash)[:10] if tx.dt_cash else ""
            if tx_date <= end_date_str:
                if not start_date_str or tx_date > start_date_str:
                    if tx.cash_type in [CashType.DEPOSIT, "DEPOSIT"]:
                        net += tx.amount
                    elif tx.cash_type in [CashType.WITHDRAW, "WITHDRAW"]:
                        net -= tx.amount
        return net

    net_deposit_today = get_net_deposit(prev_date, latest_date)
    net_deposit_this_month = get_net_deposit(prev_month_end_date, latest_date)
    net_deposit_this_year = get_net_deposit(prev_year_end_date, latest_date)

    def calc_period(a_start, a_end, net_deposit):
        profit = a_end - a_start - net_deposit
        base_amount = a_start + net_deposit
        if base_amount <= 0:
            return_rate = 0.0
        else:
            return_rate = round((profit / base_amount) * 100, 2)
        return {"profit": int(round(profit)), "return_rate": return_rate}

    total_profit = current_total_asset - total_principal
    total_return_rate = (
        round((total_profit / total_principal) * 100, 2) if total_principal > 0 else 0.0
    )

    return {
        "status": "success",
        "data": {
            "today": calc_period(prev_balance, latest_balance, net_deposit_today),
            "this_month": calc_period(prev_month_balance, latest_balance, net_deposit_this_month),
            "this_year": calc_period(prev_year_balance, latest_balance, net_deposit_this_year),
            "total": {
                "total_asset": int(round(current_total_asset)),
                "total_principal": int(round(total_principal)),
                "profit": int(round(total_profit)),
                "return_rate": total_return_rate,
            },
        },
    }
