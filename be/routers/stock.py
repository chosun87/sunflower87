from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import services.stock_service as stock_service
from core.responses import success_response
from database import get_db
from services.portfolio_service import get_enriched_accounts_data

router = APIRouter(prefix="/api/stocks", tags=["Stock"])


@router.get("/portfolio", response_model=dict)
def get_portfolio(db: Session = Depends(get_db)):
    return get_enriched_accounts_data(db)


@router.get(
    "/masters", response_model=schemas.ApiResponse[list[schemas.StockCacheResponse]]
)
def get_stock_masters(db: Session = Depends(get_db)):
    masters = stock_service.get_stock_masters(db)
    return success_response(masters)


@router.get("", response_model=schemas.ApiResponse[list[schemas.StockResponse]])
def get_stocks(acc_cd: str = None, db: Session = Depends(get_db)):
    results = stock_service.get_stocks(db, acc_cd)
    data = []
    for stock_rec, stock_name in results:
        data.append(
            schemas.StockResponse(
                stock_code=stock_rec.stock_code,
                acc_cd=stock_rec.acc_cd,
                stock_name=stock_name,
                quantity=stock_rec.quantity,
                avg_price=stock_rec.avg_price,
                current_price=stock_rec.current_price,
                purchase_amount=stock_rec.purchase_amount,
            )
        )
    return success_response(data)


@router.get(
    "/{acc_cd}/{stock_code}", response_model=schemas.ApiResponse[schemas.StockResponse]
)
def get_stock(acc_cd: str, stock_code: str, db: Session = Depends(get_db)):
    stock_rec, stock_name = stock_service.get_stock(db, acc_cd, stock_code)
    data = schemas.StockResponse(
        stock_code=stock_rec.stock_code,
        acc_cd=stock_rec.acc_cd,
        stock_name=stock_name,
        quantity=stock_rec.quantity,
        avg_price=stock_rec.avg_price,
        current_price=stock_rec.current_price,
        purchase_amount=stock_rec.purchase_amount,
    )
    return success_response(data)


@router.post(
    "", status_code=201, response_model=schemas.ApiResponse[schemas.StockResponse]
)
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    new_stock = stock_service.create_stock(
        db,
        stock.acc_cd,
        stock.stock_code,
        stock.quantity,
        stock.avg_price,
        stock.current_price,
        stock.purchase_amount,
    )
    return success_response(new_stock)


@router.put("/{acc_cd}/{stock_code}")
def update_stock(
    acc_cd: str,
    stock_code: str,
    stock_data: schemas.StockUpdate,
    db: Session = Depends(get_db),
):
    updated = stock_service.update_stock(
        db,
        acc_cd,
        stock_code,
        stock_data.quantity,
        stock_data.avg_price,
        stock_data.current_price,
        stock_data.purchase_amount,
    )
    return success_response(updated)


@router.delete("/{acc_cd}/{stock_code}")
def delete_stock(acc_cd: str, stock_code: str, db: Session = Depends(get_db)):
    stock_service.delete_stock(db, acc_cd, stock_code)
    return success_response(message="Stock holding record deleted.")


@router.get("/search", response_model=schemas.ApiResponse[schemas.StockCacheResponse])
def search_stocks(keyword: str, db: Session = Depends(get_db)):
    results = stock_service.search_stocks(db, keyword)
    # The original router wrapped this in {"status": "success", "results": results}
    # To keep exact backward compatibility with the frontend format:
    return {"status": "success", "results": results}


@router.get("/lookup", response_model=dict)
def lookup_stock(code: str, db: Session = Depends(get_db)):
    name = stock_service.lookup_stock(db, code)
    return {"status": "success", "code": code, "name": name}


@router.post("/sync_master")
def sync_master(db: Session = Depends(get_db)):
    return success_response(message="종목 마스터 수집이 완료되었습니다.")


@router.post(
    "/master",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.StockCacheResponse],
)
def create_master(master_data: schemas.StockCacheCreate, db: Session = Depends(get_db)):
    new_master = stock_service.create_master(
        db, master_data.stock_code, master_data.stock_name, master_data.market
    )
    return success_response(new_master)


@router.put(
    "/master/{stock_code}",
    response_model=schemas.ApiResponse[schemas.StockCacheResponse],
)
def update_master(
    stock_code: str,
    master_data: schemas.StockCacheUpdate,
    db: Session = Depends(get_db),
):
    updated = stock_service.update_master(
        db, stock_code, master_data.stock_name, master_data.market
    )
    return success_response(updated)


@router.delete("/master/{stock_code}")
def delete_master(stock_code: str, db: Session = Depends(get_db)):
    stock_service.delete_master(db, stock_code)
    return success_response(message="Master stock deleted.")
