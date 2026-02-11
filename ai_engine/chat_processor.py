import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def simple_sentence_splitter(text):
    """
    Fallback sentence splitter using Regex (No NLTK required).
    Splits on '.', '?', or '!' followed by a space.
    """
    # Regex lookbehind to split by sentence endings
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def get_document_answer(question, raw_text):
    """
    Find the most relevant sentence in the document.
    """
    if not raw_text or len(raw_text) < 10:
        return "The document appears to be empty or too short to analyze."

    # 1. Split text into sentences (Try NLTK, fallback to Regex)
    try:
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
            sentences = nltk.sent_tokenize(raw_text)
        except LookupError:
            sentences = simple_sentence_splitter(raw_text)
    except ImportError:
        sentences = simple_sentence_splitter(raw_text)

    # 2. Add User Question to the list
    # We clean the question to ensure it has valid words
    clean_question = re.sub(r'[^\w\s]', '', question)
    if not clean_question.strip():
        return "Please ask a question containing words, not just symbols."
        
    sentences.append(question)
    
    # 3. Vectorize (Convert text to math)
    # Using 'english' stop words removes noise like "the", "and"
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
    except ValueError:
        # Happens if doc only contains stop words
        return "I couldn't analyze the text structure. It might be too short or generic."

    # 4. Calculate Similarity
    question_vector = tfidf_matrix[-1] # Last item is the question
    
    # Compare question against all document sentences (exclude the question itself)
    similarities = cosine_similarity(question_vector, tfidf_matrix[:-1])
    
    # 5. Get Best Match
    if similarities.size == 0:
        return "No relevant content found."

    best_idx = np.argmax(similarities)
    best_score = similarities[0][best_idx]
    
    print(f"DEBUG: Question='{question}' | Score={best_score}")

    # 6. Return Answer or Fallback
    if best_score > 0.1: # Threshold (0.1 is lenient)
        return sentences[best_idx]
    else:
        return "I couldn't find a direct answer in the document. Try asking with different keywords found in the file."