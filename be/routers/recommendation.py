from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import Recommendation, StockCache, get_db

router = APIRouter(prefix="/api/recommendations", tags=["Recommendation"])


@router.get(
    "", response_model=schemas.ApiResponse[List[schemas.RecommendationResponse]]
)
def get_recommendations(db: Session = Depends(get_db)):
    query = (
        db.query(Recommendation, StockCache.stock_name)
        .outerjoin(StockCache, Recommendation.stock_code == StockCache.stock_code)
        .filter(Recommendation.dt_deleted.is_(None))
    )
    results = query.order_by(Recommendation.score.desc()).all()
    data = []
    for rec, name in results:
        r_dict = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
        r_dict["stock_name"] = name
        data.append(r_dict)
    return {"status": "success", "data": data}


@router.post(
    "",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.RecommendationResponse],
)
def add_recommendation(
    rec: schemas.RecommendationCreate, db: Session = Depends(get_db)
):
    existing = (
        db.query(Recommendation)
        .filter(
            Recommendation.stock_code == rec.stock_code,
            Recommendation.dt_deleted.is_(None),
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Recommendation already exists")
    new_rec = Recommendation(
        stock_code=rec.stock_code, tag=rec.tag, reason=rec.reason, score=rec.score
    )
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    return {"status": "success", "data": new_rec}


@router.put("/{stock_code}")
def update_recommendation(
    stock_code: str,
    rec_update: schemas.RecommendationUpdate,
    db: Session = Depends(get_db),
):
    db_rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.stock_code == stock_code, Recommendation.dt_deleted.is_(None)
        )
        .first()
    )
    if not db_rec:
        raise HTTPException(404, "Recommendation not found")
    if rec_update.tag:
        db_rec.tag = rec_update.tag
    if rec_update.reason:
        db_rec.reason = rec_update.reason
    if rec_update.score is not None:
        db_rec.score = rec_update.score
    db.commit()
    return {"status": "success", "data": db_rec}


@router.delete("/{stock_code}")
def delete_recommendation(stock_code: str, db: Session = Depends(get_db)):
    db_rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.stock_code == stock_code, Recommendation.dt_deleted.is_(None)
        )
        .first()
    )
    if not db_rec:
        raise HTTPException(404, "Recommendation not found")
    db_rec.dt_deleted = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Deleted."}

@router.get("/{stock_code}", response_model=schemas.ApiResponse[schemas.RecommendationResponse])
def get_recommendation(stock_code: str, db: Session = Depends(get_db)):
    result = (
        db.query(Recommendation, StockCache.stock_name)
        .outerjoin(StockCache, Recommendation.stock_code == StockCache.stock_code)
        .filter(Recommendation.stock_code == stock_code, Recommendation.dt_deleted.is_(None))
        .first()
    )
    if not result:
        raise HTTPException(404, "Recommendation not found")
    rec, name = result
    r_dict = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
    r_dict["stock_name"] = name
    return {"status": "success", "data": r_dict}

from pydantic import BaseModel
class FeedbackUpdate(BaseModel):
    investor_score: int

@router.patch("/{stock_code}/feedback")
def update_feedback(stock_code: str, feedback: FeedbackUpdate, db: Session = Depends(get_db)):
    db_rec = (
        db.query(Recommendation)
        .filter(Recommendation.stock_code == stock_code, Recommendation.dt_deleted.is_(None))
        .first()
    )
    if not db_rec:
        raise HTTPException(404, "Recommendation not found")
    
    db_rec.investor_score = feedback.investor_score
    if feedback.investor_score == 0:
        db_rec.dt_deleted = datetime.utcnow()
        
    db.commit()
    return {"status": "success", "message": "Feedback submitted."}
