from flask import Flask, render_template, request
import joblib
import mysql.connector
import numpy as np

app = Flask(__name__)

# =====================================
# Load Model and Scaler
# =====================================
model = joblib.load("model/random_forest.pkl")
scaler = joblib.load("model/scaler.pkl")

# =====================================
# MySQL Connection
# =====================================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",      # Change if your password is different
    database="IndustrialCarbonForecasting"
)

cursor = db.cursor(dictionary=True)

# =====================================
# Home Page
# =====================================
@app.route("/")
def home():
    return render_template("index.html")

# =====================================
# Predict Page
# =====================================
@app.route("/predict")
def predict_page():
    return render_template("predict.html")

# =====================================
# Predict Result
# =====================================
@app.route("/predict_result", methods=["POST"])
def predict_result():

    energy = float(request.form["energy"])
    temperature = float(request.form["temperature"])
    humidity = float(request.form["humidity"])
    production = float(request.form["production"])
    hour = int(request.form["hour"])
    weekend = int(request.form["weekend"])

    features = np.array([[
        energy,
        temperature,
        humidity,
        production,
        hour,
        weekend
    ]])

    features = scaler.transform(features)

    prediction = model.predict(features)[0]

    sql = """
    INSERT INTO prediction_history
    (
        energy_consumption,
        temperature,
        humidity,
        production_output,
        working_hour,
        weekend,
        predicted_co2
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        energy,
        temperature,
        humidity,
        production,
        hour,
        weekend,
        float(prediction)
    )

    cursor.execute(sql, values)
    db.commit()

    return render_template(
        "predict.html",
        prediction=round(prediction, 2)
    )

# =====================================
# History Page
# =====================================
@app.route("/history")
def history():

    cursor.execute("""
        SELECT *
        FROM prediction_history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    return render_template(
        "history.html",
        rows=rows
    )



# =====================================
# About Page
# =====================================
@app.route("/about")
def about():
    return render_template("about.html")




#=====================================
# Dashboard Page
#=====================================
@app.route("/dashboard")
def dashboard():

    cursor.execute(
        "SELECT COUNT(*) AS total FROM prediction_history"
    )

    total = cursor.fetchone()["total"]

    return render_template(
        "dashboard.html",
        total=total
    )




# =====================================
# Run Flask
# =====================================
if __name__ == "__main__":
    app.run(debug=True)