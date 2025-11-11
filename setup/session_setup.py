import requests
from requests.adapters import HTTPAdapter, Retry


# Create a session and define a retry strategy. Used for API calls.
session = requests.Session()
retry_strategy = Retry(
    total=10, # Maximum number of retries.
    backoff_factor=0.5, 
    status_forcelist=[429, 500, 502, 503, 504] # HTTP status codes to retry on.
)
session.mount('http://', HTTPAdapter(max_retries=retry_strategy))