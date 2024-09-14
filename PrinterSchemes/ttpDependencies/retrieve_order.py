# retrieve_order.py
import requests
from square.client import Client
from square.http.auth.o_auth_2 import BearerAuthCredentials
import cups
import sys
import time
import config

# Square API credentials
bearer_auth_credential = BearerAuthCredentials(
    access_token=config.SQ_ACCESS_TOKEN)

client = Client(
    bearer_auth_credentials=bearer_auth_credential,
    environment=config.ENVIRONMENT
)

def generate_receipt_text(receipt_text):
    receipt_output = []
    receipt_output.append("Order Ticket".center(40, "-"))
    receipt_output.append("-" * 40)
    receipt_output.append(receipt_text)
    receipt_output.append("-" * 40)
    return "\n".join(receipt_output)

def print_receipt_cups(receipt_text):
    receipt_output = generate_receipt_text(receipt_text)
    with open('/tmp/receipt.txt', 'w') as receipt_file:
        receipt_file.write(receipt_output)
    conn = cups.Connection()
    printers = conn.getPrinters()
    tickPrinter = config.tickPrinter
    conn.printFile(tickPrinter, '/tmp/receipt.txt', "Receipt", {})

def retrieve_order(order_id):
    try:
        response = client.orders.retrieve_order(order_id=order_id)
        if response.is_success():
            receipt_text = ""
            order = response.body['order']
            order_notes = order.get('note', 'No general notes found')
            receipt_text = receipt_text + f"Order Notes: {order_notes}\n"
            line_items = order.get('line_items', [])
            receipt_text = receipt_text + "Line Items:\n"
            for item in line_items:
                receipt_text = receipt_text + f" - Name: {item['name']}\n"
                receipt_text = receipt_text + f"   Quantity: {item['quantity']}\n"
                receipt_text = receipt_text + f"   Total Money: {item['total_money']['amount']} {item['total_money']['currency']}\n"
                item_note = item.get('note', 'No note for this item')
                receipt_text = receipt_text + f"  Item Note: {item_note}\n"
                modifiers = item.get('modifiers', [])
                if modifiers:
                    for modifier in modifiers:
                        receipt_text = receipt_text + f"  Modifier: {modifier.get('name')}\n"
                else:
                    receipt_text = receipt_text + "  No modifiers applied\n"
            print_receipt_cups(receipt_text)
        elif response.is_error():
            print(f"Error retrieving order: {response.errors}")
    except Exception as e:
        print(f"Exception when calling Square API: {str(e)}")

def main():
    if len(sys.argv) > 1:
        order_id = sys.argv[1]
        retrieve_order_with_backoff(order_id)
    else:
        print("Order ID not provided")
        
def retrieve_order_with_backoff(order_id, retries=5):
    delay = 1  # start with 1 second delay
    for attempt in range(retries):
        try:
            response = client.orders.retrieve_order(order_id=order_id)
            if response.is_success():
                receipt_text = ""
                order = response.body['order']
                order_notes = order.get('note', 'No general notes found')
                receipt_text = receipt_text + f"Order Notes: {order_notes}\n"
                line_items = order.get('line_items', [])
                receipt_text = receipt_text + "Line Items:\n"
                for item in line_items:
                    receipt_text = receipt_text + f" - Name: {item['name']}\n"
                    receipt_text = receipt_text + f"   Quantity: {item['quantity']}\n"
                    receipt_text = receipt_text + f"   Total Money: {item['total_money']['amount']} {item['total_money']['currency']}\n"
                    item_note = item.get('note', 'No note for this item')
                    receipt_text = receipt_text + f"  Item Note: {item_note}\n"
                    modifiers = item.get('modifiers', [])
                    if modifiers:
                        for modifier in modifiers:
                            receipt_text = receipt_text + f"  Modifier: {modifier.get('name')}\n"
                    else:
                        receipt_text = receipt_text + "  No modifiers applied\n"
                print_receipt_cups(receipt_text)
                return print('Successful print')
            else:
                print(f"Attempt {attempt + 1} failed: {response.errors}")
        except Exception as e:
            print(f"Exception during attempt {attempt + 1}: {str(e)}")
        time.sleep(delay)
        delay *= 2  # exponential backoff
    print(f"Failed to retrieve order after {retries} attempts.")
    return None

if __name__ == "__main__":
    main()
