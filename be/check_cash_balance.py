from database import SessionLocal, AccountDailyBalance
import pandas as pd

db = SessionLocal()
try:
    balances = db.query(AccountDailyBalance).order_by(AccountDailyBalance.trade_date.desc()).all()
    data = []
    for b in balances:
        data.append({
            "Date": b.trade_date,
            "Account": b.acc_cd,
            "Cash Balance": b.cash_balance
        })

    if not data:
        print("No data found in AccountDailyBalance.")
    else:
        df = pd.DataFrame(data)
        # Pivot the dataframe to have Date as index, Account as columns, and Cash Balance as values
        pivot_df = df.pivot(index="Date", columns="Account", values="Cash Balance")
        pivot_df = pivot_df.sort_index(ascending=False).head(15) # Show last 15 days
        
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        # Format numbers with commas
        for col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "-")
            
        print("최근 15일 기준 각 계좌별 일일 예수금 (Cash Balance) 현황:")
        print("-" * 60)
        print(pivot_df)
        print("-" * 60)
finally:
    db.close()
