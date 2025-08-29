"""
Input model → validates what the user sends (location + date range).
Output model → defines what is returned from the API (weather details)
"""
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional

# -------------------------------
# Input model for CREATE/READ
# -------------------------------
class WeatherRequest(BaseModel):
    location: str = Field(..., description="City name or zip code")
    start_date: date
    end_date: date

    # Validator to ensure start_date <= end_date
    @field_validator('end_date')
    def check_date_range(cls, v, values):
        start = values.get('start_date')
        if start and v < start:
            raise ValueError("end_date must be after or equal to start_date")
        return v


# -------------------------------
# Output model for responses
# -------------------------------
class WeatherResponse(BaseModel):
    location: str
    date: date
    temperature: float
    description: Optional[str]
    humidity: Optional[int]
    wind_speed: Optional[float]

    class Config:
        from_attributes = True  # allows compatibility with SQLAlchemy models

# class WeatherOut(BaseModel):
#     id: int
#     location: str
#     date: date
#     temperature: float
#     description: str
#     humidity: float
#     wind_speed: float

#     class Config:
#         from_attributes = True