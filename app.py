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

def admin_required():
    return "user" in session and session.get("role") == "admin"

# ---------------- HOME ----------------
@app.route("/")
def landing():
    return render_template("landing.html")


# ---------------- AUTH ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    # ✅ already logged in → redirect
    if "user" in session:
        return redirect(url_for("user_dashboard"))

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
    # ✅ already logged in → redirect
    if "user" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = mongo.db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            session["role"] = user["role"]

            # AFTER successful login
            mongo.db.logs.insert_one({
                "user": user["email"],
                "action": "User logged in"
            })

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))

        return "Invalid credentials"

    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    if "user" in session:
        mongo.db.logs.insert_one({
            "user": session["user"],
            "action": "User logged out"
        })

    session.clear()
    return redirect(url_for("landing"))
 



# ---------------- USER ROUTES ----------------
@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    documents = list(mongo.db.documents.find({"user": session["user"]}))
    return render_template("user/dashboard.html", documents=documents)



@app.route("/user/documents", methods=["GET", "POST"])
def user_documents():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["document"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # AI PIPELINE
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

            # ✅ AUDIT LOG (ADD THIS)
            mongo.db.logs.insert_one({
                "user": session["user"],
                "action": "Uploaded business document",
                "filename": filename
            })

            return redirect(url_for("user_documents"))

    documents = list(mongo.db.documents.find({"user": session["user"]}))
    return render_template("user/documents.html", documents=documents)


@app.route("/user/overview")
def user_overview():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/overview.html")

@app.route("/user/insights")
def user_insights():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/insights.html")

@app.route("/user/performance")
def user_performance():
    if "user" not in session:
        return redirect(url_for("login"))

    # Example computed scores (can be dynamic later)
    scores = {
        "readiness": 78,
        "maturity": 72,
        "digital": 65,
        "risk": 40
    }

    kpi_labels = [
        "Revenue Growth",
        "Cost Efficiency",
        "Market Expansion",
        "Automation"
    ]

    kpi_values = [70, 60, 55, 65]

    trend_labels = ["Q1", "Q2", "Q3", "Q4"]
    growth_trend = [55, 60, 68, 75]
    risk_trend = [50, 45, 42, 40]

    return render_template(
        "user/performance.html",
        scores=scores,
        kpi_labels=kpi_labels,
        kpi_values=kpi_values,
        trend_labels=trend_labels,
        growth_trend=growth_trend,
        risk_trend=risk_trend
    )

@app.route("/user/scenarios")
def user_scenarios():
    if "user" not in session:
        return redirect(url_for("login"))

    scenario = request.args.get("scenario", "growth")
    mongo.db.logs.insert_one({
        "user": session["user"],
        "action": "Simulated strategy scenario",
        "meta": scenario
    })


    # Scenario simulation logic
    scenarios = {
        "growth": {
            "focus": "Market Expansion",
            "readiness": 82,
            "risk": 55,
            "confidence": 84,
            "revenue": 80,
            "cost_efficiency": 50,
            "stability": 60,
            "explanation": (
                "Growth-focused strategy prioritizes market expansion and "
                "customer acquisition. While revenue potential is high, "
                "moderate risk exposure is expected due to increased investments."
            )
        },
        "cost": {
            "focus": "Operational Efficiency",
            "readiness": 75,
            "risk": 35,
            "confidence": 78,
            "revenue": 55,
            "cost_efficiency": 85,
            "stability": 80,
            "explanation": (
                "Cost optimization strategy improves operational efficiency "
                "and stability. Revenue growth is moderate, but risk exposure "
                "is significantly reduced."
            )
        },
        "risk": {
            "focus": "Risk Mitigation",
            "readiness": 70,
            "risk": 25,
            "confidence": 80,
            "revenue": 45,
            "cost_efficiency": 65,
            "stability": 90,
            "explanation": (
                "Risk-focused strategy emphasizes compliance and stability. "
                "This minimizes exposure but may limit aggressive growth opportunities."
            )
        }
    }

    result = scenarios.get(scenario, scenarios["growth"])

    return render_template(
        "user/scenarios.html",
        scenario=scenario,
        result=result
    )

@app.route("/user/compare", methods=["GET", "POST"])
def compare_strategies():
    if "user" not in session:
        return redirect(url_for("login"))

    documents = list(mongo.db.documents.find({"user": session["user"]}))
    comparison = None

    if request.method == "POST":
        doc1 = mongo.db.documents.find_one({"_id": ObjectId(request.form["doc1"])})
        doc2 = mongo.db.documents.find_one({"_id": ObjectId(request.form["doc2"])})

        def score_document(doc):
            score = 0

            score += len(doc.get("strategies", [])) * 10
            score += len(doc.get("kpis", [])) * 5
            score += len(doc.get("swot", {}).get("opportunities", [])) * 5
            score -= len(doc.get("swot", {}).get("threats", [])) * 5

            return max(40, min(score, 95))

        score1 = score_document(doc1)
        score2 = score_document(doc2)

        winner = doc1["filename"] if score1 > score2 else doc2["filename"]

        comparison = {
            "doc1": {
                "name": doc1["filename"],
                "focus": ", ".join(doc1.get("intents", [])),
                "score": score1,
                "risk": "Medium" if score1 < 75 else "Low"
            },
            "doc2": {
                "name": doc2["filename"],
                "focus": ", ".join(doc2.get("intents", [])),
                "score": score2,
                "risk": "Medium" if score2 < 75 else "Low"
            },
            "winner": winner,
            "explanation": (
                f"The strategy derived from '{winner}' demonstrates stronger "
                "strategic alignment, higher opportunity potential, and better "
                "risk balance based on AI evaluation."
            )
        }

        mongo.db.logs.insert_one({
            "user": session["user"],
            "action": "Compared two strategies",
            "meta": f"{doc1['filename']} vs {doc2['filename']}"
        })


    return render_template(
        "user/compare.html",
        documents=documents,
        comparison=comparison
    )


@app.route("/user/reports")
def user_reports():
    if "user" not in session:
        return redirect(url_for("login"))

    documents = list(mongo.db.documents.find({"user": session["user"]}))
    return render_template("user/reports.html", documents=documents)


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

@app.route("/admin/analytics")
def admin_analytics():
    if not admin_required():
        return redirect(url_for("login"))

    total_users = mongo.db.users.count_documents({})
    total_docs = mongo.db.documents.count_documents({})

    # -------- INTENT DISTRIBUTION --------
    intent_count = {}
    for doc in mongo.db.documents.find():
        for intent in doc.get("intents", []):
            intent_count[intent] = intent_count.get(intent, 0) + 1

    # -------- RISK DISTRIBUTION --------
    risk_count = {}
    for doc in mongo.db.documents.find():
        for threat in doc.get("swot", {}).get("threats", []):
            risk_count[threat] = risk_count.get(threat, 0) + 1

    return render_template(
        "admin/analytics.html",
        total_users=total_users,
        total_docs=total_docs,
        intent_labels=list(intent_count.keys()),
        intent_values=list(intent_count.values()),
        risk_labels=list(risk_count.keys()),
        risk_values=list(risk_count.values())
    )



@app.route("/admin/users")
def admin_users():
    if not admin_required():
        return redirect(url_for("login"))

    users = list(mongo.db.users.find())
    documents = list(mongo.db.documents.find())

    usage = {}
    for doc in documents:
        usage[doc["user"]] = usage.get(doc["user"], 0) + 1

    return render_template(
        "admin/users.html",
        users=users,
        usage=usage
    )


@app.route("/admin/strategies")
def admin_strategies():
    if not admin_required():
        return redirect(url_for("login"))

    strategy_count = {}
    for doc in mongo.db.documents.find():
        for strategy in doc.get("strategies", []):
            strategy_count[strategy] = strategy_count.get(strategy, 0) + 1

    return render_template(
        "admin/strategies.html",
        strategy_count=strategy_count
    )

@app.route("/admin/risks")
def admin_risks():
    if not admin_required():
        return redirect(url_for("login"))

    risk_count = {}
    for doc in mongo.db.documents.find():
        for threat in doc.get("swot", {}).get("threats", []):
            risk_count[threat] = risk_count.get(threat, 0) + 1

    return render_template(
        "admin/risks.html",
        risk_count=risk_count
    )


@app.route("/admin/logs")
def admin_logs():
    if not admin_required():
        return redirect(url_for("login"))

    logs = list(mongo.db.logs.find().sort("_id", -1))
    return render_template("admin/logs.html", logs=logs)





# ---------------- DOWNLOAD REPORT ----------------
@app.route("/download/<doc_id>")
def download_pdf(doc_id):
    if "user" not in session:
        return redirect(url_for("login"))

    doc = mongo.db.documents.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        return "Document not found"

    # ✅ AUDIT LOG
    mongo.db.logs.insert_one({
        "user": session["user"],
        "action": "Downloaded strategy report",
        "meta": doc["filename"]
    })

    pdf_path = f"uploads/{doc_id}.pdf"
    generate_strategy_pdf(doc, pdf_path)

    return send_file(pdf_path, as_attachment=True)



# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
