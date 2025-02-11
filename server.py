from fastapi import FastAPI, HTTPException, Query
import requests
from datetime import datetime
import uvicorn

app = FastAPI()

#Replace with your actual Indeed Publisher ID
PUBLISHER_ID = "API KEY DO NOT COMMIT TODO MAKE .ENV file"

#adam updated 2/10/2025
def get_indeed_jobs(query: str, location: str, sort_by: str = "date", limit: int = 25):
    """
    Calls the Indeed API with the given query and location,
    then processes and returns the job listings
    """
    base_url = "http://api.indeed.com/ads/apisearch"
    
    #Define query parameters based on Indeed API specs
    params = {
        "publisher": PUBLISHER_ID,
        "q": query,
        "l": location,
        "sort": "",          #Sorting is handled locally.
        "radius": "25",      #Radius in miles adjust as needed.
        "st": "",
        "jt": "",
        "start": "0",
        "limit": limit,
        "fromage": "7",      #Jobs posted within the last 7 days.
        "filter": "1",
        "latlong": "1",
        "co": "us",
        "format": "json",
        "v": "2"
    }
    
    #Make the GET request to the Indeed API
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Indeed API request failed: {response.status_code} - {response.text}")
    
    data = response.json()
    jobs = data.get("results", [])
    
    #Sorting logic
    if sort_by == "date":
        #Parse date strings into datetime objects. Adjust the format as needed
        for job in jobs:
            date_str = job.get("date", "")
            try:
                job["parsed_date"] = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            except Exception:
                #If parsing fails, assign a default minimum datetime
                job["parsed_date"] = datetime.min
        
        #Sort by parsed_date in descending order most recent first
        jobs = sorted(jobs, key=lambda x: x["parsed_date"], reverse=True)
        #Remove the temporary parsed_date key before returning
        for job in jobs:
            job.pop("parsed_date", None)
    
    elif sort_by == "jobtitle":
        #Sort alphabetically by job title.
        jobs = sorted(jobs, key=lambda x: x.get("jobtitle", ""))
    
    #You can add additional sorting methods here if needed
    
    return jobs


#adam updated 2/10/2025
@app.get("/api/jobs")
async def get_jobs(
    query: str = Query(..., description="Job search keyword(s)"),
    location: str = Query(..., description="Location for the job search"),
    sort_by: str = Query("date", description="Sort results by 'date' or 'jobtitle'"),
    limit: int = Query(25, description="Maximum number of results to return")
):
    """
    API endpoint that returns job listings from the Indeed API.
    
    Query Parameters:
    - query: The job search keywords.
    - location: The location to search.
    - sort_by: Sort results by 'date' default or jobtitle.
    - limit: Maximum number of results to return.
    """
    try:
        results = get_indeed_jobs(query, location, sort_by, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#adam updated 2/10/2025
if __name__ == "__main__":
    #Run
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
