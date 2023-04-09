import argparse
import requests
import json

# Replace this URL with the actual URL of your customer interface's FastAPI application
CUSTOMER_INTERFACE_API_URL = "http://localhost:8000"

def place_order(name,quantity,zip_code):
    order = {
        "id": "0",
        "product_id": name,
        "quantity": quantity,
        "shipping_address": {
            "zip_code": zip_code,
        },
    }
    response = requests.post(f"{CUSTOMER_INTERFACE_API_URL}/place_order", json=order)
    return(response.json())

def track_delivery(args):
    response = requests.get(f"{CUSTOMER_INTERFACE_API_URL}/track_delivery/{args.order_id}")
    print(response.json())


while True:
    product_name = input("Enter Product Name: ")
    quantity = input("Enter amount you want to order: ")
    zip_code = input("Enter your zip code: ")
    response = place_order(product_name,quantity,zip_code)
    print(response)

# parser = argparse.ArgumentParser(description="CLI app for interacting with the Customer Interface API")
# subparsers = parser.add_subparsers()

# # Place order command
# place_order_parser = subparsers.add_parser("place_order", help="Place an order")
# place_order_parser.add_argument("--order_id", default="0",help="Order ID")
# place_order_parser.add_argument("--product_id", required=True, help="Product ID")
# place_order_parser.add_argument("--quantity", required=True, type=int, help="Quantity")
# place_order_parser.add_argument("--street", required=True, help="Shipping address street")
# place_order_parser.add_argument("--city", required=True, help="Shipping address city")
# place_order_parser.add_argument("--state", required=True, help="Shipping address state")
# place_order_parser.add_argument("--zip_code", required=True, help="Shipping address zip code")
# place_order_parser.set_defaults(func=place_order)

# # Track delivery command
# track_delivery_parser = subparsers.add_parser("track_delivery", help="Track a delivery")
# track_delivery_parser.add_argument("--order_id", required=True, help="Order ID")
# track_delivery_parser.set_defaults(func=track_delivery)

# args = parser.parse_args()
# args.func(args)