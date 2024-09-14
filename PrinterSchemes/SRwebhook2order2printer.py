from flask import Flask, request, jsonify
import json
import requests
from flask_ngrok2 import run_with_ngrok
from square.client import Client
from square.http.auth.o_auth_2 import BearerAuthCredentials
import cups
from ttpDependencies import config
import subprocess
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
retrieve_order_path = os.path.join(base_dir, 'ttpDependencies', 'retrieve_order.py')

#def format_line(item, qty, price):
    #"""
    #Format a single line of the receipt.
    #"""
    #line = f"{item:<20} {qty:>5}  {price:>10.2f}"
    #return line
#[Konstantin, Rosen, Ivanov, Colin]
employees = config.employee_devices
def generate_receipt_text(receipt_text):
    """
    Generate a formatted receipt text based on the provided input.
    """
    #lines = receipt_text.splitlines()
    #items = []
    #total = 0.0

    #for line in lines:
        #if line.strip():
            #parts = line.split(",")
            #if len(parts) == 3:
                #item_name = parts[0].strip()
                #quantity = int(parts[1].strip())
                #price = float(parts[2].strip())
                #total += quantity * price
                #items.append((item_name, quantity, price))
    
    receipt_output = []
    receipt_output.append("Order Ticket".center(40, "-"))
    #receipt_output.append("Item                Qty       Price")
    receipt_output.append("-" * 40)

    #for item_name, quantity, price in items:
        #receipt_output.append(format_line(item_name, quantity, price))
    receipt_output.append(receipt_text)
    receipt_output.append("-" * 40)
    #receipt_output.append(f"{'Total':<20} {total:>15.2f}")
    receipt_output.append("-" * 40)

    return "\n".join(receipt_output)

def print_receipt_cups(receipt_text):
    """
    Print the generated receipt text using CUPS.
    """
    # Generate the formatted receipt text
    receipt_output = generate_receipt_text(receipt_text)

    # Create a temporary file to store the receipt text
    with open('/tmp/receipt.txt', 'w') as receipt_file:
        receipt_file.write(receipt_output)

    # Get the default printer
    conn = cups.Connection()
    printers = conn.getPrinters()
    #change default printer to TSP printer
    #default_printer = list(printers.keys())[0]
    tickPrinter= config.tickPrinter

    # Print the receipt
    conn.printFile(tickPrinter, '/tmp/receipt.txt', "Receipt", {})

#bearer_auth_credential = BearerAuthCredentials(
#access_token = SQ_ACCESS_TOKEN)

#client = Client(
    #bearer_auth_credentials=bearer_auth_credential,
    #environment=ENVIRONMENT  # Change to 'sandbox' if you're using the sandbox environment)
    #

def sretrieve_order(order_id):
    try:
        # Call the RetrieveOrder endpoint
        response = client.orders.retrieve_order(order_id=order_id)

        if response.is_success():
            receipt_text=""
            order = response.body['order']
            order_notes = order.get('note', 'No general notes found. ')
            print(f"Order Notes: {order_notes}")
            receipt_text= receipt_text + f"Order Notes: {order_notes}"
            line_items = order.get('line_items', [])
            print(f"Order ID: {order_id}")
            #receipt_text = receipt_text + f"Order ID: {order_id}"
            print("Line Items:")
            receipt_text = receipt_text + "Line Items:"
            for item in line_items:
                print(f" - Name: {item['name']}")
                receipt_text = receipt_text + f" - Name: {item['name']}"
                print(f"   Quantity: {item['quantity']}")
                receipt_text = receipt_text + f"   Quantity: {item['quantity']}"
                print(f"   Total Money: {item['total_money']['amount']} {item['total_money']['currency']}")
                receipt_text = receipt_text + f"   Total Money: {item['total_money']['amount']} {item['total_money']['currency']}"
                # Print line item notes
                item_note = item.get('note', 'No note for this item')
                print(f"  Item Note: {item_note}")
                receipt_text = receipt_text + f"  Item Note: {item_note}"
                
                # Check and print modifiers
                modifiers = item.get('modifiers', [])
                if modifiers:
                    for modifier in modifiers:
                        print(f"  Modifier: {modifier.get('name')}")
                        receipt_text= receipt_text + f"  Modifier: {modifier.get('name')}"
                else:
                    print("  No modifiers applied")
                    receipt_text= receipt_text + f"  Modifier: {modifier.get('name')}"
            return print_receipt_cups(receipt_text)
                
        elif response.is_error():
            print(f"Error retrieving order: {response.errors}")
    except Exception as e:
        print(f"Exception when calling Square API: {str(e)}")

app = Flask(__name__)
run_with_ngrok(app=app, auth_token=config.NGROK_AUTH_TOKEN)
# Start ngrok when the app is run
#def start_ngrok():
    #from pyngrok import ngrok
    #url = ngrok.connect(5000)
    #print(" * Tunnel URL:", url)
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
@app.route('/webhook', methods=['POST','GET'])
def webhook():
    if request.method == 'POST':
        data = request.json
        print(f"Received webhook: {data}")
        order_id = data["data"]["object"]["payment"]["order_id"]
        payment = data['data']['object']['payment']
        employee_id = payment.get('employee_id', None)
        if employee_id in employees:
            subprocess.Popen(["python3", retrieve_order_path, order_id])
        return jsonify({"status": "success"}), 200
        #extract the order ID from JSON and return it
    elif request.method =='GET':
        print(f'suceeder')
        #return 'Success',200
        return jsonify({"status": "success"}), 200
    else:
        abort(400)
        
if __name__ == '__main__':
    #start_ngrok()
    app.run(port=8080)

    

#TMkOHwG2sxxltMhC is [Konstantin, Rosen, Ivanov]
showroom_employees = ['TMkOHwG2sxxltMhC', 'TMAjCxOpEODrZzdw', 'TMTg5jRjIGuWabZ4']
