import os
from app import create_app, db
from app.models import User, Product, Trade, Notification, Message, TradeOffer
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    # Print masked URL for debugging
    print(f"DEBUG: Connecting to database: {db_url.split('@')[-1] if '@' in db_url else 'SQLite'}")
    
    print("DEBUG: Starting db.create_all()...")
    try:
        db.create_all()
        print("DEBUG: db.create_all() executed successfully.")
    except Exception as e:
        print(f"DEBUG: Error during db.create_all(): {e}")
        
    # Verify tables
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"DEBUG: Existing tables in DB: {tables}")
        
        if 'product' in tables:
            print("DEBUG: Table 'product' VERIFIED.")
        else:
            print("DEBUG: Table 'product' MISSING after creation attempt!")
    except Exception as e:
        print(f"DEBUG: Error inspecting tables: {e}")

