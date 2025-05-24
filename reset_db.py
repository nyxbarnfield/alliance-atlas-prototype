import os
from app import app, db
from seed_data import seed_all

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'atlas.sqlite')

def reset_database():
    if os.path.exists(DB_PATH):
        print("🧨 Deleting existing database...")
        os.remove(DB_PATH)
    else:
        print("✅ No existing database found.")

    print("🔧 Creating fresh database...")
    with app.app_context():
        db.create_all()
        print("✅ Tables created.")

        try:
            seed_all()
            print("🌱 Seed data loaded.")
        except Exception as e:
            print("⚠️ Error seeding data:", e)

if __name__ == '__main__':
    reset_database()
