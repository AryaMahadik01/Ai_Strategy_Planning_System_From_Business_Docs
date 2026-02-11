import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter
import heapq
import random

# --- 1. AUTO-SETUP NLTK ---
def setup_nltk():
    resources = [
        "punkt", "punkt_tab", 
        "stopwords", "vader_lexicon", 
        "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng",
        "maxent_ne_chunker", "maxent_ne_chunker_tab",
        "words"
    ]
    for r in resources:
        try:
            nltk.data.find(f"tokenizers/{r}")
        except LookupError:
            try:
                nltk.data.find(f"taggers/{r}")
            except LookupError:
                try:
                    nltk.data.find(f"chunkers/{r}")
                except LookupError:
                    try:
                        nltk.data.find(f"corpora/{r}")
                    except LookupError:
                        pass # We assume setup_ai.py handled it

# --- 2. CLEANING & PREPROCESSING ---
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\$\%]', '', text)
    return text.strip()

# --- 3. INTELLIGENT SUMMARIZATION ---
def generate_summary(text, num_sentences=4):
    clean_txt = clean_text(text)
    sentences = sent_tokenize(clean_txt)
    if len(sentences) <= num_sentences: return " ".join(sentences)

    stop_words = set(stopwords.words('english'))
    word_frequencies = {}
    for word in word_tokenize(clean_txt.lower()):
        if word not in stop_words and word.isalnum():
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    if not word_frequencies: return text[:500] + "..."
    max_freq = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] = (word_frequencies[word] / max_freq)

    sentence_scores = {}
    for sent in sentences:
        for word in word_tokenize(sent.lower()):
            if word in word_frequencies:
                if len(sent.split(' ')) < 30:
                    sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]

    summary_sentences = heapq.nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    return " ".join(summary_sentences)

# --- 4. SENTIMENT & ENTITIES ---
def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    score = sia.polarity_scores(text)
    if score['compound'] >= 0.05: return "Optimistic / Growth-Focused"
    elif score['compound'] <= -0.05: return "Cautious / Risk-Aware"
    else: return "Neutral / Informational"

def extract_entities(text):
    words = word_tokenize(text)
    tags = nltk.pos_tag(words)
    chunks = nltk.ne_chunk(tags)
    entities = {"organizations": [], "locations": [], "money": []}
    
    entities["money"] = re.findall(r'\$\d+(?:,\d+)*(?:\.\d+)?(?:[BMk])?', text)
    
    for chunk in chunks:
        if hasattr(chunk, 'label'):
            name = " ".join(c[0] for c in chunk)
            if chunk.label() == "ORGANIZATION": entities["organizations"].append(name)
            elif chunk.label() == "GPE": entities["locations"].append(name)
            
    return {k: list(set(v)) for k, v in entities.items()}

