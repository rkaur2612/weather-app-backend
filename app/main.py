from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests
import csv
from typing import List
from io import StringIO
from fastapi import HTTPException, status
from app.database import SessionLocal, engine
import app.models as models
from fastapi.staticfiles import StaticFiles

# Create tables if not exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Setup Jinja2 templates folder
templates = Jinja2Templates(directory="app/templates") 

# Mount the 'static' folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home page route: shows the input form
@app.get("/", response_class=HTMLResponse)
def home(request: Request, success_delete: str = None): #type: ignore
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "success_delete": success_delete
        }
    )
    
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
        
        # Fetch YouTube videos for the location
        youtube_videos = []
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": location,
                "type": "video",
                "maxResults": 4,
                "key": "AIzaSyC_EuXYPqDzUkt1u9bF6bOUzxLXdNoLzmM"
            }
            yt_response = requests.get(url, params=params)
            yt_data = yt_response.json()
            for item in yt_data.get("items", []):
                youtube_videos.append({
                    "title": item["snippet"]["title"],
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                    "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
        except Exception as e:
            youtube_videos = []

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "weather_data": results,
                "youtube_videos": youtube_videos,
                "location": location
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": str(e)}
        )
    
@app.get("/weather")
def get_all_weather(db: Session = Depends(get_db)):
    records = db.query(models.Weather).all()
    return [
        {
            "id": r.id,  # <-- include the unique ID
            "location": r.location,
            "date": r.date.strftime("%Y-%m-%d"),
            "temperature": r.temperature,
            "description": r.description,
            "humidity": r.humidity,
            "wind_speed": r.wind_speed
        }
        for r in records
    ]

@app.get("/export/csv")
def export_weather_csv(db: Session = Depends(get_db)):
    # Fetch all weather records
    records = db.query(models.Weather).all()
    
    # Create a CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Location", "Date", "Temperature(°C)", "Description", "Humidity(%)", "Wind Speed(kph)"])
    
    # Write data rows
    for rec in records:
        writer.writerow([rec.location, rec.date, rec.temperature, rec.description, rec.humidity, rec.wind_speed])
    
    output.seek(0)
    
    # Return as downloadable file
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=weather_data.csv"}
    )

@app.post("/weather/update", response_class=HTMLResponse)
def update_weather(
    request: Request,
    location: str = Form(...),
    date: str = Form(...),
    temperature: str = Form(""),
    description: str = Form(""),
    humidity: str = Form(""),
    wind_speed: str = Form(""),
    db: Session = Depends(get_db)
):
    try:
        # Parse and validate date
        try:
            record_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return templates.TemplateResponse(
                "index.html", {"request": request, "error_update": "Invalid date format"}
            )

        # Find record
        weather_entry = db.query(models.Weather).filter_by(location=location, date=record_date).first()
        if not weather_entry:
            return templates.TemplateResponse(
                "index.html", {"request": request, "error_update": f"No record found for {location} on {date}"}
            )

        # Update temperature if provided
        if temperature.strip() != "":
            try:
                temp_val = float(temperature)
                if temp_val < -100 or temp_val > 100:
                    return templates.TemplateResponse(
                        "index.html", {"request": request, "error_update": "Temperature out of range. Please enter a value between -100°C and 100°C."}
                    )
                weather_entry.temperature = temp_val # type: ignore
            except ValueError:
                return templates.TemplateResponse(
                    "index.html", {"request": request, "error_update": "Invalid temperature. Please enter a valid number (e.g., 23.5)."}
                )

        # Update humidity if provided
        if humidity.strip() != "":
            try:
                hum_val = int(humidity)
                if hum_val < 0 or hum_val > 100:
                    return templates.TemplateResponse(
                        "index.html", {"request": request, "error_update": "Humidity out of range. Please enter a value between 0% and 100%."}
                    )
                weather_entry.humidity = hum_val # type: ignore
            except ValueError:
                return templates.TemplateResponse(
                    "index.html", {"request": request, "error_update": "Invalid humidity. Please enter a whole number (e.g., 55)."}
                )

        # Update wind_speed if provided
        if wind_speed.strip() != "":
            try:
                wind_val = float(wind_speed)
                if wind_val < 0:
                    return templates.TemplateResponse(
                        "index.html", {"request": request, "error_update": "Wind speed cannot be negative. Please enter a value of 0 or higher"}
                    )
                weather_entry.wind_speed = wind_val # type: ignore
            except ValueError:
                return templates.TemplateResponse(
                    "index.html", {"request": request, "error_update": "Invalid wind speed. Please enter a valid number"}
                )

        # Update description if provided
        if description.strip() != "":
            weather_entry.description = description # type: ignore

        db.commit()
        db.refresh(weather_entry)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "success_update": f"Weather record for {location} on {date} updated successfully",
                "updated_weather": [weather_entry]  # optionally show updated record
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error_update": str(e)}
        )

@app.post("/delete/{weather_id}")
def delete_weather(weather_id: int, db: Session = Depends(get_db)):
    weather_entry = db.query(models.Weather).filter_by(id=weather_id).first()
    if not weather_entry:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(weather_entry)
    db.commit()

    # Redirect back to home page with a success message
    message = f"Weather record for {weather_entry.location} on {weather_entry.date.strftime('%Y-%m-%d')} deleted successfully."
    return RedirectResponse(url=f"/?success_delete={message}", status_code=303)


# YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"
# @app.get("/youtube_videos", response_class=HTMLResponse)
# def youtube_videos(request: Request, location: str = "", max_results: int = 5):
#     if not location:
#         return templates.TemplateResponse("index.html", {"request": request, "error_youtube": "No location provided"})
    

#     # YouTube search API URL
#     url = "https://www.googleapis.com/youtube/v3/search"
#     params = {
#         "part": "snippet",
#         "q": location,
#         "type": "video",
#         "maxResults": max_results,
#         "key": "AIzaSyC_EuXYPqDzUkt1u9bF6bOUzxLXdNoLzmM"
#     }
#     youtube_videos = []
#     try:
#         yt_response = requests.get(url, params=params)
#         yt_data = yt_response.json()
#         for item in yt_data.get("items", []):
#             youtube_videos.append({
#                 "title": item["snippet"]["title"],
#                 "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
#                 "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
#             })
#     except Exception as e:
#         youtube_videos = []