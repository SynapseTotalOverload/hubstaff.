import os

DB_NAME = "db.sqlite3"

# Hubstaff Configuration
HUBSTAFF_CLIENT_ID = os.getenv("HUBSTAFF_CLIENT_ID", "your_hubstaff_client_id")
HUBSTAFF_CLIENT_SECRET = os.getenv("HUBSTAFF_CLIENT_SECRET", "your_hubstaff_client_secret")
HUBSTAFF_REDIRECT_URI = os.getenv("HUBSTAFF_REDIRECT_URI", "http://localhost:8000/callback")
HUBSTAFF_AUTH_URL = os.getenv("HUBSTAFF_AUTH_URL", "https://app.hubstaff.com/oauth/authorize")

# Admin Configuration
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