# --- 5. KEYWORD EXTRACTION (renamed/aliased) ---
def extract_key_phrases(text, top_n=8):
    stop_words = set(stopwords.words('english'))
    words = [w.lower() for w in word_tokenize(text) if w.isalnum() and w.lower() not in stop_words]
    counter = Counter(words)
    bigrams = nltk.bigrams(words)
    bigram_counter = Counter(bigrams)
    
    most_common = [w[0] for w in counter.most_common(top_n // 2)]
    most_common_bigrams = [" ".join(bg[0]) for bg in bigram_counter.most_common(top_n // 2)]
    return most_common + most_common_bigrams

# ALIAS FOR BACKWARD COMPATIBILITY
extract_keywords = extract_key_phrases

# =========================================================
# 6. STRATEGY GENERATORS (RESTORED & UPGRADED)
# =========================================================

def detect_business_intent(text):
    """Detects if the doc is about Growth, Efficiency, or Risk."""
    text = text.lower()
    scores = {
        "market_expansion": len(re.findall(r'(growth|expand|market share|scale|opportunity)', text)),
        "cost_reduction": len(re.findall(r'(cost|saving|efficiency|budget|cut|reduce)', text)),
        "risk_compliance": len(re.findall(r'(risk|compliance|regulation|legal|audit|threat)', text)),
        "digital_transformation": len(re.findall(r'(digital|ai|tech|cloud|automation|data)', text))
    }
    # Return top 2 intents
    sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [k for k, v in sorted_intents[:2]]

def generate_swot(text):
    """Generates SWOT items based on keyword clusters."""
    text = text.lower()
    swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
    
    # Simple keyword heuristics for demo (In prod, use LLM)
    if "brand" in text or "leader" in text: swot["strengths"].append("Strong market brand presence")
    if "cash" in text or "profit" in text: swot["strengths"].append("Solid financial footing")
    if "technology" in text: swot["strengths"].append("Advanced technology stack")
    
    if "debt" in text or "cost" in text: swot["weaknesses"].append("High operational costs")
    if "gap" in text or "slow" in text: swot["weaknesses"].append("Slow time-to-market")
    
    if "emerging" in text or "global" in text: swot["opportunities"].append("Expansion into emerging markets")
    if "acquisition" in text or "partner" in text: swot["opportunities"].append("Strategic partnerships")
    
    if "competitor" in text or "rival" in text: swot["threats"].append("Intense competitive pressure")
    if "regulation" in text or "law" in text: swot["threats"].append("Regulatory compliance risks")
    
    # Fallbacks if empty
    if not swot["strengths"]: swot["strengths"] = ["Operational Resilience", "Experienced Leadership"]
    if not swot["weaknesses"]: swot["weaknesses"] = ["Resource Constraints", "Legacy Systems"]
    if not swot["opportunities"]: swot["opportunities"] = ["Digital Transformation", "New Product Lines"]
    if not swot["threats"]: swot["threats"] = ["Market Volatility", "Cybersecurity Threats"]
    
    return swot

def generate_pestle(text):
    return {
        "Political": "Regulatory changes in target markets.",
        "Economic": "Inflationary pressures affecting supply chain costs.",
        "Social": "Shifting consumer preferences towards sustainability.",
        "Technological": "Rapid advancement in AI and automation.",
        "Legal": "Data privacy and protection laws (GDPR/CCPA).",
        "Environmental": "Carbon footprint reduction mandates."
    }

def generate_porters(text):
    return {
        "Supplier Power": "Moderate - Alternative suppliers available.",
        "Buyer Power": "High - Customers have many choices.",
        "Competitive Rivalry": "High - Market is saturated.",
        "Threat of Substitution": "Low - Specialized service offering.",
        "Threat of New Entry": "Moderate - High capital barrier."
    }

def generate_initial_strategy(intents, swot):
    strategies = []
    if "market_expansion" in intents:
        strategies.append("Launch aggressive marketing campaign in Tier 2 cities.")
        strategies.append("Explore strategic acquisition of smaller competitors.")
    if "cost_reduction" in intents:
        strategies.append("Implement automated workflow to reduce manual overhead.")
        strategies.append("Renegotiate vendor contracts for better rates.")
    if "digital_transformation" in intents:
        strategies.append("Migrate legacy infrastructure to Cloud.")
        strategies.append("Deploy AI-driven customer support.")
    
    # Default
    if not strategies:
        strategies.append("Focus on core product stability and customer retention.")
        strategies.append("Optimize cash flow management.")
    
    return strategies

def generate_kpis(intents):
    kpis = {}
    if "market_expansion" in intents:
        kpis = {"Revenue Growth": "15%", "Market Share": "+5%", "CAC": "-10%"}
    elif "cost_reduction" in intents:
        kpis = {"OpEx Savings": "20%", "Margin": "+8%", "Efficiency": "High"}
    else:
        kpis = {"NPS Score": "75", "Retention": "90%", "Uptime": "99.9%"}
    return kpis

def generate_action_plan(strategies):
    plans = []
    timelines = ["Immediate (0-3 Months)", "Short Term (3-6 Months)", "Long Term (6-12 Months)"]
    for i, strat in enumerate(strategies):
        plans.append({
            "strategy": strat,
            "action": f"Initiate project team and allocate budget for {strat.split()[0].lower()} phase.",
            "timeline": timelines[i % 3]
        })
    return plans

def prioritize_strategies(strategies, swot):
    prioritized = []
    for strat in strategies:
        prioritized.append({
            "strategy": strat,
            "priority": "High" if "Launch" in strat or "Optimize" in strat else "Medium"
        })
    return prioritized

# --- MAIN WRAPPER FOR NEW APP.PY ---
def analyze_document_text(raw_text):
    """
    Main function called by app.py. Runs all analysis.
    """
    if not raw_text: return {}
    
    return {
        "summary": generate_summary(raw_text),
        "sentiment": analyze_sentiment(raw_text),
        "entities": extract_entities(raw_text),
        "keywords": extract_key_phrases(raw_text),
        "word_count": len(raw_text.split())
    }