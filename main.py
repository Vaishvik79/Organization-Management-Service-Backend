from app import create_app

app = create_app()

if __name__ == "__main__":
    # For local development
    app.run(port=5000, debug=True)
