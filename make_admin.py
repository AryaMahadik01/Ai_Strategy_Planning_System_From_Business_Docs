from flask import Flask
from flask_pymongo import PyMongo
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)

def promote_to_admin(email):
    with app.app_context():
        user = mongo.db.users.find_one({"email": email})
        if user:
            mongo.db.users.update_one(
                {"email": email},
                {"$set": {"role": "admin"}}
            )
            print(f"Success! {email} is now an Admin.")
        else:
            print(f"Error: User {email} not found.")

if __name__ == "__main__":
    # REPLACE THIS WITH YOUR EMAIL
    target_email = "arya01@gmail.com" 
    promote_to_admin(target_email)