from pydantic import BaseModel, Field
from typing import Optional

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class DeleteAccountRequest(BaseModel):
    pass # No body needed usually, but logic might require confirmation later.

class DashboardData(BaseModel):
    name: str
    plan_count: int
    completed_topics_count: int
    last_plan_id: Optional[str]
    xp_points: int
    day_streak: int
    level: int

class DashboardResponse(BaseModel):
    status: str
    data: DashboardData
