from datetime import datetime

from sqlalchemy.orm import Session

from constants import CashType
from database import Account, AccountBalanceDaily, TransactionCash
from services.portfolio_service import get_enriched_accounts_data


def get_dashboard_kpi(db: Session, acc_cd: str = None) -> dict:
    unique_dates = (
        db.query(AccountBalanceDaily.trade_date)
        .distinct()
        .order_by(AccountBalanceDaily.trade_date.desc())
        .all()
    )
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

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.now()

    yesterday_date = None
    for d in unique_dates:
        if d < today_str:
            yesterday_date = d
            break

    first_of_this_month = today_dt.replace(day=1).strftime("%Y-%m-%d")
    prev_month_end_date = None
    for d in unique_dates:
        if d < first_of_this_month:
            prev_month_end_date = d
            break

    first_of_this_year = today_dt.replace(month=1, day=1).strftime("%Y-%m-%d")
    prev_year_end_date = None
    for d in unique_dates:
        if d < first_of_this_year:
            prev_year_end_date = d
            break

    def get_balance_for_date(target_date_str):
        if not target_date_str:
            return 0
        accounts_to_check = (
            [acc_cd] if acc_cd else [a.acc_cd for a in db.query(Account).all()]
        )
        total = 0
        for acct in accounts_to_check:
            latest = (
                db.query(AccountBalanceDaily)
                .filter(
                    AccountBalanceDaily.acc_cd == acct,
                    AccountBalanceDaily.trade_date <= target_date_str,
                )
                .order_by(AccountBalanceDaily.trade_date.desc())
                .first()
            )
            if latest:
                total += latest.total_balance
        return total

    yesterday_balance = get_balance_for_date(yesterday_date)
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

    today_str = datetime.now().strftime("%Y-%m-%d")

    net_deposit_today = get_net_deposit(yesterday_date, today_str)
    net_deposit_this_month = get_net_deposit(prev_month_end_date, today_str)
    net_deposit_this_year = get_net_deposit(prev_year_end_date, today_str)

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
            "today": calc_period(
                yesterday_balance, current_total_asset, net_deposit_today
            ),
            "this_month": calc_period(
                prev_month_balance, current_total_asset, net_deposit_this_month
            ),
            "this_year": calc_period(
                prev_year_balance, current_total_asset, net_deposit_this_year
            ),
            "total": {
                "total_asset": int(round(current_total_asset)),
                "total_principal": int(round(total_principal)),
                "profit": int(round(total_profit)),
                "return_rate": total_return_rate,
            },
        },
    }
