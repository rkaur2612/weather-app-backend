#backup main

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests

from app.database import SessionLocal, engine
import app.models as models

# Create tables if not exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Setup Jinja2 templates folder
templates = Jinja2Templates(directory="app/templates") 

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home page route: shows the input form
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Route to search valid locations
# @app.get("/search_location", response_class=HTMLResponse)
# def search_location(request: Request, q: str):
#     try:
#         response = requests.get(
#             "https://api.weatherapi.com/v1/search.json",
#             params={"key": "04dcb7c9e5154d13a68191510252808", "q": q}
#         )
#         locations = response.json()
#         # Return list of names
#         location_names = [loc["name"] + (", " + loc["region"] if loc.get("region") else "") for loc in locations]
#         return {"locations": location_names}
#     except Exception as e:
#         return {"locations": [], "error": str(e)}
    
# Route to search valid locations (autocomplete)
@app.get("/search_location", response_class=JSONResponse)
def search_location(q: str):
    try:
        if not q or len(q) < 2:
            return {"locations": []}

        response = requests.get(
            "https://api.weatherapi.com/v1/search.json",
            params={"key": "04dcb7c9e5154d13a68191510252808", "q": q}
        )
        locations = response.json()

        location_names = [
            loc["name"] + (", " + loc["region"] if loc.get("region") else "") for loc in locations
        ]
        return {"locations": location_names}

    except Exception as e:
        return {"locations": [], "error": str(e)}

# Weather route with date range
@app.post("/weather", response_class=HTMLResponse)
def get_weather(
    request: Request,
    location: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        today = datetime.today().date()
        max_forecast_date = today + timedelta(days=5)

        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Validate date range
        if start > end:
            return templates.TemplateResponse(
                "index.html", {"request": request, "error": "Start date must be before end date"}
            )
        if start < today or end > max_forecast_date:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "error": f"Please select dates between today ({today}) and next 5 days ({max_forecast_date})"
                }
            )

        # First, validate location with API (call once)
        api_response = requests.get(
            "https://api.weatherapi.com/v1/forecast.json",
            params={"key": "04dcb7c9e5154d13a68191510252808", "q": location, "days": 5}
        )
        api_data = api_response.json()
        forecast_days = api_data.get("forecast", {}).get("forecastday", [])

        if not forecast_days:
            # Location not found or API returned no forecast
            return templates.TemplateResponse(
                "index.html", {"request": request, "error": f"Location '{location}' not found or invalid."}
            )

        current = start
        results = []

        while current <= end:
            # Check DB first
            weather_entry = db.query(models.Weather).filter_by(location=location, date=current).first()

            if weather_entry:
                # Fetch from DB
                results.append({
                    "location": weather_entry.location,
                    "date": weather_entry.date.strftime("%Y-%m-%d"),
                    "temperature": weather_entry.temperature,
                    "description": weather_entry.description,
                    "humidity": weather_entry.humidity,
                    "wind_speed": weather_entry.wind_speed
                })
            else:
                # Find forecast for current date from API data
                date_str = current.strftime("%Y-%m-%d")
                forecast_day = next(
                    (day for day in forecast_days if day["date"] == date_str),
                    None
                )

                if forecast_day:
                    forecast = forecast_day["day"]
                    temp = forecast["avgtemp_c"]
                    description = forecast.get("condition", {}).get("text", "No data")
                    humidity = forecast.get("avghumidity")
                    wind_speed = forecast.get("maxwind_kph")

                    # Save to DB
                    weather_entry = models.Weather(
                        location=location,
                        date=current,
                        temperature=temp,
                        description=description,
                        humidity=humidity,
                        wind_speed=wind_speed
                    )
                    db.add(weather_entry)
                    db.commit()
                    db.refresh(weather_entry)

                    results.append({
                        "location": location,
                        "date": date_str,
                        "temperature": temp,
                        "description": description,
                        "humidity": humidity,
                        "wind_speed": wind_speed
                    })
                else:
                    # No data for this date
                    results.append({
                        "location": location,
                        "date": date_str,
                        "temperature": None,
                        "description": "No data",
                        "humidity": None,
                        "wind_speed": None
                    })

            current += timedelta(days=1)

        return templates.TemplateResponse(
            "index.html", {"request": request, "weather_data": results}
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": str(e)}
        )