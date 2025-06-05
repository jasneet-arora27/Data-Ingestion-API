from uuid import uuid4
import time

def generate_ingestion_id():
    return str(uuid4())

def simulate_external_api_response(id):
    time.sleep(1)  # Simulate a delay for fetching data
    return {"id": id, "data": "processed"}