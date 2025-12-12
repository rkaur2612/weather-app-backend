from langchain_core.prompts import PromptTemplate

weather_prompt_template = PromptTemplate(
    input_variables=["location", "date", "temp", "humidity", "wind_speed", "description"],
    validate_template = True,
    template="""
You are a helpful assistant that converts raw weather data into a clear, concise, and friendly daily weather summary for a user.

Input Data:
- Location: {location}
- Date: {date}
- Forecast:
  - Temperature: {temp}°C
  - Humidity: {humidity}%
  - Wind: {wind_speed} km/h
  - Description: {description}

Instructions:
- Write a short paragraph (2-3 sentences) summarizing the weather.
- Mention key aspects: temperature, wind, humidity, and description.
- Do NOT use the location as if it were a person’s name. Mention it neutrally in the summary.
- Make it human-friendly and easy to read, but avoid greetings like "Hey there".
- Friendly, casual tone.
"""
)