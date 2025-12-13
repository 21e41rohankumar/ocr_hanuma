from flask import Flask, jsonify, request
import json
import os
import shutil
import re
import easyocr
from datetime import datetime
from PIL import Image
from io import BytesIO

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.environ.get("DATA_DIR", "/tmp/ocr_data")

UPLOAD_FOLDER = os.path.join(DATA_DIR, "upload")
PROCESSED_FOLDER = os.path.join(DATA_DIR, "processed_images")
JSON_FILE_PATH = os.path.join(DATA_DIR, "master_ocr.json")


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def clean_folder(folder):
    for f in os.listdir(folder):
        file_path = os.path.join(folder, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

def run_ocr(image_path):
    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(image_path)

    extracted_texts = [text for (_, text, prob) in result if prob >= 0.25]

    patterns = ("VNI", "VHI", "VH1", "VN1","VH","VN")
    ocr_value = next((text for text in extracted_texts if text.strip().upper().startswith(patterns)), None)

    if not ocr_value:
        numbers = []
        for text in extracted_texts:
            found = re.findall(r'\d+', text)
            if found:
                numbers.extend(found)
        ocr_value = numbers if numbers else None

    return ocr_value

@app.route("/")
def home():
    return jsonify({"message": "OCR API is running"})

@app.route("/upload", methods=["POST"])
def upload_data():
    if "image" not in request.files:
        return jsonify({"status": "failed", "message": "No image uploaded"}), 400
    
    image = request.files["image"]
    payload_raw = request.form.get("payload")

    img_bytes = image.read()
    pil_img = Image.open(BytesIO(img_bytes))
    width, height = pil_img.size

    if width < 720 and height < 720:
        return jsonify({
            "status": "failed",
            "message": "Image resolution too low. Minimum 720px required."
        }), 400

    image.stream.seek(0)

    try:
        payload = json.loads(payload_raw) if payload_raw else {}
    except json.JSONDecodeError:
        return jsonify({"status": "failed", "message": "Invalid JSON format"}), 400

    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)

    ocr_text = run_ocr(image_path)

    try:
        shutil.move(image_path, os.path.join(PROCESSED_FOLDER, image.filename))
        clean_folder(UPLOAD_FOLDER)
    except Exception as e:
        print("File error:", e)

    clean_folder(UPLOAD_FOLDER)

    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_filename": image.filename,
        "payload": payload,
        "ocr_result": ocr_text
    }

    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, "r") as file:
                data = json.load(file)
                if not isinstance(data, list):
                    data = [data]
        except Exception:
            data = []
    else:
        data = []

    data.append(new_entry)

    with open(JSON_FILE_PATH, "w") as file:
        json.dump(data, file, indent=4)

    return jsonify({
        "status": "success",
        "message": "Image processed and OCR extracted",
        "processed_data": new_entry
    })

@app.route("/records", methods=["GET"])
def retrieve_data():
    if not os.path.exists(JSON_FILE_PATH):
        return jsonify({"status": "error", "message": "No stored records"}), 404
    
    with open(JSON_FILE_PATH, "r") as file:
        data = json.load(file)

    return jsonify({"status": "success", "records": data})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
