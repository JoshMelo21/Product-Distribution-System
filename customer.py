from fastapi import FastAPI
from pydantic import BaseModel
import requests
import uvicorn
import sys

app = FastAPI()

# Replace this URL with the actual URL of your central system's RESTful API
CENTRAL_SYSTEM_API_URL = "http://localhost:8001"

class Order(BaseModel):
    id: str
    product_id: str
    quantity: int
    shipping_address: dict

class DeliveryStatus(BaseModel):
    order_id: str
    status: str

@app.post("/place_order")
async def place_order(order: Order):
    response = requests.post(f"{CENTRAL_SYSTEM_API_URL}/orders", json=order.dict())
    if response.status_code == 201:
        return response.json()
    else:
        return {"message": "Failed to place the order"}

@app.get("/track_delivery/{order_id}")
async def track_delivery(order_id: str):
    response = requests.get(f"{CENTRAL_SYSTEM_API_URL}/delivery_status/{order_id}")
    if response.status_code == 200:
        delivery_status = response.json()
        return {"message": "Delivery status retrieved successfully", "status": delivery_status}
    else:
        return {"message": "Failed to retrieve delivery status"}
    
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)    