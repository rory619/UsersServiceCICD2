from typing import Annotated, Optional
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints

# ---------- Reusable type aliases ----------
NameStr = Annotated[str, StringConstraints(min_length=1, max_length=100)]
StudentIdStr = Annotated[str, StringConstraints(pattern=r"^S\d{7}$")]
AgeInt = Annotated[int, Ge(0), Le(150)]


class UserCreate(BaseModel):
    name: NameStr
    email: EmailStr
    age: AgeInt
    student_id: StudentIdStr


class UserRead(BaseModel):
    id: int
    name: NameStr
    email: EmailStr
    age: AgeInt
    student_id: StudentIdStr

class UserUpdate(BaseModel):
    name: Optional[NameStr] = None
    email: Optional[EmailStr] = None
    age: Optional[AgeInt] = None
    student_id: Optional[StudentIdStr] = None

    model_config = ConfigDict(from_attributes=True)
