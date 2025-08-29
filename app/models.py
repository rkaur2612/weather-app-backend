"""
models.py

This file defines the structure of the database tables using SQLAlchemy ORM.

Weather Table:
- Stores weather information for different locations and dates.
- Columns:
    - id: Primary key, unique identifier for each record
    - location: Name, ZIP code, or any string representing the location
    - date: Date of the weather reading
    - temperature: Temperature value (float)
    - description: Optional text describing the weather (e.g., Sunny, Rainy)
    - humidity: Optional humidity percentage (integer)
    - wind_speed: Optional wind speed value (float)

Note: The actual table in the SQLite database will be created when
      Base.metadata.create_all(bind=engine) is executed.
"""

from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class Weather(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True, nullable=False) #for quick loopkup used index
    date = Column(Date, nullable=False)
    temperature = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    humidity = Column(Integer, nullable=True)
    wind_speed = Column(Float, nullable=True)

