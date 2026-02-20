import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file, flash, jsonify
)
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId
from bson.objectid import ObjectId

from config import Config
from datetime import datetime

# AI ENGINE IMPORTS
from ai_engine.text_extractor import extract_text
from ai_engine.nlp_processor import (
    clean_text, extract_keywords,
    generate_summary
)
from ai_engine.strategy_generator import (
    generate_full_strategy_profile, # <--- Our new Gemini function!
    generate_initial_strategy, generate_kpis, 
    generate_action_plan, prioritize_strategies,
    calculate_strategic_scores, simulate_scenario
)
from ai_engine.pdf_generator import generate_strategy_pdf
from ai_engine.chat_processor import get_document_answer  # <--- ADD THIS
import ai_engine.nlp_processor as nlp


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

# --- ADD THESE HELPER FUNCTIONS ---
def get_active_document():
    """Fetches the currently selected document, or falls back to the latest one."""
    if "active_doc_id" in session:
        doc = mongo.db.documents.find_one({
            "_id": ObjectId(session["active_doc_id"]), 
            "user": session["user"]
        })
        if doc: 
            return doc
            
    # Fallback to latest if nothing is selected
    doc = mongo.db.documents.find_one({"user": session["user"]}, sort=[('created_at', -1)])
    if doc:
        session['active_doc_id'] = str(doc['_id'])
    return doc

@app.context_processor
def inject_docs():
    """Injects the user's document list into EVERY HTML template automatically."""
    if "user" in session and session.get("role") == "user":
        # Get all documents for the dropdown
        docs = list(mongo.db.documents.find(
            {"user": session["user"]}, 
            {"filename": 1} # Only fetch ID and filename to save memory
        ).sort("created_at", -1))
        
        # Convert ObjectIds to strings for HTML comparison
        for d in docs:
            d["_id"] = str(d["_id"])
            
        return dict(user_document_list=docs, active_doc_id=session.get("active_doc_id"))
    return dict()

