import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import pytesseract
# import pyheif  # Uncomment if handling HEIC images

# Set Tesseract path if needed
pytesseract.pytesseract.tesseract_cmd = 'C:/Users/asif.ayub/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_text_from_image(image_path):
    # Load HEIC files if needed
    # Uncomment the code below if HEIC handling is required
    # if image_path.lower().endswith('.heic'):
    #     heif_file = pyheif.read(image_path)
    #     image = Image.frombytes(
    #         heif_file.mode, 
    #         heif_file.size, 
    #         heif_file.data,
    #         "raw",
    #         heif_file.mode,
    #         heif_file.stride,
    #     )
    # else:
    image = Image.open(image_path)

    # Extract text with pytesseract
    text = pytesseract.image_to_string(image)
    return text

def parse_receipt_text(text):
    items = []
    prices = []
    lines = text.split('\n')
    
    # Enhanced regex patterns for items, descriptions, and prices
    item_price_pattern = re.compile(r'(.+?)\s+(\d+\.\d{2})$')  # Match items with price at end of line
    price_only_pattern = re.compile(r'(\d+\.\d{2})$')  # Match lines that contain only price
    description_start_pattern = re.compile(r'(description|item|product)', re.IGNORECASE)  # Common headers

    date_pattern = re.compile(r'(\d{2}[/-]\d{2}[/-]\d{4})')
    total_pattern = re.compile(r'(Total|Amount Due|Grand Total)\s*:\s*(\d+\.\d{2})', re.IGNORECASE)
    
    date, total = None, None
    parsing_items = False  # Flag to start capturing items after detecting the "Description" header

    for line in lines:
        # Capture the date
        if not date:
            date_match = date_pattern.search(line)
            if date_match:
                date = date_match.group(1)

        # Capture total amount
        total_match = total_pattern.search(line)
        if total_match:
            total = float(total_match.group(2))

        # Start parsing items if "Description" or similar header is found
        if description_start_pattern.search(line):
            parsing_items = True
            continue  # Skip to the next line

        # Parse items and prices if we are in the items section
        if parsing_items:
            item_price_match = item_price_pattern.search(line)
            if item_price_match:
                item, price = item_price_match.groups()
                items.append(item.strip())
                prices.append(float(price))
            else:
                # Check if line might be an item name without price
                if not price_only_pattern.match(line) and line.strip():
                    # Treat it as an item name if it’s non-empty and has no price
                    items.append(line.strip())
                elif price_only_pattern.match(line):
                    # If line contains only a price, attach it to the last item
                    prices.append(float(line.strip()))
    
    # Compute total if not found
    if total is None and prices:
        total = sum(prices)

    return {
        'Date': date,
        'Items': items,
        'Prices': prices,
        'Total': total
    }

@app.route('/upload', methods=['POST'])
def upload_receipt():
    files = request.files.getlist('receipts')
    receipts_data = []

    for file in files:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)

        # Extract and parse text
        text = extract_text_from_image(filename)
        parsed_data = parse_receipt_text(text)
        receipts_data.append(parsed_data)
    
    # Save data to JSON
    with open('receipts_data.json', 'w') as json_file:
        json.dump(receipts_data, json_file, indent=4)

    return jsonify({"message": "Receipts processed", "data": receipts_data})

if __name__ == '__main__':
    app.run(debug=True)

