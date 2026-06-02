import os
import sys
from datetime import datetime

# Ensure 'be' directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from database import Account, SessionLocal
from main import app

client = TestClient(app)


def run_tests():
    db = SessionLocal()
    acc = db.query(Account).first()
    if not acc:
        print("No accounts found in DB. Please create one first.")
        return

    acc_cd = acc.acc_cd
    today_str = datetime.now().strftime("%Y-%m-%d")

    print(f"--- QA Testing for Account: {acc_cd} ---")

    print("\n[TC-01] 파라미터 없이 동기화 요청 (기본값: 1개월 전 ~ 어제)")
    res1 = client.post(f"/api/accounts/{acc_cd}/sync_balance_daily", json={})
    print(f"Status: {res1.status_code}")
    print(f"Response: {res1.json()}")

    print("\n[TC-02] 과거 기간 명시적 지정 (2024-01-01 ~ 2024-01-31)")
    res2 = client.post(
        f"/api/accounts/{acc_cd}/sync_balance_daily",
        json={"start_date": "2024-01-01", "end_date": "2024-01-31"},
    )
    print(f"Status: {res2.status_code}")
    print(f"Response: {res2.json()}")

    print(f"\n[TC-03] end_date를 오늘({today_str})로 지정하여 미래 날짜 방어 로직 확인")
    res3 = client.post(
        f"/api/accounts/{acc_cd}/sync_balance_daily",
        json={"end_date": today_str},
    )
    print(f"Status: {res3.status_code}")
    print(f"Response: {res3.json()}")


if __name__ == "__main__":
    run_tests()