# --- ADD THIS NEW ROUTE TO HANDLE SWITCHING ---
@app.route("/user/switch_doc/<doc_id>")
def switch_doc(doc_id):
    if "user" in session:
        session["active_doc_id"] = doc_id
    # Refresh the page the user is currently on
    return redirect(request.referrer or url_for('user_dashboard'))

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
        email = request.form["email"].strip()
        # Hash the password for security
        password = generate_password_hash(request.form["password"].strip())
        
        # ❌ REMOVED: role = request.form["role"] (This was causing the crash!)

        if mongo.db.users.find_one({"email": email}):
            flash("User already exists with that email.")
            return redirect(url_for("register"))

        # Force role to be 'user' for all new signups
        mongo.db.users.insert_one({
            "name": name,
            "email": email,
            "password": password,
            "role": "user",  # <--- HARDCODED SECURITY
            "created_at": datetime.now()
        })
        
        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        # Redirect based on role if already logged in
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        
        user = mongo.db.users.find_one({"email": email})
        
        if user:
            # 1. CHECK IF PASSWORD MATCHES (HASHED or PLAIN)
            # We try checking the hash first. If that errors (because it's plain text), we fallback to plain text.
            password_matches = False
            
            try:
                if check_password_hash(user["password"], password):
                    password_matches = True
            except:
                # If check_password_hash fails (e.g. user has plain text "123"), do direct comparison
                if user["password"] == password:
                    password_matches = True
            
            if password_matches:
                session["user"] = email
                session["role"] = user.get("role", "user")
                
                if session["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("user_dashboard"))
            else:
                flash("Invalid email or password")
        else:
            flash("Invalid email or password")
            
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
# ---------------- USER DASHBOARD ----------------
@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # 1. Fetch the ACTIVE document using our new helper function
    doc = get_active_document()

    # 2. Get Statistics for the "Stats Row"
    total_docs = mongo.db.documents.count_documents({"user": session["user"]})
    
    # Calculate Risk Score based on the ACTIVE document
    risk_score = 0
    if doc and "swot" in doc:
        threats = len(doc.get("swot", {}).get("threats", []))
        risk_score = min(threats * 10, 100) # 10% risk per threat

    # 3. Get Recent Activity (Last 3 docs) for the side panel
    recent_docs = list(mongo.db.documents.find(
        {"user": session["user"]},
        {"filename": 1, "created_at": 1, "sentiment": 1}
    ).sort("created_at", -1).limit(3))

    return render_template(
        "user/dashboard.html", 
        doc=doc,  # Changed from latest_doc to doc!
        stats={
            "total": total_docs,
            "risk": risk_score,
            "last_active": doc['created_at'].strftime('%b %d') if doc and 'created_at' in doc else "N/A"
        },
        recent=recent_docs
    )

@app.route("/user/documents", methods=["GET", "POST"])
def user_documents():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "document" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["document"]
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # 1. Extract Text
            raw_text = extract_text(filepath)
            
            # 2. Run Industry-Grade NLP Analysis (Sentiment, Entities, Smart Summary)
            analysis = nlp.analyze_document_text(raw_text)

            # 3. Run AI Strategic Analysis using Gemini
            #from ai_engine.strategy_generator import generate_full_strategy_profile
            
            # Get everything from Gemini in one call
            llm_analysis = generate_full_strategy_profile(raw_text)
            
            # Map the results to your existing variables with safe fallbacks
            intents = llm_analysis.get("intents", ["general_strategy"])
            swot = llm_analysis.get("swot", {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []})
            pestle = llm_analysis.get("pestle", {})
            porters = llm_analysis.get("porters", {})

            # 4. Run Derived Strategic Analysis (Your existing Logic)
            strategies = generate_initial_strategy(intents, swot)
            kpis = generate_kpis(intents)
            action_plan = generate_action_plan(strategies)
            prioritized = prioritize_strategies(strategies, swot)

            # 5. Save Everything to Database
            inserted_doc = mongo.db.documents.insert_one({
                "user": session["user"],
                "filename": filename,
                "raw_text": raw_text,       # Critical for Chat
                "cleaned_text": raw_text,   # (Simplified for now)
                
                # --- INTELLIGENCE DATA ---
                "summary": analysis.get("summary"),       # Uses the new smart summarizer
                "sentiment": analysis.get("sentiment", "Neutral"),
                "entities": analysis.get("entities", {}), # Orgs, Money, Locations
                "keywords": analysis.get("keywords", []),
                "word_count": analysis.get("word_count", 0),

                # --- STRATEGIC DATA ---
                "intents": intents,
                "swot": swot,
                "pestle": pestle,
                "porters": porters,
                "strategies": strategies,
                "kpis": kpis,
                "action_plan": action_plan,
                "prioritized_strategies": prioritized,
                
                "created_at": datetime.now()
            })
            # SET THE NEWLY UPLOADED DOC AS ACTIVE
            session["active_doc_id"] = str(inserted_doc.inserted_id)

            # 6. Audit Log
            mongo.db.logs.insert_one({
                "user": session["user"],
                "action": "Uploaded & Analyzed Document with AI",
                "meta": filename,
                "timestamp": datetime.now()
            })

            flash("Document uploaded and successfully analyzed by Gemini AI!")
            return redirect(url_for("user_documents"))

    # GET Request: Show list
    documents = list(mongo.db.documents.find({"user": session["user"]}).sort("created_at", -1))
    return render_template("user/documents.html", documents=documents)

@app.route("/user/delete_document/<doc_id>", methods=["POST"])
def delete_document(doc_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # 1. Find the document first to ensure it belongs to the logged-in user
    doc = mongo.db.documents.find_one({
        "_id": ObjectId(doc_id), 
        "user": session["user"]
    })

    if doc:
        # 2. Delete from Database
        mongo.db.documents.delete_one({"_id": ObjectId(doc_id)})
        
        # 3. (Optional) Delete the actual file from the uploads folder to save space
        try:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], doc["filename"])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

        # 4. Log the action
        mongo.db.logs.insert_one({
            "user": session["user"],
            "action": "Deleted document",
            "meta": doc["filename"]
        })

    return redirect(url_for("user_documents"))

