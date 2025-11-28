from app import create_app, db

app = create_app()

# Force table creation on startup (fix for Render)
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
