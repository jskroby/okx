from flask import Flask, request, jsonify
import requests
import base64
import hmac
import hashlib
import json
from datetime import datetime, timezone

# Flask app setup
app = Flask(__name__)

# OKX API key details (Ensure these are correct)
api_key = "8a4d15f9-b3de-4098-8a84-b3698ce0475d"  # Replace with your actual API key
secret_key = "3A7025A8213464431FB4BA2A178F8719"   # Replace with your actual Secret key
passphrase = "Lola369!"                           # Replace with your actual Passphrase

# Function to generate the OK-ACCESS-SIGN header
def generate_signature(timestamp, method, request_path, body, secret_key):
    message = timestamp + method + request_path + body
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    return base64.b64encode(mac.digest()).decode()

# Function to place a market order on OKX
def place_order(instId, tdMode, side, ordType, sz, posSide):
    method = 'POST'
    request_path = '/api/v5/trade/order'
    body_dict = {
        "instId": instId,  # Instrument ID for the perpetual swap (e.g., 'DOGE-USDT-SWAP')
        "tdMode": tdMode,  # Margin mode ('isolated' or 'cross')
        "side": side,      # Order side ('buy' or 'sell')
        "ordType": ordType,  # Order type ('market' for market order)
        "sz": sz,          # Order size
        "posSide": posSide # Position side ('long' or 'short')
    }
    
    # Convert body to JSON string without spaces
    body = json.dumps(body_dict, separators=(',', ':'))
    
    # Generate the timestamp in the correct format
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    
    # Generate the signature for the request
    sign = generate_signature(timestamp, method, request_path, body, secret_key)
    
    # Set headers for the request
    headers = {
        'Content-Type': 'application/json',
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase
    }
    
    # Make the POST request to place an order
    response = requests.post(f'https://www.okx.com{request_path}', headers=headers, data=body)
    
    # Print the response for debugging
    print("Order Response:", response.json())
    return response.json()

# Webhook route to receive alerts
@app.route('/webhook', methods=['POST'])
def webhook():
    # Extract the data from the request
    data = request.json
    print(f"Received webhook data: {data}")

    # Check for the required fields in the webhook data
    if "signal" in data:
        signal = data["signal"]
        # Set parameters based on the signal
        instId = "DOGE-USDT-SWAP"  # Example instrument, modify as needed
        tdMode = "cross"           # Using cross margin mode as an example
        ordType = "market"         # Market order
        sz = "0.1"                 # Example size; adjust as needed
        
        # Determine the side and posSide based on the signal
        if signal == "long":
            side = "buy"
            posSide = "short"  # Closing a short position
        elif signal == "short":
            side = "sell"
            posSide = "long"  # Closing a long position
        else:
            return jsonify({"error": "Invalid signal"}), 400
        
        # Place the order
        order_response = place_order(instId, tdMode, side, ordType, sz, posSide)
        return jsonify(order_response)
    else:
        return jsonify({"error": "Invalid data format"}), 400

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
