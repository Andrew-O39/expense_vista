from sqlalchemy.orm import Session
from typing import Optional
from app.db.models.ml_category_map import MLCategoryMap

def get_by_user_and_pattern(db: Session, user_id: int, pattern: str) -> Optional[MLCategoryMap]:
    return (
        db.query(MLCategoryMap)
        .filter(MLCategoryMap.user_id == user_id, MLCategoryMap.pattern == pattern)
        .first()
    )

def upsert_mapping(db: Session, user_id: int, pattern: str, category: str, source: str | None = None) -> MLCategoryMap:
    existing = get_by_user_and_pattern(db, user_id, pattern)
    if existing:
        existing.category = category
        if source:
            existing.source = source
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    obj = MLCategoryMap(user_id=user_id, pattern=pattern, category=category, source=source)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj