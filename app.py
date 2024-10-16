import requests
import datetime
from flask import Flask, jsonify, send_from_directory, request, url_for
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import base64
import cv2
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from roboflow import Roboflow
import cv2
from waitress import serve

matplotlib.use('Agg')
app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET'])
def get_home():
    toReturn = jsonify({"text": "Welcome to the Triage backend server! API requests may be requested from this URL."})
    toReturn.headers.add('Access-Control-Allow-Origin', '*')
    return toReturn


@app.route('/imagerisks/<string:address>', methods=['GET'])
def image_risks(address):    
    API_URL = "https://3gf752e95a.execute-api.us-east-2.amazonaws.com/prod/image-similarity/"

    try:
        googleKey = 'AIzaSyCgWSfHxmUm-75lPOdgFfHeBfUBmhkEqRI'
        url = f'https://maps.googleapis.com/maps/api/staticmap?center={address}&zoom=15&size=400x400&maptype=satellite&key={googleKey}'
        response = requests.get(url)

        img_array = np.frombuffer(response.content, np.uint8)

        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        _, buffer = cv2.imencode('.png', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        IMAGE_DIR = './images'  # Change this to your actual directory


        API_URL = "https://3gf752e95a.execute-api.us-east-2.amazonaws.com/prod/image-similarity/"

        # Store scores for each image pair
        scores = {}
        max = ''
        maxScore = 0
        for filename in os.listdir('./images'):
          
              file_path = os.path.join('./images', filename)
              line = file_path.split('.')[2]
              img2_data = ''
              
              with open(file_path, "rb") as img_file:
                  img2_data = base64.b64encode(img_file.read()).decode('utf-8')

              # Prepare the request body
              request_body = {
                  "img_1": img_base64,
                  "img_2": img2_data
              }


              response = requests.post(API_URL, json=request_body)
              if maxScore < response.json()['similarity']:
                  maxScore = response.json()['similarity']
                  max = line

        return jsonify({"damage": str(max)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/imagerisk/<string:address>', methods=['GET'])
def image_risk(address):
    damage = [2, 6, 8, 1, 14, 17, 3]
    return jsonify({"damage": str(damage[np.random.randint(0, len(damage))]) + "%"})

@app.route('/run-program', methods=['POST'])
def run_program():
    if 'imageBefore' not in request.files or 'imageAfter' not in request.files:
        return jsonify({'error': 'Both before and after images are required'}), 400

    image_before = request.files['imageBefore']
    image_after = request.files['imageAfter']

    if image_before.filename == '' or image_after.filename == '':
        return jsonify({'error': 'Both before and after images must be selected'}), 400

    if image_before and image_after and allowed_file(image_before.filename) and allowed_file(image_after.filename):
        image_path_before = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image_before.filename))
        image_path_after = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image_after.filename))

        # Save images as RGB
        Image.open(image_before).convert('RGB').save(image_path_before, 'JPEG')
        Image.open(image_after).convert('RGB').save(image_path_after, 'JPEG')

        rf = Roboflow(api_key="zpb5BDJeUPjMGNd2CVoO")
        project = rf.workspace().project("junk-jzngr")
        model = project.version(16).model

        # Process before image
        result_before = model.predict(image_path_before, confidence=12).json()
        before_count = sum(1 for result in result_before['predictions'] if result['class'] == "no-damage")
        output_path_before = process_image(image_path_before, result_before)

        # Process after image
        result_after = model.predict(image_path_after, confidence=12).json()
        after_count = sum(1 for result in result_after['predictions'] if result['class'] == "no-damage")
        output_path_after = process_image(image_path_after, result_after)

        damage_percentage = (after_count / before_count * 100) if before_count > 0 else 0

        response = {
            "outputImageBefore": url_for('serve_image', filename=output_path_before, _external=True),
            "outputImageAfter": url_for('serve_image', filename=output_path_after, _external=True),
            "damagePercentage": damage_percentage
        }

        return jsonify(response)

    return jsonify({'error': 'Invalid file type'}), 400

def process_image(image_path, result):
    image = Image.open(image_path).convert('RGB')  # Convert to RGB
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image)

    for pred in result['predictions']:
        x_center, y_center = pred['x'], pred['y']
        width, height = pred['width'], pred['height']
        x_min, y_min = x_center - (width / 2), y_center - (height / 2)

        color = {
            "minor-damage": "green",
            "major-damage": "yellow",
            "destroyed": "red",
            "no-damage": "blue"
        }.get(pred['class'], "white")

        rect = patches.Rectangle((x_min, y_min), width, height, linewidth=3, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        ax.text(x_min, y_min - 10, pred['class'], fontsize=8, color="black")

    ax.axis('off')
    output_path = f"output_{os.path.basename(image_path)}"
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, format='jpeg')
    plt.close(fig)
    return output_path

@app.route('/images/<path:filename>')
def serve_image(filename):
    try:
        response = send_from_directory('', filename)
        return response
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filename': filename}), 200
    return jsonify({'error': 'File type not allowed'}), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def create_app():
   return app