# ---------------- USER OVERVIEW ----------------
@app.route("/user/overview")
def user_overview():
    if "user" not in session:
        return redirect(url_for("login"))

    # Fetch the ACTIVE document
    doc = get_active_document()

    if not doc:
        flash("Please upload a document to view the strategy overview.")
        return redirect(url_for("user_documents"))

    # Calculate scores on the fly for the active document
    from ai_engine.strategy_generator import calculate_strategic_scores
    scores = calculate_strategic_scores(doc.get("swot", {}), doc.get("intents", []))

    return render_template("user/overview.html", doc=doc, scores=scores)

# ---------------- USER INSIGHTS ----------------
@app.route("/user/insights")
def user_insights():
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Fetch the ACTIVE document
    doc = get_active_document()

    if not doc:
        return render_template("user/insights.html", error="No documents found.")

    return render_template("user/insights.html", doc=doc)

@app.route("/user/performance")
def user_performance():
    if "user" not in session:
        return redirect(url_for("login"))

    doc = get_active_document()

    if not doc or "raw_text" not in doc:
        flash("Please upload a document to view performance metrics.")
        return redirect(url_for("user_documents"))
    
    if "performance_metrics" in doc:
        metrics = doc["performance_metrics"]
    else:
        # Generate them and save them to the DB so we never ask the AI again for this doc
        from ai_engine.strategy_generator import generate_performance_metrics
        metrics = generate_performance_metrics(doc["raw_text"])
        
        # Save to MongoDB
        mongo.db.documents.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"performance_metrics": metrics}}
        )

    # REAL-TIME AI GENERATION
    from ai_engine.strategy_generator import generate_performance_metrics
    metrics = generate_performance_metrics(doc["raw_text"])

    trend_labels = ["Q1", "Q2", "Q3", "Q4"]

    return render_template(
        "user/performance.html",
        scores=metrics["scores"],
        kpi_labels=metrics["kpi_labels"],
        kpi_values=metrics["kpi_values"],
        trend_labels=trend_labels,
        growth_trend=metrics["growth_trend"],
        risk_trend=metrics["risk_trend"]
    )

# ---------------- USER CHAT ----------------
@app.route("/user/chat", methods=["GET", "POST"])
def user_chat():
    if "user" not in session:
        return redirect(url_for("login"))

    # Fetch the ACTIVE document
    doc = get_active_document()

    # Handle the Question (AJAX POST)
    if request.method == "POST":
        data = request.json
        question = data.get("question")
        
        if not doc:
            return {"answer": "Please upload a document first."}
            
        # Get the text to analyze
        text_to_analyze = doc.get("raw_text") or doc.get("cleaned_text")
        if not text_to_analyze:
            return {"answer": "This document is missing text data. Please upload it again."}

        # Run the AI Search using our new Gemini integration
        from ai_engine.chat_processor import get_document_answer
        answer = get_document_answer(question, text_to_analyze)                             
        
        return {"answer": answer}

    return render_template("user/chat.html", doc=doc)

