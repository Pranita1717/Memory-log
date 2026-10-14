from db import *

import datetime
import os
import threading
import time

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash

import schedule

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "local-development-only-change-me")

# ==============================
# REMINDER SYSTEM
# ==============================

def send_reminder():
    print("🔔 Reminder triggered!")

schedule.every().day.at("09:00").do(send_reminder)

def run_scheduler():

    while True:

        schedule.run_pending()

        time.sleep(1)

threading.Thread(
    target=run_scheduler,
    daemon=True
).start()

# ==============================
# HOME
# ==============================

@app.route("/")
def home():

    return render_template(
        "landing.html",
        logged_in=("user" in session)
    )

# ==============================
# LOGIN
# ==============================

@app.route("/login_form")
def login_form():

    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    user = users_collection.find_one({
        "username": username
    })

    if user and user["password"] == password:

        session["user"] = username
        session["role"] = user["role"]

        if user["role"] == "caregiver":
            return redirect("/caregiver")

        if user["role"] == "admin":
            return redirect("/admin")

        return redirect("/dashboard")

    return render_template(
        "index.html",
        error="Invalid credentials"
    )

# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    existing = users_collection.find_one({
        "username": username
    })

    if existing:

        return render_template(
            "register.html",
            error="User already exists"
        )

    user_data = {

        "username": username,
        "password": password,
        "role": role,

        "assessment_score": 0,
        "assessment_result": "Not Taken",

        "latitude": None,
        "longitude": None
    }

    # CAREGIVER LINKING

    if role == "caregiver":

        linked_patients = request.form.get(
            "linked_patient"
        )

        if linked_patients:

            patient_list = [

                p.strip()

                for p in linked_patients.split(",")

            ]

            user_data["linked_patients"] = patient_list

        else:

            user_data["linked_patients"] = []

    users_collection.insert_one(user_data)

    return redirect("/login_form")

# ==============================
# PATIENT DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    user = session["user"]

    # GAME HISTORY

    history = list(

        history_collection.find({

            "username": user

        })

    )

    history.reverse()

    # LAST TEST DAYS

    last_test_days = None

    if history:

        try:

            last_date = datetime.datetime.strptime(

                history[0]["date"],
                "%Y-%m-%d %H:%M:%S"

            )

            last_test_days = (

                datetime.datetime.now() - last_date

            ).days

        except:
            pass

    # ALERT STATUS

    alert_status = None

    scores = [

        h.get("score", 0)

        for h in history

    ]

    if len(scores) >= 4:

        recent_avg = sum(scores[:2]) / 2

        old_avg = sum(scores[2:4]) / 2

        drop = old_avg - recent_avg

        if drop > 20:
            alert_status = "danger"

        elif drop > 10:
            alert_status = "warning"

        else:
            alert_status = "good"

    # USER DATA

    user_data = users_collection.find_one({
        "username": user
    })

    return render_template(

        "dashboard.html",

        user=user,

        history=history,

        last_test_days=last_test_days,

        alert_status=alert_status,

        assessment_score=user_data.get(
            "assessment_score", 0
        ),

        assessment_result=user_data.get(
            "assessment_result",
            "Not Taken"
        ),

        latitude=user_data.get(
            "latitude"
        ),

        longitude=user_data.get(
            "longitude"
        )
    )

# ==============================
# GAMES
# ==============================

@app.route("/test/matching")
def test_matching():

    return render_template("test.html")


@app.route("/test/words")
def test_words():

    return render_template("test_words.html")


@app.route("/test/pattern")
def test_pattern():

    return render_template("test_pattern.html")

# ==============================
# SAVE GAME SCORE
# ==============================

@app.route("/submit_score", methods=["POST"])
def submit_score():

    if "user" not in session:

        return jsonify({
            "status": "error"
        })

    data = request.get_json()

    game_name = data.get("game")
    score = data.get("score")

    history_collection.insert_one({

        "username": session["user"],

        "game_name": game_name,

        "score": score,

        "date": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    })

    return jsonify({
        "status": "success"
    })

# ==============================
# COGNITIVE ASSESSMENT
# ==============================

@app.route("/assessment", methods=["POST"])
def assessment():

    if "user" not in session:
        return redirect("/")

    total_score = 0

    for i in range(1, 11):

        total_score += int(

            request.form.get(f"q{i}", 0)

        )

    # RESULT MESSAGE

    result = "Normal Cognitive Health"

    if total_score < 5:
        result = "Needs Attention"

    users_collection.update_one(

        {

            "username": session["user"]

        },

        {

            "$set": {

                "assessment_score": total_score,

                "assessment_result": result

            }

        }

    )

    flash("Assessment Saved Successfully")

    return redirect("/dashboard")

# ==============================
# CAREGIVER DASHBOARD
# ==============================

@app.route("/caregiver")
def caregiver():

    if "user" not in session:
        return redirect(url_for("login"))

    caregiver = users_collection.find_one({
        "username": session["user"]
    })

    linked_patients = caregiver.get(
        "linked_patients",
        []
    )

    patients = []

    for username in linked_patients:

        patient = users_collection.find_one({
            "username": username
        })

        if patient:

            history = list(

                history_collection.find({
                    "username": username
                })

            )

            history.reverse()

            patient["game_history"] = history

            patients.append(patient)

    return render_template(

        "caregiver.html",

        caregiver=caregiver,

        patients=patients
    )

# ==============================
# SAVE LIVE LOCATION
# ==============================

@app.route("/save_location", methods=["POST"])
def save_location():

    if "user" not in session:

        return jsonify({
            "status": "error"
        })

    try:

        data = request.get_json()

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        users_collection.update_one(

            {
                "username": session["user"]
            },

            {
                "$set": {

                    "latitude": latitude,
                    "longitude": longitude
                }
            }
        )

        return jsonify({
            "status": "success"
        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)
        })

# ==============================
# GET LOCATION
# ==============================

@app.route("/get_location")
def get_location():

    if "user" not in session:

        return jsonify({
            "status": "error"
        })

    caregiver = users_collection.find_one({
        "username": session["user"]
    })

    linked_patients = caregiver.get(
        "linked_patients",
        []
    )

    if not linked_patients:

        return jsonify({
            "status": "error"
        })

    patient = users_collection.find_one({
        "username": linked_patients[0]
    })

    if patient:

        return jsonify({

            "status": "success",

            "latitude": patient.get("latitude"),

            "longitude": patient.get("longitude")
        })

    return jsonify({
        "status": "error"
    })

# ==============================
# ADMIN
# ==============================

@app.route("/admin")
def admin_portal():

    if "user" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return redirect("/dashboard")

    users = {}

    records = users_collection.find()

    for user in records:

        users[user["username"]] = {

            "username": user.get("username"),

            "role": user.get("role"),

            "linked_patients":
            user.get("linked_patients", [])

        }

    return render_template(
        "admin.html",
        users=users
    )

# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ==============================
# RUN
# ==============================

if __name__ == "__main__":

    app.run(debug=True)