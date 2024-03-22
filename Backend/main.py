import requests
from flask import Flask, render_template, jsonify, request, redirect, url_for
import openai

app = Flask(__name__)

# Load API key from environment variable or configuration file
openai.api_key = "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"

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/login", methods=['POST'])
def login():
    username = request.form.get("name", "")
    # Perform login validation here if needed
    return redirect(url_for('dashboard', name=username))

@app.route("/dashboard")
def dashboard():
    name = request.args.get("name", "")
    return render_template("dashboard.html", name=name)

@app.route("/result", methods=['POST', 'GET'])
def results():
    if request.method == 'POST':
        output = request.form.to_dict()
        name = output.get("name", "")
        return render_template("index.html", name=name)
    return render_template("index.html")

@app.route("/generate_image", methods=['POST'])
def generate_image():
    global response
    prompt = request.form.get("prompt")
    cuisine = request.form.get("cuisine")
    meal = request.form.get("meal")
    size = request.form.get("size")

    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    if cuisine not in {"Chinese", "Italian", "Mexican","Thai", "French", "Japanese", "Indian", "American", "Mediterranean", "Vietnamese", "Ethiopian"}:
        return jsonify({"error": "Invalid cuisine."}), 400
    
    if meal not in {"Breakfast", "Lunch", "Dinner", "Snack","Dessert"}:
                return jsonify({"error": "Invalid cuisine."}), 400

    try:
        if size == "1024x1024" or size == "1024x1792" or size == "1792x1024":
            passthroughPrompt = "For " + meal+ " " + cuisine + " style dish made with "+ prompt  
            response = openai.Image.create(
                model="dall-e-3",
                prompt=passthroughPrompt,
                size=size,
                n=1,
            )
        elif size == "512x512" or size == "256x256":
            passthroughPrompt = "For " + meal+ " " + cuisine + " style dish made with "+ prompt  
            response = openai.Image.create(
                model="dall-e-2",
                prompt=passthroughPrompt,
                size=size,
                n=1,
            )
        image_url = response.get('data', [])[0].get('url')
        return jsonify({"image_url": image_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
