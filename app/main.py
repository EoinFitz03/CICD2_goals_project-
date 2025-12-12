# app/main.py

from typing import List
import os          # NEW: for env vars
import httpx       # NEW: for HTTP calls to other services

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
    allow_origins=["*"],  # tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- NEW: Base URLs for other services ----------
# Same pattern as the others: env vars tell this service where the others live.
# In dev: localhost with different ports.
# In Docker: service names (e.g. http://user_service:8000)
USER_SERVICE_BASE_URL = os.getenv("USER_SERVICE_BASE_URL", "http://localhost:8000")
WORKOUT_SERVICE_BASE_URL = os.getenv("WORKOUT_SERVICE_BASE_URL", "http://localhost:8001")


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


# ---------- NEW: Integration endpoint (goals service calling others) ----------

@app.get("/api/goals-summary/{user_id}", tags=["proxy"])
def goals_summary(user_id: int, db: Session = Depends(get_db)):
    """
    This endpoint lives in the GOALS service but:
      - Calls the USER service:    GET /api/users/{user_id}
      - Calls the WORKOUT service: GET /workouts?user_id={user_id}
      - Uses its own DB to load goals for that user.

    Same env + httpx pattern as the user and workout services.
    """

    # 1) Call USER service to verify the user exists and get basic info
    user_url = f"{USER_SERVICE_BASE_URL}/api/users/{user_id}"

    try:
        with httpx.Client() as client:
            user_res = client.get(user_url)
        user_res.raise_for_status()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error contacting user service: {exc}",
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"User service error: {exc.response.text}",
        )

    user_data = user_res.json()

    # 2) Get goals locally from this service's own DB
    goals = (
        db.query(GoalDB)
        .filter(GoalDB.user_id == user_id)
        .all()
    )
    goals_list = [GoalOutput.model_validate(g).model_dump() for g in goals]

    # 3) Call WORKOUT service to get this user's workouts (optional)
    workouts_url = f"{WORKOUT_SERVICE_BASE_URL}/workouts"
    workouts_data: list = []

    try:
        with httpx.Client() as client:
            workouts_res = client.get(workouts_url, params={"user_id": user_id})
        workouts_res.raise_for_status()
        workouts_data = workouts_res.json()
    except httpx.RequestError:
        # If workout service is down, still return user + goals
        workouts_data = []
    except httpx.HTTPStatusError:
        workouts_data = []

    return {
        "user": user_data,
        "goals": goals_list,
        "workouts": workouts_data,
    }
