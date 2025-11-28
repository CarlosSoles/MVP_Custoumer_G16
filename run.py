from app import create_app, db

app = create_app()

from sqlalchemy import text

# Force table creation on startup (fix for Render)
with app.app_context():
    db.create_all()
    try:
        # Fix for password hash length in existing table
        db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(256)'))
        db.session.commit()
        print("Schema updated: password_hash size increased.")
    except Exception as e:
        print(f"Schema update ignored (probably already done): {e}")


if __name__ == '__main__':
    app.run(debug=True)
