from app import app
from db.database import db

with app.app_context():
    db.create_all()
    print("✅ Tables created.")
