from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connect to your MongoDB (Make sure this matches your config.py!)
client = MongoClient("mongodb://localhost:27017/")
db = client["strategix"] # Replace 'strategix' if your DB name is different

admin_email = "admin@strategix.com"
admin_password = "admin123" # Change this to whatever you want!

# Check if admin already exists
if db.users.find_one({"email": admin_email}):
    print(f"Admin {admin_email} already exists! Try logging in.")
else:
    # Insert Admin
    db.users.insert_one({
        "name": "System Admin",
        "email": admin_email,
        "password": generate_password_hash(admin_password), # Securely hashed
        "role": "admin",
        "created_at": datetime.now()
    })
    print(f"✅ Admin created successfully!")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")