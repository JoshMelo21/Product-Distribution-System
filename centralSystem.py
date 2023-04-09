import pika
import json
import uvicorn
import sys
import threading
import pymongo
from time import sleep
from fastapi import FastAPI
from pydantic import BaseModel

mongo_username = "plazadruben"
mongo_password = "5tjFpgtRqjjS26QX"

client = pymongo.MongoClient("mongodb+srv://plazadruben:5tjFpgtRqjjS26QX@warehouse-data.lyyeoya.mongodb.net/?retryWrites=true&w=majority")
db = client["warehouse-data"]
inventory_db = db["inventory"]


from_db = list(inventory_db.find({}))

inventories = {}

for warehouse in from_db:
    inventories[warehouse["warehouse_id"]] = warehouse["items"]


app = FastAPI()

class Order(BaseModel):
    id: str
    product_id: str
    quantity: int
    shipping_address: dict

class DeliveryStatus(BaseModel):
    order_id: str
    status: str

# In-memory data storage for orders and delivery statuses
orders = {}
delivery_statuses = {}
warehouses = ["A", "B", "C"]
return_message = ""
current_order_id = 0

@app.post("/orders", status_code=201)
async def create_order(order: Order):
    # Determine the warehouse and process the order using your existing logic
    # For example, call the determine_warehouse(order) function and process_order(order) function
    global return_message
    oldReturnMessage = return_message
    warehouse_id = receive_order_from_customer(order)

    if warehouse_id == "No Warehouse":
        return {"message": "No Warehouse"}

    while oldReturnMessage == return_message:
        sleep(1)
    temp_return_message = return_message
    return_message = ""

    if "Assigned" in temp_return_message:
        # Add the order to the in-memory storage
        global current_order_id
        orders[str(current_order_id)] = order

        # Update the delivery status
        delivery_statuses[str(current_order_id)] = "Processing"
        current_order_id += 1
        return {"message": temp_return_message, "order_id": str(current_order_id-1), "warehouse_id": warehouse_id}
    
    else:
        return {"message": temp_return_message, "warehouse_id": warehouse_id}

@app.get("/delivery_status/{order_id}")
async def get_delivery_status(order_id: str):
    if order_id not in delivery_statuses:
        return {"message": "Order not found"}, 404

    return {"order_id": order_id, "status": delivery_statuses[order_id]}

# Configuration
RABBITMQ_HOST = "localhost"

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.exchange_declare(exchange="orders", exchange_type="direct")

channel.queue_declare(queue="placed_orders")
channel.queue_bind(exchange="orders", queue="placed_orders", routing_key="placed_orders")   


def send_order_to_warehouse(order, warehouse_id):
    channel.basic_publish(
        exchange="orders", routing_key=warehouse_id, body=json.dumps(order.dict())
    )

def receive_order_from_customer(order):
    warehouse_id = determine_warehouse(order)
    if warehouse_id == None:
        return "No Warehouse"
    send_order_to_warehouse(order, warehouse_id)
    return warehouse_id



def determine_warehouse(order):
    order_zip_code = order.shipping_address["zip_code"]
    order_product_id = order.product_id
    order_quantity = order.quantity

    if order_zip_code[0] != "A" and order_zip_code[0] != "B" and order_zip_code[0] != "C":
        return None
    
    w_ids = [order_zip_code[0]]
    if "A" not in w_ids:
        w_ids.append("A")
    if "B" not in w_ids:
        w_ids.append("B")
    if "C" not in w_ids:
        w_ids.append("C")

    for i in w_ids:
        current_inventory = inventories[i]
        if current_inventory[order_product_id] >= order_quantity:
            return i
        
    return None

def consume_placed_orders(ch, method, properties, body):
    global return_message
    return_message = json.loads(body)["message"]


def uvicorn_thread():
    uvicorn.run(app, host="localhost", port=8001)

def rabbit_thread():
    print("Consuming")
    channel.basic_consume(queue="placed_orders", on_message_callback=consume_placed_orders, auto_ack=True)
    channel.start_consuming()


if __name__ == '__main__':
    try:
        uvi = threading.Thread(target=uvicorn_thread)
        mq_thread = threading.Thread(target=rabbit_thread)

        uvi.start()
        mq_thread.start()

        uvi.join()
        mq_thread.join()
    except KeyboardInterrupt:
        sys.exit(1)
        
    