@app.route("/user/scenarios")
def user_scenarios():
    if "user" not in session:
        return redirect(url_for("login"))

    doc = get_active_document()

    if not doc or "raw_text" not in doc:
        return redirect(url_for("user_documents"))

    scenario_type = request.args.get("scenario", "growth")
    # Create a unique database key for this specific scenario (e.g., "scenario_growth")
    scenario_key = f"scenario_{scenario_type}"

    if scenario_key in doc:
        result = doc[scenario_key]
    else:
        from ai_engine.strategy_generator import simulate_scenario_llm
        result = simulate_scenario_llm(doc["raw_text"], scenario_type)
        
        # Save to MongoDB
        mongo.db.documents.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {scenario_key: result}}
        )

    # REAL-TIME AI SIMULATION
    from ai_engine.strategy_generator import simulate_scenario_llm
    result = simulate_scenario_llm(doc["raw_text"], scenario_type)

    mongo.db.logs.insert_one({
        "user": session["user"],
        "action": f"Simulated {scenario_type} scenario via LLM",
        "meta": doc['filename']
    })

    return render_template(
        "user/scenarios.html",
        scenario=scenario_type,
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

        # 1. Calculate Standardized Scores for both
        stats1 = calculate_strategic_scores(doc1.get("swot", {}), doc1.get("intents", []))
        stats2 = calculate_strategic_scores(doc2.get("swot", {}), doc2.get("intents", []))

        # 2. Determine the "Winner" based on a weighted formula
        # Formula: Readiness (60%) - Risk (40%)
        score1 = (stats1["readiness"] * 0.6) - (stats1["risk"] * 0.4)
        score2 = (stats2["readiness"] * 0.6) - (stats2["risk"] * 0.4)

        winner_name = doc1["filename"] if score1 > score2 else doc2["filename"]
        
        # 3. Generate a dynamic explanation
        if score1 > score2:
            reason = f"{doc1['filename']} has a stronger strategic position due to higher readiness ({stats1['readiness']}%) and lower risk exposure."
        else:
            reason = f"{doc2['filename']} offers a more balanced approach, effectively mitigating risks ({stats2['risk_label']}) while maintaining operational stability."

        comparison = {
            "doc1": {
                "name": doc1["filename"],
                "focus": stats1["focus"],
                "readiness": stats1["readiness"],
                "risk": stats1["risk"],
                "risk_label": stats1["risk_label"]
            },
            "doc2": {
                "name": doc2["filename"],
                "focus": stats2["focus"],
                "readiness": stats2["readiness"],
                "risk": stats2["risk"],
                "risk_label": stats2["risk_label"]
            },
            "winner": winner_name,
            "explanation": reason
        }

        # Log the action
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

# ---------------- USER ACTION ROADMAP ----------------
@app.route("/user/roadmap")
def user_roadmap():
    if "user" not in session:
        return redirect(url_for("login"))

    doc = get_active_document()

    if not doc or "raw_text" not in doc:
        flash("Please upload a document to view the execution roadmap.")
        return redirect(url_for("user_documents"))

    # 🚀 CACHING LOGIC
    if "execution_roadmap" in doc:
        roadmap = doc["execution_roadmap"]
    else:
        # Generate the roadmap using AI
        from ai_engine.strategy_generator import generate_execution_roadmap
        roadmap = generate_execution_roadmap(doc["raw_text"])
        
        # Save to MongoDB
        mongo.db.documents.update_one(
            {"_id": doc["_id"]}, 
            {"$set": {"execution_roadmap": roadmap}}
        )
        
        # Audit Log
        mongo.db.logs.insert_one({
            "user": session["user"],
            "action": "Generated Step-by-Step AI Roadmap",
            "meta": doc['filename']
        })

    return render_template("user/roadmap.html", roadmap=roadmap, doc=doc)


# ---------------- PROFILE SETTINGS ----------------
@app.route("/user/profile")  
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/profile.html")


# ---------------- ADMIN ROUTES ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    # Security: Kick out non-admins
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    # 1. Calculate Real Stats
    total_users = mongo.db.users.count_documents({})
    total_docs = mongo.db.documents.count_documents({})
    total_logs = mongo.db.logs.count_documents({})
    
    # 2. Calculate Risk Score (Avoid division by zero)
    docs_with_risk = list(mongo.db.documents.find({}, {"swot": 1}))
    total_risk_points = 0
    risk_count = 0
    
    for d in docs_with_risk:
        if "swot" in d and "threats" in d["swot"]:
            total_risk_points += len(d["swot"]["threats"]) * 10
            risk_count += 1
            
    avg_risk = round(total_risk_points / risk_count) if risk_count > 0 else 0

    # 3. Create the stats dictionary
    stats_data = {
        "total_users": total_users,
        "total_docs": total_docs,
        "avg_risk": min(avg_risk, 100),
        "total_logs": total_logs
    }

    # 4. Pass 'stats' to the template
    return render_template("admin/dashboard.html", stats=stats_data)

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
