import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# make sure these are downloaded once:
# nltk.download('punkt')
# nltk.download('stopwords')

stop_words = set(stopwords.words("english"))


def clean_text(text):
    """
    Lowercase, remove symbols, stopwords
    """
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)

    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]

    return " ".join(tokens)


def extract_keywords(text, top_n=10):
    """
    Extract keywords using TF-IDF
    """
    if not text.strip():
        return []

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([text])

    scores = zip(
        vectorizer.get_feature_names_out(),
        tfidf.toarray()[0]
    )

    sorted_words = sorted(scores, key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def generate_summary(text, max_sentences=3):
    """
    Simple extractive summary
    """
    sentences = nltk.sent_tokenize(text)
    return " ".join(sentences[:max_sentences])


def detect_business_intent(text):
    """
    Rule-based intent detection
    """
    intents = {
        "growth": ["growth", "expand", "increase", "scale"],
        "cost_reduction": ["cost", "reduce", "optimize", "efficiency"],
        "market_expansion": ["market", "region", "global", "international"],
        "digital_transformation": ["digital", "automation", "ai", "technology"],
        "risk_management": ["risk", "compliance", "regulation", "uncertainty"]
    }

    detected = []

    text = text.lower()
    for intent, keywords in intents.items():
        if any(k in text for k in keywords):
            detected.append(intent)

    return detected
