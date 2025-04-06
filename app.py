from flask import Flask, request, jsonify, render_template, redirect, session, send_file
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import torch
from diffusers import StableDiffusionPipeline
from peft import PeftModel
import os
from bson import ObjectId

app = Flask(__name__)
CORS(app)
app.secret_key = "9537b06e59ad970d60375d235fa8a1675f13f1a03c1506e70fd8ce5ef13a11c2"  # Change this in production

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["dreammon"]
users_collection = db["users"]
images_collection = db["images"]

# Routes

@app.route('/')
def home():
    if 'username' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        if users_collection.find_one({"username": username}):
            return render_template("signup.html", error="Username already exists")

        hashed_pw = generate_password_hash(password)
        users_collection.insert_one({"username": username, "password": hashed_pw})

        return redirect('/')
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return redirect('/dashboard')
    return render_template('login.html', error="Invalid credentials")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/generate', methods=['POST'])
def generate():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    image_path = generate_image(prompt)
    return send_file(image_path, mimetype='image/png')

def generate_image(prompt: str):
    base_model_id = "runwayml/stable-diffusion-v1-5"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_id,
        torch_dtype=dtype,
        use_safetensors=True
    )

    unet_base = pipe.unet
    lora_model_id = "AryanMakadiya/pokemon_lora"
    unet = PeftModel.from_pretrained(unet_base, lora_model_id)
    pipe.unet = unet

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = pipe.to(device)

    print("Generating image...")

    if torch.cuda.is_available():
        with torch.autocast("cuda"):
            image = pipe(prompt, num_inference_steps=50, guidance_scale=7.5).images[0]
    else:
        image = pipe(prompt, num_inference_steps=50, guidance_scale=7.5).images[0]

    output_path = "generated_pokemon.png"
    image.save(output_path)
    print("Image saved as generated_pokemon.png")
    return output_path

@app.route('/save', methods=['POST'])
def save_image_info():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    prompt = data.get("prompt")
    image_path = "generated_pokemon.png"

    images_collection.insert_one({
        "username": session['username'],
        "prompt": prompt,
        "image_path": image_path,
        "created_at": datetime.utcnow()
    })
    return jsonify({"message": "Saved to history"})

@app.route('/history', methods=['GET'])
def get_history():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_images = images_collection.find({"username": session['username']}).sort("created_at", -1)
    history = [{
        "prompt": img["prompt"],
        "image_path": img["image_path"],
        "created_at": img["created_at"].strftime('%Y-%m-%d %H:%M')
    } for img in user_images]

    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
