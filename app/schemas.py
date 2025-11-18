# app/schemas.py

from typing import Annotated, Optional
from enum import Enum

from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints

# ---------- Reusable type aliases ----------

NameStr   = Annotated[str, StringConstraints(min_length=2, max_length=50)]
AgeInt    = Annotated[int, Ge(18), Le(150)]
UserIdInt = int


# ---------- Enums ----------

class GenderEnum(str, Enum):
    Male   = "Male"
    Female = "Female"
    Other  = "Other"


# ---------- Users ----------

# Used for creating a new user (request body)
class UserInput(BaseModel):
    name: NameStr
    email: EmailStr
    age: AgeInt
    gender: GenderEnum


# Used when returning a user from the database (response model)
class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UserIdInt
    name: NameStr
    email: EmailStr
    age: AgeInt
    gender: GenderEnum


# Used for updating an existing user (PATCH/PUT body)
# Fields are optional so you can send partial updates if you want
class UserUpdate(BaseModel):
    name: Optional[NameStr] = None
    email: Optional[EmailStr] = None
    age: Optional[AgeInt] = None
    gender: Optional[GenderEnum] = None


# Used when you want to delete a user (request body or path param + body)
class UserRemove(BaseModel):
    user_id: UserIdInt
