# app/schemas.py

from typing import Annotated, Optional
from datetime import date

from annotated_types import Ge, Le
from pydantic import BaseModel, ConfigDict, StringConstraints

# ---------- Reusable type aliases ----------

GoalTitleStr = Annotated[str, StringConstraints(min_length=3, max_length=100)]
GoalDescriptionStr = Annotated[str, StringConstraints(max_length=500)]
GoalStatusStr = Annotated[str, StringConstraints(min_length=3, max_length=50)]
GoalUnitStr = Annotated[str, StringConstraints(min_length=1, max_length=50)]

GoalValueFloat = Annotated[float, Ge(0.0), Le(1_000_000.0)]

UserIdInt = int
GoalIdInt = int


# ---------- Schemas ----------

class GoalInput(BaseModel):
    user_id: UserIdInt
    title: GoalTitleStr
    description: Optional[GoalDescriptionStr] = None
    target_value: Optional[GoalValueFloat] = None
    current_value: Optional[GoalValueFloat] = None
    unit: Optional[GoalUnitStr] = None
    due_date: Optional[date] = None
    status: GoalStatusStr = "pending"


class GoalOutput(BaseModel):
    # like orm_mode=True in Pydantic v1
    model_config = ConfigDict(from_attributes=True)

    goal_id: GoalIdInt
    user_id: UserIdInt
    title: GoalTitleStr
    description: Optional[GoalDescriptionStr] = None
    target_value: Optional[GoalValueFloat] = None
    current_value: Optional[GoalValueFloat] = None
    unit: Optional[GoalUnitStr] = None
    due_date: Optional[date] = None
    status: GoalStatusStr


class GoalUpdate(BaseModel):
    title: Optional[GoalTitleStr] = None
    description: Optional[GoalDescriptionStr] = None
    target_value: Optional[GoalValueFloat] = None
    current_value: Optional[GoalValueFloat] = None
    unit: Optional[GoalUnitStr] = None
    due_date: Optional[date] = None
    status: Optional[GoalStatusStr] = None


class GoalRemove(BaseModel):
    goal_id: GoalIdInt
