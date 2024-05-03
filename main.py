from flask import Flask, render_template, jsonify, request, redirect, url_for
import openai
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy.sql import text

app = Flask(__name__)

# Initialize Cloud SQL Python Connector
connector = Connector()

# Function to create database connections
def getconn() -> sqlalchemy.engine.base.Connection:
    conn = connector.connect(
        "instancename", 
        "pymysql",
        user="root",
        password="pass",
        db="foodies",
        ip_type=IPTypes.PUBLIC 
    )
    return conn

# Create SQLAlchemy engine and scoped session
engine = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
    pool_pre_ping=True,
    pool_recycle=1800,  # Adjust pool recycle time as needed
    pool_size=5
)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Load API key from environment variable or configuration file
openai.api_key = "apikey"

@app.teardown_appcontext
def remove_session(ex=None):
    db_session.remove()

@app.route("/")
@app.route("/home")
def home():
    return render_template("landing.html")

@app.route("/help")
def help():
    return render_template("FoodiesHelp.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        # Use text() to wrap your SQL query
        sql_query = text('SELECT password FROM users WHERE username = :username')
        
        # Execute the query with parameters
        cursor = db_session.execute(sql_query, {'username': username})
        user_password_tuple = cursor.fetchone()
        cursor.close()

        if user_password_tuple:
            user_password = user_password_tuple[0]
            if user_password == password:
                return redirect(url_for('dashboard', name=username))
            else:
                return "Password does not match"
        else:
            return "No user found with the username"

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    name = request.args.get("name", "")
    return render_template('dashboard.html', name=name)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        # Updated SQL execution call
        sql = text('INSERT INTO users (username, password, email) VALUES (:username, :password, :email)')
        db_session.execute(sql, {'username': username, 'password': password, 'email': email})
        db_session.commit()

        return redirect(url_for('dashboard', name=username))
    else:
        return render_template("signup.html")


@app.route("/result", methods=['POST', 'GET'])
def results():
    if request.method == 'POST':
        output = request.form.to_dict()
        name = output.get("name", "")
        return render_template("index.html", name=name)
    return render_template("index.html")

@app.route("/generate_recipe", methods=['POST'])
def generate_recipe():
    prompt = request.form.get("prompt")
    cuisine = request.form.get("cuisine")
    meal = request.form.get("meal")

    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    if cuisine not in {"Chinese", "Italian", "Mexican", "Thai", "French", "Japanese", "Indian", "American", "Mediterranean", "Vietnamese", "Ethiopian"}:
        return jsonify({"error": "Invalid cuisine."}), 400

    if meal not in {"Breakfast", "Lunch", "Dinner", "Snack", "Dessert"}:
        return jsonify({"error": "Invalid meal."}), 400

    try:
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=f"What can I make for {meal} in {cuisine} style with these ingredients: {prompt}? Please provide a recipe with a title, ingredients, and instructions.",
            temperature=0.7,
            max_tokens=500
        )

        recipes = [result["text"].strip() for result in response["choices"]]
        formatted_recipes = []
        for recipe in recipes:
            title_start = recipe.find("Title:")
            ingredients_start = recipe.find("Ingredients:")
            instructions_start = recipe.find("Instructions:")

            title = recipe[title_start:ingredients_start].strip() if title_start != -1 else f"{cuisine} {meal} Recipe"
            ingredients = recipe[ingredients_start:instructions_start].strip() if ingredients_start != -1 else ""
            instructions = recipe[instructions_start:].strip() if instructions_start != -1 else ""

            title = title.replace("Title:", "").strip()
            ingredients = ingredients.replace("- ", "• ").replace("Ingredients:", "").strip()
            instructions = instructions.replace("1. ", "• ").replace("Instructions:", "").strip()

            formatted_recipe = f"**{title}**\n\n**Ingredients**\n{ingredients}\n\n**Instructions**\n{instructions}"
            formatted_recipes.append(formatted_recipe)

        return jsonify({"recipes": formatted_recipes})

    except Exception as e:
        print(f"Exception occurred: {e}")
        return jsonify({"error": "An error occurred while generating the recipe."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080)
