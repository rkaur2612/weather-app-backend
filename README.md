<h1>Weather App</h1>

A Weather Forecast Web App built with <b>FastAPI, Jinja2, and SQLAlchemy</b>. Users can view weather forecasts for a location, see related YouTube videos for their location, update and delete records. This app also demonstrates form validation, dynamic date ranges, autocomplete for locations.

<h2>Features</h2>

Search <b>5-day weather forecast</b> for a location (City, State)
<ol>
<li>Display relevant YouTube videos for the selected location (API integration)</li>
<li>View all weather records in a table.</li>
<li>Download all weather data in CSV format.</li>
<li>Update weather records via a form.</li>
<li>Delete weather records with a confirmation prompt.</li>
<li>Autocomplete suggestions for locations.</li>
<li>Footer with developer info and PM Accelerator program details.</li>
</ol>

<h2>Use Cases</h2>

1. <b>GET WEATHER</b>: Users can input a location and date range to fetch weather data.
2. <b>READ DATA</b>: Users can view all stored weather records in a table.
3. <b>EXPORT DATA</b>: Users can export all weather records in <b>CSV</b> format.
4. <b>UPDATE DATA</b>: Users can update existing weather records by selecting the location and date.
5. <b>DELETE DATA</b>: Users can remove unwanted or incorrect weather records through a button.
6. <b>YOUTUBE INTEGRATION</b>: Users can view related videos for searched location to learn more about the area.

<h2>Tech Stack</h2>
<ul>
<li>Backend Framework: FastAPI</li>
<li>Backend Language: Python</li>
<li>Frontend: Jinja2 templates (HTML/CSS)</li>
<li>Database: SQLite</li>
<li>ORM/Database Handling: SQLAlchemy</li>
<li>Other Tools: Pandas (for CSV export), Requests (for API calls)</li>
</ul>

<h2>API Integrations</h2>
1. <b>OpenWeatherMap API</b> - Fetches real-time weather data (temperature, humidity, description, etc.) for a given location.<br/>
2. <b>YouTube Data API v3</b> - Retrieves video content related to a searched city (e.g., travel guides, news, or vlogs) to enhance user experience

<h2>Backend Perspective</h2>

Here’s how your FastAPI backend handles the core operations:

<h3>Get Weather (/weather POST)</h3>

- The backend receives location, start_date, and end_date from the form.
- Validates the location input using the autocomplete suggestions.
- Fetches weather data (from weather API or database). If data already exists for a "location + date" combination in db, then it is directly fetched from db, else API call is made.
- Returns the data to the frontend via a Jinja2 template, which renders it dynamically and returns:
   - Temperature
   - Description
   - Humidity
   - Wind Speed
   - Youtube Videos(4) for searched (from YouTube Data API v3)
 
<h3>Read Weather (/weather GET)</h3>

- Retrieves all weather records from the database.
- Sends JSON data for the frontend table or renders results in the template.

<h3>Download CSV (/export/csv GET)</h3>

- Fetches all weather records from the database.
- Generates a CSV using Python’s csv module.
- Sends the CSV as a streaming response for the user to download.

<h3>Update Weather (/weather/update POST)</h3>

- Receives location, date, and value for fields to update.
- Validates location and date.
- Updates only the provided fields in the database using SQLAlchemy.(If any field is left blank, ex wind speed - the existing databse value is retained)
- Returns the updated record to the frontend for confirmation.

<h3>Delete Weather (/delete/{id} POST)</h3>

- Receives the unique record id from the frontend when user clicks on delete button for a particular record.
- Deletes the corresponding record in the database after user confirmation.
- Returns a success message to the frontend.

<h2>Database Structure</h2>

| Column Name   | Data Type | Constraints                 | Description                               |
| ------------- | --------- | --------------------------- | ----------------------------------------- |
| `id`          | Integer   | Primary Key, Auto Increment | Unique identifier for each weather record |
| `location`    | varchar   | NOT NULL                    | Name of the city, State                   |
| `temperature` | Float     | NOT NULL                    | Current temperature of the city           |
| `description` | varchar   | NOT NULL                    | Weather description (e.g., cloudy, sunny) |
| `humidity`    | Integer   |                             | Humidity percentage                       |
| `wind_speed`  | float     |                             |                                           |




Weather Table:<br/>
<img width="209" height="163" alt="image" src="https://github.com/user-attachments/assets/31579ec1-e516-4dc8-b112-a8721e55fa3f" />

<br/>Example with Data:<br/>
<img width="583" height="281" alt="image" src="https://github.com/user-attachments/assets/118fbad4-dafc-4a84-8e39-18fed64c291d" />

<h2>How to Run the App</h2>

1. <b>Clone the repository</b>
   - git clone https://github.com/rkaur2612/weather-app-backend.git
   - In terminal enter command : cd weather-app-backend

2. <b>Install dependencies</b>
   - pip install -r requirements.txt

3. <b>Run the FastAPI server</b><br/>
   From the root folder (weather-app-backend), run:
   - uvicorn app.main:app --reload

       - app.main:app → points to main.py inside the app folder where app = FastAPI() is defined.
       - --reload → automatically reloads the server when you change code.

4. <b>Open the app in your browser</b>:
   - Got to http://127.0.0.1:8000/
   - You should see the Weather App homepage.


<H3>Debugging Steps</H3>
If any issues related to installing dependencies, recommendation is to use virtual environment





