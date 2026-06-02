from datetime import datetime
from typing import List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.exceptions import BadRequestException, NotFoundException
from database import Stock, StockCache

# --- Stock (Portfolio Holding) ---


def get_stocks(db: Session, acc_cd: str = None) -> List[Tuple[Stock, str]]:
    query = db.query(Stock, StockCache.stock_name).outerjoin(
        StockCache, Stock.stock_code == StockCache.stock_code
    )
    if acc_cd:
        query = query.filter(Stock.acc_cd == acc_cd)
    return query.all()


def get_stock(db: Session, acc_cd: str, stock_code: str) -> Tuple[Stock, str]:
    result = (
        db.query(Stock, StockCache.stock_name)
        .outerjoin(StockCache, Stock.stock_code == StockCache.stock_code)
        .filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code)
        .first()
    )
    if not result:
        raise NotFoundException("Stock holding not found")
    return result


def create_stock(
    db: Session,
    acc_cd: str,
    stock_code: str,
    quantity: int,
    avg_price: float,
    current_price: float,
    purchase_amount: int,
) -> Stock:
    existing = (
        db.query(Stock)
        .filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code)
        .first()
    )
    if existing:
        raise BadRequestException("Stock holding already exists")

    new_stock = Stock(
        acc_cd=acc_cd,
        stock_code=stock_code,
        quantity=quantity,
        avg_price=avg_price,
        current_price=current_price,
        purchase_amount=purchase_amount,
    )
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    return new_stock


def update_stock(
    db: Session,
    acc_cd: str,
    stock_code: str,
    quantity: int = None,
    avg_price: float = None,
    current_price: float = None,
    purchase_amount: int = None,
) -> Stock:
    stock_rec = (
        db.query(Stock)
        .filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code)
        .first()
    )
    if not stock_rec:
        raise NotFoundException("Stock holding not found")

    if quantity is not None:
        stock_rec.quantity = quantity
    if avg_price is not None:
        stock_rec.avg_price = avg_price
    if current_price is not None:
        stock_rec.current_price = current_price
    if purchase_amount is not None:
        stock_rec.purchase_amount = purchase_amount

    db.commit()
    db.refresh(stock_rec)
    return stock_rec


def delete_stock(db: Session, acc_cd: str, stock_code: str):
    stock_rec = (
        db.query(Stock)
        .filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code)
        .first()
    )
    if not stock_rec:
        raise NotFoundException("Stock holding not found")
    db.delete(stock_rec)
    db.commit()


# --- StockCache (Master) ---


def get_stock_masters(db: Session) -> List[StockCache]:
    return db.query(StockCache).filter(StockCache.dt_deleted.is_(None)).all()


def search_stocks(db: Session, keyword: str) -> List[StockCache]:
    return (
        db.query(StockCache)
        .filter(
            StockCache.dt_deleted.is_(None),
            or_(
                StockCache.stock_name.like(f"%{keyword}%"),
                StockCache.stock_code.like(f"%{keyword}%"),
            ),
        )
        .limit(20)
        .all()
    )


def lookup_stock(db: Session, code: str) -> str:
    master = (
        db.query(StockCache)
        .filter(StockCache.stock_code == code, StockCache.dt_deleted.is_(None))
        .first()
    )
    return master.stock_name if master else "알 수 없음"


def create_master(
    db: Session, stock_code: str, stock_name: str, market: str
) -> StockCache:
    existing = db.query(StockCache).filter(StockCache.stock_code == stock_code).first()
    if existing:
        raise BadRequestException("Master already exists")

    new_master = StockCache(
        stock_code=stock_code,
        stock_name=stock_name,
        market=market,
    )
    db.add(new_master)
    db.commit()
    db.refresh(new_master)
    return new_master


def update_master(
    db: Session, stock_code: str, stock_name: str = None, market: str = None
) -> StockCache:
    master = (
        db.query(StockCache)
        .filter(StockCache.stock_code == stock_code, StockCache.dt_deleted.is_(None))
        .first()
    )
    if not master:
        raise NotFoundException("Master not found")

    if stock_name is not None:
        master.stock_name = stock_name
    if market is not None:
        master.market = market

    db.commit()
    db.refresh(master)
    return master


def delete_master(db: Session, stock_code: str):
    master = (
        db.query(StockCache)
        .filter(StockCache.stock_code == stock_code, StockCache.dt_deleted.is_(None))
        .first()
    )
    if not master:
        raise NotFoundException("Master not found")
    master.dt_deleted = datetime.utcnow().isoformat()
    db.commit()
