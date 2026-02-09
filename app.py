import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file
)
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId

from config import Config

# AI ENGINE IMPORTS
from ai_engine.text_extractor import extract_text
from ai_engine.nlp_processor import (
    clean_text, extract_keywords,
    generate_summary, detect_business_intent
)
from ai_engine.strategy_generator import (
    generate_swot,
    generate_initial_strategy,
    generate_kpis,
    generate_action_plan,
    prioritize_strategies
)
from ai_engine.pdf_generator import generate_strategy_pdf


# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.config.from_object(Config)

mongo = PyMongo(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- HOME ----------------
@app.route("/")
def landing():
    return render_template("landing.html")


# ---------------- AUTH ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        if mongo.db.users.find_one({"email": email}):
            return "User already exists"

        mongo.db.users.insert_one({
            "name": name,
            "email": email,
            "password": password,
            "role": role
        })

        return redirect(url_for("login"))

    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = mongo.db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            session["role"] = user["role"]
            return redirect(url_for("user_dashboard"))

        return "Invalid credentials"

    return render_template("auth/login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- USER ROUTES ----------------
@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    docs = list(mongo.db.documents.find({"user": session["user"]}))
    return render_template("user/dashboard.html", documents=docs)


@app.route("/user/upload", methods=["GET", "POST"])
def upload_document():
    if "user" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["document"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # -------- AI PIPELINE --------
            raw_text = extract_text(filepath)
            cleaned_text = clean_text(raw_text)

            summary = generate_summary(raw_text)
            keywords = extract_keywords(cleaned_text)
            intents = detect_business_intent(raw_text)

            swot = generate_swot(raw_text)
            strategies = generate_initial_strategy(intents, swot)
            kpis = generate_kpis(intents)
            action_plan = generate_action_plan(strategies)
            prioritized = prioritize_strategies(strategies, swot)

            mongo.db.documents.insert_one({
                "user": session["user"],
                "filename": filename,
                "summary": summary,
                "keywords": keywords,
                "intents": intents,
                "swot": swot,
                "strategies": strategies,
                "kpis": kpis,
                "action_plan": action_plan,
                "prioritized_strategies": prioritized
            })

            return redirect(url_for("user_dashboard"))

    return render_template("user/upload.html")


@app.route("/user/analysis")
def user_analysis():
    return render_template("user/analysis.html")


@app.route("/user/decisions")
def user_decisions():
    return render_template("user/decisions.html")


@app.route("/user/reports")
def user_reports():
    return render_template("user/reports.html")


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/profile.html")


# ---------------- ADMIN ROUTES ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    users = list(mongo.db.users.find())
    documents = list(mongo.db.documents.find())

    intent_stats = {}
    for doc in documents:
        for intent in doc.get("intents", []):
            intent_stats[intent] = intent_stats.get(intent, 0) + 1

    return render_template(
        "admin/dashboard.html",
        users=users,
        documents=documents,
        total_users=len(users),
        total_documents=len(documents),
        intent_stats=intent_stats
    )


# ---------------- DOWNLOAD REPORT ----------------
@app.route("/download/<doc_id>")
def download_report(doc_id):
    if "user" not in session:
        return redirect(url_for("login"))

    doc = mongo.db.documents.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        return "Document not found"

    pdf_path = os.path.join(app.config["REPORT_FOLDER"], f"{doc_id}.pdf")
    generate_strategy_pdf(doc, pdf_path)

    return send_file(pdf_path, as_attachment=True)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
