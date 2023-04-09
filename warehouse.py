import pika
import json
import sys
import pymongo
from datetime import datetime, timedelta

mongo_username = "plazadruben"
mongo_password = "5tjFpgtRqjjS26QX"

client = pymongo.MongoClient("mongodb+srv://plazadruben:5tjFpgtRqjjS26QX@warehouse-data.lyyeoya.mongodb.net/?retryWrites=true&w=majority")
db = client["warehouse-data"]
inventory_db = db["inventory"]


# Configuration
RABBITMQ_HOST = "localhost"
WAREHOUSE_ID = sys.argv[1]

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.exchange_declare(exchange="orders", exchange_type="direct")
channel.exchange_declare(exchange="delivery_schedules", exchange_type="direct")

# Global variables for inventory and vehicle capacities
#inventory = {"tshirt": 500, "xbox": 200, "playstation":213, "sweater": 532, "pants": 1900, "shoes": 123}
warehouse_capacity = 1000
vehicle_capacity = 100

# wh_obj = {
#     "warehouse_id" : WAREHOUSE_ID,
#     "items": {"tshirt": 500, "xbox": 200, "playstation":213, "sweater": 532, "pants": 1900, "shoes": 123}
# }

# inventory_db.insert_one(wh_obj);

from_db = inventory_db.find_one({ "warehouse_id": WAREHOUSE_ID })

inventory = from_db["items"]


# Delivery vehicle statuses
delivery_vehicles = {
    "vehicle_1": {"capacity": vehicle_capacity, "orders": []},
    "vehicle_2": {"capacity": vehicle_capacity, "orders": []},
    "vehicle_3": {"capacity": vehicle_capacity, "orders": []},
}

def process_order(order):
    product_id = order["product_id"]
    quantity = order["quantity"]

    if not product_id in inventory.keys():
        #Product doesnt exist error
        return f"Product {product_id} not sold."
    
    global vehicle_available 
    vehicle_available = False
    for vehicle_id, vehicle in delivery_vehicles.items():
        if vehicle["capacity"] >= quantity:
            vehicle_available = True

    if not vehicle_available: 
        return f"No available vehicle for order {order['id']}: {product_id} x {quantity}"

    # Check if there is enough inventory for the order
    if inventory[product_id] >= quantity:
        # Update inventory
        query = {"warehouse_id": WAREHOUSE_ID}
        new_values = {"$set": {"items": inventory}}
        inventory[product_id] -= quantity
        inventory_db.update_one(query, new_values)
    else:
        return f"Insufficient inventory for order {order['id']}: {product_id} x {quantity}"

    # Check if there is enough capacity in any delivery vehicle
   
    for vehicle_id, vehicle in delivery_vehicles.items():
        if vehicle["capacity"] >= quantity:
            # Assign the order to the vehicle and update the capacity
            vehicle["orders"].append(order["id"])
            vehicle["capacity"] -= quantity
            currentDate = datetime.now().date()
            deliveryDate = currentDate + timedelta(days=10)
            return f"Assigned order {order['id']} to {vehicle_id}. Your order will be delivered on {deliveryDate}"
  

    # If needed, update the central system and/or the delivery vehicles

def on_order_received(ch, method, properties, body):
    order = json.loads(body)
    print(f"Received order {order['id']} for {order['product_id']} x {order['quantity']}")
    temp = process_order(order)
    temp_return = {"message": temp}
    channel.basic_publish(
        exchange="orders", routing_key="placed_orders", body=json.dumps(temp_return)
    )

channel.queue_declare(queue="placed_orders")
channel.queue_bind(exchange="orders", queue="placed_orders")   

# Bind the queue to the exchange and set the routing key as the warehouse ID
queue_name = f"warehouse{WAREHOUSE_ID}_orders"
channel.queue_declare(queue=queue_name)
channel.queue_bind(exchange="orders", queue=queue_name, routing_key=WAREHOUSE_ID)

# Function to handle incoming delivery schedule updates
def on_delivery_schedule_received(ch, method, properties, body):
    schedule_message = json.loads(body)
    vehicle_id = schedule_message["vehicle_id"]
    schedule = schedule_message["schedule"]

    # Update the delivery vehicle's schedule
    delivery_vehicles[vehicle_id]["orders"] = schedule
    print(f"Updated delivery schedule for {vehicle_id}: {schedule}")

# Bind the delivery schedules queue to the delivery_schedules exchange and set the routing key as the warehouse ID
schedules_queue_name = f"warehouse{WAREHOUSE_ID}_schedules"
channel.queue_declare(queue=schedules_queue_name)
channel.queue_bind(exchange="delivery_schedules", queue=schedules_queue_name, routing_key=WAREHOUSE_ID)

# Start consuming orders and delivery schedules
print(f"[*] Warehouse {WAREHOUSE_ID} waiting for orders and delivery schedules.")
channel.basic_consume(queue=queue_name, on_message_callback=on_order_received, auto_ack=True)
channel.basic_consume(queue=schedules_queue_name, on_message_callback=on_delivery_schedule_received, auto_ack=True)
channel.start_consuming()