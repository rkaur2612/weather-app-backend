from sqlalchemy.orm import Session
from datetime import date
from . import models, schemas

# -------------------------------
# CREATE: Add weather records
# -------------------------------
 #Takes a WeatherResponse object.
# Adds it to the database.
# Returns the created record.
def create_weather(db: Session, weather_data: schemas.WeatherResponse):
    db_weather = models.Weather(
        location=weather_data.location,
        date=weather_data.date,
        temperature=weather_data.temperature,
        description=weather_data.description,
        humidity=weather_data.humidity,
        wind_speed=weather_data.wind_speed
    )
    db.add(db_weather)
    db.commit()
    db.refresh(db_weather)
    return db_weather


# -------------------------------
# READ: Get weather for location + date range
# -------------------------------
# Takes a location and a start_date/end_date
# Queries all matching rows
def get_weather(db: Session, location: str, start_date: date, end_date: date):
    return db.query(models.Weather)\
        .filter(models.Weather.location == location)\
        .filter(models.Weather.date.between(start_date, end_date))\
        .all()


# -------------------------------
# UPDATE: Update a weather record by ID
# -------------------------------
# Updates any field of a weather record by its id
# Accepts a dictionary of fields to update.
def update_weather(db: Session, weather_id: int, update_data: dict):
    db_weather = db.query(models.Weather).filter(models.Weather.id == weather_id).first()
    if not db_weather:
        return None
    for key, value in update_data.items():
        setattr(db_weather, key, value)
    db.commit()
    db.refresh(db_weather)
    return db_weather


# -------------------------------
# DELETE: Delete a weather record by ID
# -------------------------------
# Deletes a record by id.
def delete_weather(db: Session, weather_id: int):
    db_weather = db.query(models.Weather).filter(models.Weather.id == weather_id).first()
    if not db_weather:
        return False
    db.delete(db_weather)
    db.commit()
    return True
