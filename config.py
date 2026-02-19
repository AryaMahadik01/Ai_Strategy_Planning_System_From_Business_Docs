import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/strategix")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    REPORT_FOLDER = os.path.join(os.getcwd(), 'reports')

    # Add the Gemini API Key here
    GEMINI_API_KEY = os.environ.get("AIzaSyC_U9O1-ZkN7mZEvGyO8apwEW4b7ZVkuxk")