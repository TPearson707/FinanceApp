#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

def search_jobs(title: str = "Software Engineer", location: str = "San Francisco", job_type: str = "null"):
    """
    Searches for job listings using the JobData API with the given parameters.
    """
    # API endpoint (update if necessary per JobData API documentation)
    url = "https://jobdataapi.com/api/jobs"

    # Hard-coded (or dynamic) search parameters
    params = {
        "title": title,         # Job title to search for
        "location": location,   # Location filter
        "job_type": job_type    # Job type filter
    }

    # Use the public API key (or replace YOUR_API_KEY with your actual API key if available)
    headers = {"Authorization": "Api-Key YOUR_API_KEY"}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        print("Error fetching jobs:", e)
        return None

@app.get("/jobs")
async def get_jobs(
    title: str = "Software Engineer",
    location: str = "San Francisco",
    job_type: str = "null"
):
    """
    API endpoint to retrieve job listings.
    
    Query parameters:
    - **title**: Job title to search for (default: "Software Engineer")
    - **location**: Location filter (default: "San Francisco")
    - **job_type**: Job type filter (default: "null")
    """
    result = search_jobs(title, location, job_type)
    if result is None:
        raise HTTPException(status_code=404, detail="No results returned or an error occurred.")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
