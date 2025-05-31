import json
from datetime import datetime
import requests as r 


index_url = "https://www.mdcalc.com/_next/data/mbFTGi54cglQw_5xbY1ey/index.json"

def fetch_index():
    print(f"Fetching index from {index_url} at {datetime.now()}")
    response = r.get(index_url)
    
    if response.status_code != 200:
        print(f"Error fetching index: {response.status_code}")
        return None
    else:
        print(response.headers)
        return response.json()