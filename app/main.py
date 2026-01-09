# app/main.py

from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, GoalDB
from app.schemas import GoalInput, GoalOutput, GoalUpdate

# Create tables using the Base from app.models
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Goals Service",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "goals"}


# ---------- GOALS CRUD ----------

@app.post(
    "/goals",
    response_model=GoalOutput,
    status_code=status.HTTP_201_CREATED,
    tags=["goals"],
)
def create_goal(
    payload: GoalInput,
    db: Session = Depends(get_db),
):
    goal = GoalDB(
        user_id=payload.user_id,
        title=payload.title,
        description=payload.description,
        target_value=payload.target_value,
        current_value=payload.current_value,
        unit=payload.unit,
        due_date=payload.due_date,
        status=payload.status,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@app.get(
    "/goals",
    response_model=List[GoalOutput],
    tags=["goals"],
)
def list_goals(
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    """
    List all goals, optionally filtered by user_id.
    """
    query = db.query(GoalDB)
    if user_id is not None:
        query = query.filter(GoalDB.user_id == user_id)
    return query.all()


@app.get(
    "/goals/{goal_id}",
    response_model=GoalOutput,
    tags=["goals"],
)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
):
    goal = (
        db.query(GoalDB)
        .filter(GoalDB.goal_id == goal_id)
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@app.put(
    "/goals/{goal_id}",
    response_model=GoalOutput,
    tags=["goals"],
)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
):
    goal = (
        db.query(GoalDB)
        .filter(GoalDB.goal_id == goal_id)
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(goal, key, value)

    db.commit()
    db.refresh(goal)
    return goal


@app.delete(
    "/goals/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["goals"],
)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
):
    goal = (
        db.query(GoalDB)
        .filter(GoalDB.goal_id == goal_id)
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return
