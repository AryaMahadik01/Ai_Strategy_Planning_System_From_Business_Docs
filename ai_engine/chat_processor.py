from google import genai
from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)

def get_document_answer(question, raw_text):
    """
    Uses Gemini to answer user questions based strictly on the provided document.
    """
    if not raw_text or len(raw_text) < 10:
        return "The document appears to be empty or too short to analyze."

    prompt = f"""
    You are an AI Strategy Assistant for the StrategixAI platform.
    Answer the user's question based ONLY on the context of the business document provided below. 
    If the answer is not in the document, politely say that you cannot find the information in the current text. Do not make up facts.
    Keep the answer concise, professional, and directly address the prompt.

    User Question: {question}

    Document Context:
    {raw_text[:30000]} 
    """

    try:
        # New API call syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return "⚠️ Whoa there! We're hitting the AI speed limit (max 15 requests per minute). Please wait about 10 seconds and ask your question again."
        
        print(f"Chat API Error: {e}")
        return "I'm sorry, I encountered an error while processing the document. Please check the terminal logs."