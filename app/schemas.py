from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    department: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=15, le=60)

class StudentUpdate(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=15, le=60)


class StudentResponse(StudentCreate):

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime