import os
from app.database import engine, Base, DB_ENABLED
from app.models.chess_models import AiChess

def create_tables():
    if DB_ENABLED:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    else:
        print("Database is not enabled. Skipping table creation.")

if __name__ == "__main__":
    create_tables() 