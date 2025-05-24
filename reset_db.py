import os
from app import app, db
from seed_data import seed_all

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'atlas.sqlite')

def reset_database():
    # Ensure the instance directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if os.path.exists(DB_PATH):
        print("🧨 Deleting existing database...", flush=True)
        os.remove(DB_PATH)
    else:
        print("✅ No existing database found.", flush=True)

    print("🔧 Creating fresh database...", flush=True)
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tables created.", flush=True)

            seed_all()
            print("🌱 Seed data loaded.", flush=True)
        except Exception as e:
            print("⚠️ Error during reset:", str(e), flush=True)

if __name__ == '__main__':
    reset_database()
