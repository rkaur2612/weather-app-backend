from sqlalchemy.orm import Session
from datetime import date
from . import models, schemas
from app.utils import weather_prompt_template
from groq import Groq
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os

# Load API key from .env
load_dotenv()

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

# ----------------------------------
# LLM Call to generate summary
# ----------------------------------
# creating object of ChatGroq
llm_model = ChatGroq(
    model="llama-3.1-8b-instant",
    max_tokens=250,
    temperature=0.7
)

def generate_summary_llm(location, date, temp, humidity, wind_speed, description):
    # Inject dynamic variables into the prompt using invoke
    prompt_value = weather_prompt_template.invoke({
        "location": location,
        "date": date,
        "temp": temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "description": description,
    })
    
    # Convert Prompt Value to string for the LLM
    # prompt_text = prompt_value.to_string()
    # messages = [
    # SystemMessage(content="You are a helpful weather assistant."),
    # HumanMessage(content=prompt_text)
    # ]
    # Generate response from ChatGroq
    # response = llm_model.invoke(messages)
    # response = llm_model.invoke(
    #     messages=[
    #         (SystemMessage(content = "You are a helpful weather assistant.")),
    #         (HumanMessage(content = prompt_text))
    #     ]
    # )
    response = llm_model.invoke(prompt_value)

    #messages.append(AIMessage(content = response.content))

    return response.content
    #return (AIMessage(messages))
