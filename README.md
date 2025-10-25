README.md
markdown
# Country Data API

A RESTful API that fetches country data from external APIs, stores it in MySQL, and provides CRUD operations with GDP estimation.

## Features

- Fetch country data from REST Countries API
- Get exchange rates from Exchange Rate API
- Calculate estimated GDP based on population and exchange rates
- CRUD operations for country data
- Filtering and sorting capabilities
- Summary image generation
- MySQL database integration

## Setup Instructions

### Prerequisites

- Python 3.8+
- MySQL 5.7+
- Redis (optional, for Celery)

### Installation
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd country_api
Create virtual environment

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install -r requirements.txt
Environment configuration

bash
cp .env.example .env
# Edit .env with your database credentials
Database setup

sql
CREATE DATABASE country_api;
Run migrations

bash
python manage.py migrate
Create superuser (optional)

bash
python manage.py createsuperuser
Running the Application
Development server:

bash
python manage.py runserver
The API will be available at http://localhost:8000

API Endpoints
POST /countries/refresh
Fetch and refresh all countries data from external APIs.

GET /countries
Get all countries with optional filtering and sorting.

Query parameters:
region: Filter by region (e.g., Africa)
currency: Filter by currency code (e.g., USD)
sort: Sort by field (gdp_desc, gdp_asc, population_desc, population_asc, name_asc, name_desc)

GET /countries/{name}
Get specific country by name.

DELETE /countries/{name}
Delete country by name.

GET /status
Get API status and statistics.

GET /countries/image
Get generated summary image.

Example Usage
bash
# Refresh countries data
curl -X POST http://localhost:8000/countries/refresh/

# Get all countries in Africa
curl "http://localhost:8000/countries/?region=Africa"

# Get countries sorted by GDP descending
curl "http://localhost:8000/countries/?sort=gdp_desc"

# Get specific country
curl http://localhost:8000/countries/Nigeria

# Get API status
curl http://localhost:8000/status/
Environment Variables
SECRET_KEY: Django secret key

DEBUG: Debug mode (True/False)

ALLOWED_HOSTS: Comma-separated list of allowed hosts

DB_NAME: MySQL database name
DB_USER: MySQL username
DB_PASSWORD: MySQL password
DB_HOST: MySQL host
DB_PORT: MySQL port

REDIS_URL: Redis connection URL (optional)

Deployment
The application can be deployed on various platforms:

Railway
Heroku
AWS Elastic Beanstalk
DigitalOcean App Platform
PythonAnywhere

Make sure to set appropriate environment variables in your deployment platform.

Testing
Run the test suite:

bash
python manage.py test
API Documentation
The API returns consistent JSON responses and follows RESTful conventions. All endpoints return JSON format.

Error Responses
400 Bad Request: Validation failed
404 Not Found: Resource not found
503 Service Unavailable: External API unavailable
500 Internal Server Error: Server error

text

## Deployment Instructions

This Django application can be deployed on various platforms. Here are some options:

### Railway Deployment

1. Create account on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy automatically from GitHub

### Heroku Deployment

1. Install Heroku CLI
2. Create `Procfile`:
web: gunicorn country_api.wsgi --log-file -

text
3. Create `runtime.txt` with Python version
4. Deploy using Heroku Git

### AWS Elastic Beanstalk

1. Install EB CLI
2. Initialize EB application
3. Configure environment variables
4. Deploy using EB CLI
