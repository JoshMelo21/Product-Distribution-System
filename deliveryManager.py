import pika
import json

# Configuration
RABBITMQ_HOST = "localhost"

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.exchange_declare(exchange="delivery_schedules", exchange_type="direct")

# Delivery schedules
delivery_schedules = {
    "vehicle_1": [],
    "vehicle_2": [],
    # Add more vehicles as needed
}

def update_delivery_schedule(order, vehicle_id):
    # Update the delivery schedule for the vehicle
    delivery_schedules[vehicle_id].append(order["id"])

    # Send the updated delivery schedule to the Warehouse application using RabbitMQ
    schedule_message = {
        "vehicle_id": vehicle_id,
        "schedule": delivery_schedules[vehicle_id],
    }
    warehouse_id = order["warehouse_id"]
    channel.basic_publish(
        exchange="delivery_schedules",
        routing_key=warehouse_id,
        body=json.dumps(schedule_message),
    )
    print(f"Updated delivery schedule for {vehicle_id}: {delivery_schedules[vehicle_id]}")

# Sample usage
sample_order = {
    "id": "order_1",
    "product_id": "product_1",
    "quantity": 10,
    "warehouse_id": "1",
}
sample_vehicle_id = "vehicle_1"
update_delivery_schedule(sample_order, sample_vehicle_id) 